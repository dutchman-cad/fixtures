#!/usr/bin/env python3
"""Check one public (CC0) fixture pair with the same steps as the portal's pair checker.

Mirrors the portal's `fixture-check` (src/bin/fixture-check.rs): `analyze` per file
(cadmpeg check --json, cadmpeg convert --allow-errors, solidcraft-cli eval), `verdict`,
`pair_report`, `mesh_only_step`, the preview, and the `Report` shape. Standard library only.

Usage: pair_check.py WORK_DIR OUT_DIR
  WORK_DIR holds native.<ext> and, if there is one, reference.step (inputs, never uploaded).
  OUT_DIR receives result.json, logs/*, and preview.png (what the workflow uploads).
Environment: CADMPEG, SOLIDCRAFT_CLI (absolute paths), PAIR_ID, NATIVE_EXT, HAS_STEP ("1" or "0"),
TIMEOUT_SECS, and optionally MEMORY_BYTES, plus run details copied into result.json.
"""
import hashlib
import json
import os
import re
import resource
import signal
import subprocess
import sys
import time

OUTPUT_CAP = 4 * 1024 * 1024  # fixture-check.rs OUTPUT_CAP
PNG_CAP = 2 * 1024 * 1024
LOG_CAP, LOG_HEAD = 20_000, 8_000  # check.rs shorten_log
TESSELLATED = "tessellated STEP: no exact geometry to compare"
NOT_CHECKABLE = "not checkable yet: no geometry reader for this format"
NO_CHECK = "no automatic check for this format yet"
TOO_LARGE = "too large to check here"
# formats.rs `readers`, lower case. Anything else known is kept but not checked automatically.
READERS = {"f3d", "f3z", "ipt", "iam", "sldprt", "fcstd", "prt", "catpart", "3dm", "sat", "sab",
           "smt", "smb", "step", "stp", "igs", "iges", "pvz"}
KNOWN_NO_READER = {"sldasm", "asm", "catproduct", "par", "psm", "ad_prt", "ad_smp", "ad_asm",
                   "gltf", "glb", "stl", "3mf", "obj"}
ALLOC_TEXT = ("memory allocation", "cannot allocate memory", "out of memory", "bad_alloc",
              "allocation failed", "failed to allocate")
# Killed by these (fixture-check.rs child): SIGKILL, SIGXCPU, SIGABRT, SIGSEGV.
RESOURCE_SIGNALS = {signal.SIGKILL, signal.SIGXCPU, signal.SIGABRT, signal.SIGSEGV}


class FileErr(Exception):
    """Error::File(reason): a result about the file."""

    def __init__(self, reason, outcome="tool_error"):
        super().__init__(reason)
        self.reason, self.outcome = reason, outcome


class RetryErr(Exception):
    """Error::Retry(class): the tool did not finish (timeout) or the host failed."""

    def __init__(self, cls, outcome="tool_error"):
        super().__init__(cls)
        self.cls, self.outcome = cls, outcome


def shorten_log(text):
    total = len(text.encode())
    if len(text) <= LOG_CAP:
        return text
    return f"{text[:LOG_HEAD]}\n... (log shortened: {total} bytes total)\n{text[-(LOG_CAP - LOG_HEAD):]}"


class Runner:
    def __init__(self, work, out):
        self.work, self.out = work, out
        self.cadmpeg = os.environ["CADMPEG"]
        self.renderer = os.environ["SOLIDCRAFT_CLI"]
        self.timeout = int(os.environ["TIMEOUT_SECS"])
        self.memory = int(os.environ.get("MEMORY_BYTES", 16 * 1024**3))
        self.steps = []
        # The job is sized for three tools at the limit; later steps get what is left of that.
        self.deadline = time.monotonic() + 3 * self.timeout
        os.makedirs(os.path.join(out, "logs"), exist_ok=True)

    def run(self, label, exe, args, memory, timeout, renderer=False, keep_logs=True):
        """Run one tool as fixture-check.rs `child` does: no stdin, cleared environment, cwd/HOME/TMPDIR
        in the work folder, nice 10, address-space limit, no core dumps, own process group, 4 MiB
        output caps. Returns (ok, stdout bytes). Raises RetryErr on timeout, FileErr on a memory stop."""
        env = {"PATH": "/usr/bin:/bin", "HOME": self.work, "TMPDIR": self.work}
        if renderer:
            env["SOLIDCRAFT_GPU"] = "cpu"
        out_path = os.path.join(self.work, ".stdout")
        err_path = os.path.join(self.work, ".stderr")

        def limits():
            os.setpgid(0, 0)
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
            os.setpriority(os.PRIO_PROCESS, 0, 10)

        start = time.monotonic()
        timed_out = False
        code = None
        started = True
        with open(out_path, "wb") as so, open(err_path, "wb") as se:
            try:
                proc = subprocess.Popen([exe, *args], cwd=self.work, env=env, stdin=subprocess.DEVNULL,
                                        stdout=so, stderr=se, preexec_fn=limits)
            except OSError:
                started = False
            if started:
                try:
                    code = proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                finally:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)  # also descendants
                    except OSError:
                        pass
                    code = proc.wait() if code is None else code
        seconds = time.monotonic() - start
        stdout = open(out_path, "rb").read(OUTPUT_CAP + 1)
        stderr = open(err_path, "rb").read(OUTPUT_CAP + 1)
        step = {"step": label, "seconds": round(seconds, 2), "exit": code if started else None}
        low = (stdout + stderr).decode("utf-8", "replace").lower()
        killed = code is not None and code < 0 and -code in {int(s) for s in RESOURCE_SIGNALS}
        if code is not None and code > 128 and (code - 128) in {int(s) for s in RESOURCE_SIGNALS}:
            killed = True
        if not started:
            step["status"] = "tool_error"
        elif timed_out:
            step["status"] = "time_limit"
        elif killed or (code != 0 and any(t in low for t in ALLOC_TEXT)):
            step["status"] = "memory_limit"
        elif code != 0:
            step["status"] = "tool_error"
        elif len(stdout) > OUTPUT_CAP or len(stderr) > OUTPUT_CAP:
            step["status"] = "tool_error"
            step["note"] = "output limit"
        else:
            step["status"] = "ok"
        self.steps.append(step)
        if keep_logs:
            base = os.path.join(self.out, "logs", label)
            with open(base + ".stdout", "wb") as f:
                f.write(stdout[:OUTPUT_CAP])
            text = stdout.decode("utf-8", "replace") + stderr.decode("utf-8", "replace")
            with open(base + ".log", "w") as f:
                f.write(shorten_log(text))
        if step["status"] == "time_limit":
            raise RetryErr("timeout", "time_limit")
        if step["status"] == "memory_limit":
            raise FileErr(TOO_LARGE, "memory_limit")
        if step.get("note") == "output limit":
            raise FileErr("output limit")
        if not started:
            raise RetryErr("spawn")
        return code == 0, stdout

    def limit(self):
        return max(1, min(self.timeout, int(self.deadline - time.monotonic())))

    def version(self, label, exe, renderer=False):
        try:
            ok, out = self.run(label, exe, ["--version"], 512 * 1024 * 1024, 10, renderer, keep_logs=False)
        except (FileErr, RetryErr):
            return None
        for line in out.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if line:
                return line if ok and version_line(line) else None
        return None


def version_line(s):
    return (1 <= len(s) <= 80 and s[0].isalpha() and all(c.isalnum() or c in " .+-_()" for c in s)
            and s.isascii())


def finite(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) != float("inf") and v == v else None


def get(v, *path):
    for p in path:
        try:
            v = v[p]
        except (KeyError, IndexError, TypeError):
            return None
    return v


def code_token(s):
    return bool(s) and len(s) <= 100 and re.fullmatch(r"[A-Za-z0-9._:\-]+", s) is not None


def losses(v, out):
    for path in (("decode_report", "losses"), ("check_report", "losses")):
        items = get(v, *path)
        if isinstance(items, list):
            for item in items:
                c = item.get("code") if isinstance(item, dict) else None
                if isinstance(c, str):
                    value = c
                elif isinstance(c, dict) and isinstance(c.get("namespace"), str) and isinstance(c.get("code"), str):
                    value = f"{c['namespace']}:{c['code']}"
                else:
                    value = c.get("kind", "") if isinstance(c, dict) and isinstance(c.get("kind"), str) else ""
                if code_token(value) and len(out) < 50:
                    out.add(value)


def refusal(v):
    r = v.get("refusal") if isinstance(v, dict) else None
    r = r if isinstance(r, dict) else {}
    if r.get("code") in ("resource_limit", "out_of_memory", "allocation_failed"):
        return FileErr(TOO_LARGE, "memory_limit")
    stage = r.get("stage") if r.get("stage") in ("detect", "check", "measure") else "decode"
    cls = r.get("code") if r.get("code") in ("unsupported_dialect", "empty_geometry", "decode_failed") else "refused"
    return FileErr(f"{stage} {cls}")


def eval_measure(ev):
    bad = FileErr("eval invalid_json")
    bodies = ev.get("bodies") if isinstance(ev, dict) else None
    if not isinstance(bodies, list):
        raise bad
    faces, volume = 0, 0.0
    lo_all, hi_all = [float("inf")] * 3, [float("-inf")] * 3
    for b in bodies:
        f = get(b, "faces")
        if not isinstance(f, int) or isinstance(f, bool) or f < 0:
            raise bad
        faces += f
        vol = finite(get(b, "volume_mm3"))
        volume = None if volume is None or vol is None else volume + vol
        for i in range(3):
            lo, hi = finite(get(b, "bbox", "min", i)), finite(get(b, "bbox", "max", i))
            if lo is None or hi is None or hi < lo:
                raise bad
            lo_all[i], hi_all[i] = min(lo_all[i], lo), max(hi_all[i], hi)
    return {"bodies": len(bodies), "faces": faces, "volume": volume,
            "bbox": None if not bodies else (lo_all, hi_all)}


def parse(check, ev):
    findings = get(check, "check_report", "findings")
    if not isinstance(findings, list):
        raise FileErr("check invalid_json")
    bbox = None
    if ev["bbox"] is not None:
        bbox = [ev["bbox"][1][i] - ev["bbox"][0][i] for i in range(3)]
        if any(e < 0 or e != e for e in bbox):
            bbox = None
    codes = set()
    losses(check, codes)
    gen = check.get("generator")
    rev = gen if isinstance(gen, str) and len(gen) <= 150 and re.fullmatch(r"[A-Za-z0-9 ._+\-]*", gen) else None
    sev = lambda s: float(sum(1 for f in findings if isinstance(f, dict) and f.get("severity") == s))
    return {"rev": rev, "bodies": float(ev["bodies"]), "faces": float(ev["faces"]), "volume": ev["volume"],
            "bbox": bbox, "errors": sev("error"), "warnings": sev("warning"), "seconds": 0.0, "losses": codes}


def load_json(data):
    try:
        return json.loads(data)
    except ValueError:
        raise FileErr("decode invalid_json")


def analyze(r, prefix, name):
    """fixture-check.rs `analyze`: check, convert, eval, parse. `prefix` labels the steps."""
    start = time.monotonic()
    ok, out = r.run(f"{prefix}.check", r.cadmpeg, ["check", "--json", name], r.memory, r.limit())
    check = load_json(out)
    if (not ok or get(check, "status") == "refused") and (
            get(check, "refusal", "code") != "check_failed" or get(check, "check_report", "findings") is None):
        raise refusal(check)
    for n in ("measure.step", "eval.json"):
        try:
            os.remove(os.path.join(r.work, n))
        except FileNotFoundError:
            pass
    ok, _ = r.run(f"{prefix}.convert", r.cadmpeg, ["convert", name, "-o", "measure.step", "--allow-errors"],
                  r.memory, r.limit())
    if not ok:
        raise FileErr("convert failed")
    ok, _ = r.run(f"{prefix}.eval", r.renderer, ["eval", "measure.step", "--json-out", "eval.json"],
                  max(r.memory, 2 * 1024**3), r.limit(), renderer=True)
    if not ok:
        raise FileErr("eval failed")
    with open(os.path.join(r.work, "eval.json"), "rb") as f:
        data = f.read(OUTPUT_CAP + 1)
    if len(data) > OUTPUT_CAP:
        raise FileErr("output limit")
    a = parse(check, eval_measure(load_json(data)))
    a["seconds"] = time.monotonic() - start
    return a


def mesh_only_step(path):
    """fixture-check.rs `mesh_only_step`: only tessellated geometry in the DATA section."""
    with open(path, "rb") as f:
        data = f.read(OUTPUT_CAP + 1)
    if len(data) > OUTPUT_CAP:
        return False
    text = re.sub(r"'(?:''|[^'])*'|/\*.*?\*/", " ", data.decode("utf-8", "replace"), flags=re.S).upper()
    if not text.lstrip().startswith("ISO-10303-21;") or not text.rstrip().endswith("END-ISO-10303-21;"):
        return False
    exact_names = {"MANIFOLD_SOLID_BREP", "BREP_WITH_VOIDS", "ADVANCED_BREP_SHAPE_REPRESENTATION", "ADVANCED_FACE",
                   "SHELL_BASED_SURFACE_MODEL", "FACE_BASED_SURFACE_MODEL", "MANIFOLD_SURFACE_SHAPE_REPRESENTATION",
                   "GEOMETRIC_CURVE_SET", "EDGE_BASED_WIREFRAME_MODEL"}
    mesh = exact = False
    for section in re.finditer(r"\bDATA\s*(?:\([^;]*\))?\s*;(.*?)\bENDSEC\s*;", text, flags=re.S):
        for rec in re.finditer(r"#\s*[0-9]+\s*=([^;]*);", section.group(1), flags=re.S):
            ents = set(re.findall(r"\b([A-Z][A-Z0-9_]*)\s*\(", rec.group(1)))
            faceted = "FACETED_BREP" in ents
            mesh = mesh or faceted or any(
                n.startswith(("TESSELLATED_", "TRIANGULATED_")) or n in (
                    "COMPLEX_TRIANGULATED_FACE", "COMPLEX_TRIANGULATED_SURFACE_SET") for n in ents)
            exact = exact or (not faceted and bool(ents & exact_names))
    return mesh and not exact


def num(x):
    """Rust f64 Display for the reason strings: whole numbers print without a decimal point."""
    return str(int(x)) if x == int(x) else repr(x)


def verdict(nat, stp):
    if stp is not None and stp["bodies"] == 0:
        return "partial", TESSELLATED
    if nat["errors"] > 0:
        return "partial", f"check_errors: native {num(nat['errors'])} vs expected 0" + (
            "; no STEP reference" if stp is None else "")
    if stp is None:
        return "pass", "no STEP reference"
    if stp["errors"] > 0:
        return "partial", f"check_errors: STEP {num(stp['errors'])} vs expected 0"
    sv = stp["volume"]
    for key, a, b, tol in (("bodies", nat["bodies"], stp["bodies"], 0.0), ("faces", nat["faces"], stp["faces"], 0.0),
                           ("volume_mm3", nat["volume"], sv, abs(sv or 0.0) * 0.001)):
        if a is not None and b is not None and abs(a - b) <= tol:
            continue
        if a is not None and b is not None:
            return "partial", f"{key}: native {num(a)} vs STEP {num(b)}"
        return "partial", (f"{key}: native {'unavailable' if a is None else num(a)} "
                           f"vs STEP {'unavailable' if b is None else num(b)}")
    if nat["bbox"] is None or stp["bbox"] is None:
        return "partial", "bbox: native or STEP unavailable"
    tol = max(0.01, 1e-5 * sum(v * v for v in stp["bbox"]) ** 0.5)
    for i, k in enumerate(("dx", "dy", "dz")):
        if abs(nat["bbox"][i] - stp["bbox"][i]) > tol:
            return "partial", f"bbox_{k}: native {num(nat['bbox'][i])} vs STEP {num(stp['bbox'][i])}"
    return "pass", "matches STEP reference"


class Report:
    def __init__(self, status, reason, rev):
        self.status, self.reason, self.cadmpeg_rev = status, reason[:300], rev
        self.metrics, self.losses, self.reader, self.renderer = {}, set(), None, None

    def add(self, prefix, a):
        if prefix == "native" and a["rev"]:
            self.cadmpeg_rev = a["rev"]
        for k, v in (("bodies", a["bodies"]), ("faces", a["faces"]), ("volume_mm3", a["volume"]),
                     ("check_errors", a["errors"]), ("check_warnings", a["warnings"]), ("seconds", a["seconds"])):
            if v is not None:
                self.metrics[f"{prefix}_{k}"] = v
        if a["bbox"] is not None:
            for k, v in zip(("x_mm", "y_mm", "z_mm"), a["bbox"]):
                self.metrics[f"{prefix}_bbox_{k}"] = v
        self.losses = set(sorted(self.losses | a["losses"])[:50])

    def as_json(self):
        return {"status": self.status, "reason": self.reason, "cadmpeg_rev": self.cadmpeg_rev,
                "metrics": self.metrics, "losses": sorted(self.losses), "reader": self.reader,
                "renderer": self.renderer}


def try_analyze(r, prefix, name):
    try:
        return analyze(r, prefix, name), None
    except (FileErr, RetryErr) as e:
        return None, e


def resource_stop(e):
    return isinstance(e, FileErr) and e.reason in (TOO_LARGE, "output limit")


def pair_report(nat, step, step_path, rev):
    """step: None (no STEP), or (analysis, error). Raises the error for a resource stop."""
    stp = None
    if step is not None:
        a, err = step
        if err is not None:
            if isinstance(err, FileErr) and not resource_stop(err):
                rep = Report("partial", TESSELLATED if mesh_only_step(step_path) else "STEP unreadable", rev)
                rep.add("native", nat)
                return rep
            raise err
        stp = a
    if stp is not None and stp["bodies"] > 0 and mesh_only_step(step_path):
        status, reason = "partial", TESSELLATED
    else:
        status, reason = verdict(nat, stp)
    rep = Report(status, reason, rev)
    rep.add("native", nat)
    if stp is not None:
        rep.add("step", stp)
    return rep


def valid_png(b):
    return (33 <= len(b) <= PNG_CAP and b[:8] == b"\x89PNG\r\n\x1a\n" and b[8:12] == (13).to_bytes(4, "big")
            and b[12:16] == b"IHDR" and b[16:20] == (1200).to_bytes(4, "big") and b[20:24] == (800).to_bytes(4, "big"))


def snapshot(r, step_name):
    png = os.path.join(r.work, "preview.png")
    try:
        os.remove(png)
    except FileNotFoundError:
        pass
    ok, _ = r.run(f"preview.snapshot.{step_name.split('.')[0]}", r.renderer,
                  ["snapshot", step_name, "--out", "preview.png", "--width", "1200", "--height", "800",
                   "--view", "iso", "--no-grid"], r.memory, r.limit(), renderer=True)
    if not ok:
        raise RetryErr("render failed")
    with open(png, "rb") as f:
        data = f.read(PNG_CAP + 1)
    if not valid_png(data):
        raise RetryErr("invalid PNG")
    return data


def pair_preview(r, native, geometry, rep):
    """Native render when the verdict is pass or partial, else (or on failure) the STEP's."""
    err = RetryErr("verdict fail")
    if rep.status in ("pass", "partial"):
        try:
            if not geometry:
                raise RetryErr("empty geometry")
            ok, _ = r.run("preview.convert", r.cadmpeg, ["convert", native, "-o", "preview.step"], r.memory, r.limit())
            if not ok:
                raise RetryErr("conversion failed")
            return snapshot(r, "preview.step"), "native"
        except (FileErr, RetryErr) as e:
            err = e
    if rep.metrics.get("step_bodies", 0) > 0:
        return snapshot(r, "reference.step"), "step"
    raise err


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    work, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    r = Runner(work, out)
    ext = os.environ["NATIVE_EXT"]
    has_step = os.environ.get("HAS_STEP") == "1"
    native = f"native.{ext}"
    step_path = os.path.join(work, "reference.step")

    # fixture-check.rs run(): cadmpeg's whole --version output is the revision; it must be plain.
    try:
        ok, vout = r.run("version.cadmpeg", r.cadmpeg, ["--version"], r.memory, 60, keep_logs=False)
    except (FileErr, RetryErr):
        ok, vout = False, b""
    rev = vout.decode("utf-8", "replace").strip()
    if not ok or not rev or len(rev) > 150 or not re.fullmatch(r"[A-Za-z0-9 ._+\-]+", rev):
        # fixture-check.rs stops with Retry("version") and posts nothing; here the run says so instead.
        print("pair-check: cadmpeg did not report a plain version", file=sys.stderr)
        with open(os.path.join(out, "result.json"), "w") as f:
            json.dump({"schema": 1, "pair_id": int(os.environ["PAIR_ID"]), "outcome": "tool_error",
                       "stopped": "version", "steps": r.steps, "report": None, "preview": None}, f, indent=1)
        return 0
    renderer_version = r.version("version.solidcraft_cli", r.renderer, renderer=True)

    outcome, stopped = "ok", None
    rep, geometry = None, False
    try:
        if ext.lower() not in READERS:
            # row(): no reader for the CAD file; its STEP can still be measured and previewed.
            reason = NO_CHECK if ext.lower() in KNOWN_NO_READER else "unknown format"
            rep = Report("unknown", reason, rev)
            if has_step:
                a, _ = try_analyze(r, "step", "reference.step")
                if a:
                    rep.add("step", a)
        else:
            optional = ext.lower() == "prt"  # geometry_optional(): Creo and NX parts
            nat, err = try_analyze(r, "native", native)
            if err is None and nat["bodies"] == 0 and optional:
                rep = Report("partial", NOT_CHECKABLE, rev)
            elif err is not None and isinstance(err, FileErr) and optional and not resource_stop(err):
                rep = Report("partial", NOT_CHECKABLE, rev)
            elif err is not None and isinstance(err, FileErr) and has_step and not resource_stop(err):
                rep = Report("fail", err.reason, rev)
                a, _ = try_analyze(r, "step", "reference.step")
                if a:
                    rep.add("step", a)
                outcome, stopped = err.outcome, err.reason
            elif err is not None:
                raise err
            else:
                step = try_analyze(r, "step", "reference.step") if has_step else None
                rep = pair_report(nat, step, step_path, rev)
                geometry = nat["bodies"] > 0
    except FileErr as e:
        rep = Report("fail", "resource limit exceeded on the public runner" if e.reason == TOO_LARGE else e.reason, rev)
        outcome, stopped = e.outcome, e.reason
    except RetryErr as e:
        rep = Report("fail", "timed out on the public runner" if e.cls == "timeout" else f"tool failed: {e.cls}", rev)
        outcome, stopped = e.outcome, e.cls
    rep.reader = rev
    rep.renderer = renderer_version

    preview = None
    if rep.status != "unknown" or rep.metrics.get("step_bodies", 0) > 0:
        try:
            png, source = pair_preview(r, native, geometry, rep)
            with open(os.path.join(out, "preview.png"), "wb") as f:
                f.write(png)
            preview = {"file": "preview.png", "source": source}
        except (FileErr, RetryErr) as e:
            print(f"pair-check: preview skipped: {getattr(e, 'cls', None) or getattr(e, 'reason', '')}")

    result = {
        "schema": 1,
        "pair_id": int(os.environ["PAIR_ID"]),
        "native_ext": ext,
        "native_sha256": sha256(os.path.join(work, native)),
        "step_sha256": sha256(step_path) if has_step else None,
        "tools": {"cadmpeg": rev, "solidcraft_cli": renderer_version,
                  "cadmpeg_rev_requested": os.environ.get("CADMPEG_REV"),
                  "solidcraft_version_requested": os.environ.get("SOLIDCRAFT_VERSION")},
        "timeout_secs": r.timeout,
        "outcome": outcome,
        "stopped": stopped,
        "steps": r.steps,
        "report": rep.as_json(),
        "preview": preview,
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
    }
    with open(os.path.join(out, "result.json"), "w") as f:
        json.dump(result, f, indent=1, sort_keys=True)
    print(f"pair-check: pair #{result['pair_id']} -> {rep.status} ({rep.reason}); outcome {outcome}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
