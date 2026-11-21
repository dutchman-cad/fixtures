"""Tests for the pair checker's verdict rules. Run: python3 -m unittest discover -s tools/pair-check"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pair_check as pc  # noqa: E402


def part(faces, volume, dims):
    return {"faces": faces, "volume": volume, "dims": list(dims)}


def analysis(parts):
    return {"bodies": float(len(parts)), "faces": float(sum(p["faces"] for p in parts)),
            "volume": sum(p["volume"] for p in parts), "bbox": [30.0, 20.0, 10.0], "errors": 0.0,
            "warnings": 0.0, "seconds": 0.0, "rev": None, "losses": set(), "parts": parts}


MAIN = part(174, 16332.2, (30.0, 20.0, 10.0))
SMALL = part(3, 3.2, (2.0, 2.0, 1.0))


class ReferenceIncomplete(unittest.TestCase):
    def test_pair2_shape_is_a_pass_with_the_extra_body_listed(self):
        nat, stp = analysis([SMALL, MAIN]), analysis([MAIN])
        self.assertEqual(pc.verdict(nat, stp), (
            "pass", "pass, reference incomplete: every STEP body matched; the design has 1 more body "
                    "(3.2 mm3) that the STEP doesn't contain"))
        with tempfile.TemporaryDirectory() as d:
            step_path = os.path.join(d, "reference.step")
            with open(step_path, "w") as f:
                f.write("ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\n#1=MANIFOLD_SOLID_BREP('a',#2);\nENDSEC;\nEND-ISO-10303-21;\n")
            rep = pc.pair_report(nat, (stp, None), step_path, "r")
        self.assertEqual(rep.status, "pass")
        self.assertEqual(rep.metrics["reference_incomplete"], 1.0)
        self.assertEqual(rep.metrics["extra_bodies"], 1.0)
        self.assertEqual(rep.metrics["extra_body_1_volume_mm3"], 3.2)

    def test_unmatched_step_body_stays_partial(self):
        nat = analysis([SMALL, MAIN])
        for other in (part(174, 16000.0, (30.0, 20.0, 10.0)), part(170, 16332.2, (30.0, 20.0, 10.0))):
            self.assertEqual(pc.verdict(nat, analysis([other])), ("partial", "bodies: native 2 vs STEP 1"))

    def test_step_with_more_bodies_stays_partial(self):
        self.assertEqual(pc.verdict(analysis([MAIN]), analysis([SMALL, MAIN])),
                         ("partial", "bodies: native 1 vs STEP 2"))

    def test_equal_bodies_unchanged(self):
        status, reason = pc.verdict(analysis([MAIN]), analysis([MAIN]))
        self.assertEqual((status, reason), ("pass", "matches STEP reference"))

    def test_without_per_body_data_stays_partial(self):
        nat = analysis([SMALL, MAIN])
        nat["parts"] = []
        self.assertEqual(pc.verdict(nat, analysis([MAIN]))[0], "partial")

    def test_eval_bodies_carry_their_own_volume_and_box(self):
        body = lambda v, x: {"faces": 6, "volume_mm3": v, "bbox": {"min": [0, 0, 0], "max": [x, 1, 1]}}
        m = pc.eval_measure({"bodies": [body(1.0, 2.0), body(3.0, 4.0)]})
        self.assertEqual(m["parts"][1], {"faces": 6, "volume": 3.0, "dims": [4.0, 1.0, 1.0]})


if __name__ == "__main__":
    unittest.main()
