# Creo Fixture Builder kit

Everything needed to build the Creo fixtures, by script or by hand, from the Creo page of our Fixture Builders
site. Download these into one folder:
[KIT.md](https://fixtures.dutchmancad.xyz/builders/creo/KIT.md),
[creo_fixtures.json](https://fixtures.dutchmancad.xyz/builders/creo/creo_fixtures.json),
[build_creo.html](https://fixtures.dutchmancad.xyz/builders/creo/build_creo.html),
[creo_recipes.creojs](https://fixtures.dutchmancad.xyz/builders/creo/creo_recipes.creojs),
[pack_creo.ps1](https://fixtures.dutchmancad.xyz/builders/creo/pack_creo.ps1).

| File | What it is | Yours to edit? |
|---|---|---|
| `creo_fixtures.json` | Every Creo design (97): file name, template, booklet steps, the Creo tools, the expected values, and for a twin the one number that changes | no (generated) |
| `build_creo.html` | The builder: a Creo.JS page that makes or opens each design, checks it against the answer key, blanks personal parameters, saves, exports STEP, and writes `results.json` and `FixtureBuilder.log` | no (generated) |
| `creo_recipes.creojs` | One function per design. This is where your code goes | **yes** |
| `pack_creo.ps1` | Zips a run folder for us, with a privacy scan, and prints the finish line | no (generated) |
| `probe_creo.html`, `probe_creo.ps1` | What your Creo can script (Creo.JS, VB API) | no |

The answer key is the recipe booklet (<https://fixtures.dutchmancad.xyz/booklet.pdf>, Creo section and tool table) and
its expected values; `creo_fixtures.json` carries both, so you need nothing else.

## Run it

1. Make a new, empty folder outside your user folder: `C:\Users\Public\FixtureOut\creo-1` (the next run gets
   `creo-2`, and so on). Creo writes the folder it saves in into every file, so the builder refuses a folder inside
   your user folder, OneDrive or a network share.
2. Put `build_creo.html`, `creo_recipes.creojs` and `pack_creo.ps1` in it, and copy `creojs.js` from your Creo.JS
   setup next to them (we don't ship PTC's files).
3. Start Creo. **File → Manage Session → Select Working Directory**, and pick that folder.
4. Open `build_creo.html` in Creo's browser, the way you open your other Creo.JS pages.
5. Type your Creo release (for example `10.0.3.0`) and click **Run**. Leave Creo alone until the line under the
   buttons changes. To build only some designs, list them in **Only these designs** (`P01a P01b`).
6. If the page says Creo didn't let it write files, click **Save results** and **Save log** and put both files in
   the folder. (Creo.JS writes files only when `config.pro` has `web_link_file_read yes`.)
7. Open Windows PowerShell and run:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Public\FixtureOut\creo-1\pack_creo.ps1" -Folder "C:\Users\Public\FixtureOut\creo-1"
   ```

8. It ends with `N recipes: X built, Y failed, Z not scripted` and the zip's path. Send that zip to **Dutchy** in a
   Discord direct message, and say which Creo release you used.

## What the builder does with each design

In booklet order, for each design in `creo_fixtures.json`:

1. **A file in the folder:** if `p01a.prt` (or `.asm`) is already there, made by hand or by an earlier run, it
   opens it. Untick **Use files already in the folder** to skip this.
2. **Your function:** otherwise it calls `RECIPES.P01a(ctx)` from `creo_recipes.creojs`, if you wrote one.
3. **A twin with one number changed:** otherwise, if the design's `single_change` is set (P01b: the extrude depth
   10 → 12) and its base was built in this run, it copies the base and changes the one dimension whose value is
   `from` (it refuses when none or several match).
4. Otherwise the design is `not_scripted`, with the reason, never skipped silently.

Then it checks a part against the answer key: volume within 1e-4 (relative) and bounding box within 0.01 mm,
where the key has them. An assembly from A11 on is checked against its entry in the answer key's `assemblies`
(`expect.assembly` in `creo_fixtures.json`):
- the number of active parts and of assembly levels;
- the bounding box (0.01 mm, or the key's `bbox_tol`);
- every part's position `t` (0.01 mm) and turn `R` (1e-4) in the top assembly, where the key scores them.

Creo has no instance names, so parts are matched to the key by part file and position. A family-table member or a
new mirrored part carries its own name and is matched by position. A suppressed part must be there and suppressed.
Motion keys (`free`, `dof`, `limits`, `pose`, `probes`) are not read by this builder; they are listed under
`measured.not_checked`. A10 and earlier assemblies have no key: we check those from the zip.

A design that doesn't match is `failed` with the numbers and is not saved. A twin the booklet's Creo tool table says
Creo cannot make (A19c, A23b) is `not_scripted` with that reason. Then it blanks personal parameters (`MODELED_BY`, `AUTHOR`,
`CREATED_BY` and the like), saves, and exports `p01a.stp` next to it.

`results.json` rows: `{"id": "P01a", "status": "ok" | "failed" | "not_scripted", "error": "<Creo's exact error
text>", "files": ["p01a.prt", "p01a.step"], "app": "Creo", "version": "10.0.3.0", "build": "", "builder":
"<builder version>", "seconds": 1.2, "made": "scripted" | "opened" | "twin of P01a", "measured": {...}}`. File names
only, never a path.

## Writing a design function

```js
var RECIPES = {
  // Template route: a block you made once by hand, saved as template_block.prt in the run folder.
  P01a: (ctx) => ctx.fromTemplate('template_block.prt', [[10, 10]]),
  // A design this Creo can't make: say which Creo fact stops it.
  P15b: (ctx) => ctx.notScripted('<the Creo.JS call that is missing, and what you tried>'),
};
```

A function returns the finished model, in the session, named after the design (`ctx.copyAs(model)` does that). It
gets `ctx`:

| `ctx.` | does |
|---|---|
| `design` | this design's row from `creo_fixtures.json` (`id`, `file`, `kind`, `template`, `steps`, `ops`, `expect`, `single_change`, `uses`) |
| `session` | the Creo session (`pfcGetCurrentSession()`) |
| `built` | the models already built in this run, by design id (`ctx.built.P01a`) |
| `open(file)` | retrieves a file from the working folder, or returns null |
| `copyAs(model)` | a copy of `model` under this design's name |
| `setDimension(model, from, to)` | changes the one dimension whose value is `from`, then regenerates |
| `setParameter(model, name, value)` | sets or creates a parameter |
| `fromTemplate(file, [[from, to], ...])` | copies a template part and changes its dimensions |
| `mapkey(text)` | runs a mapkey (Creo runs it after control returns to it, so it is not finished when the call returns) |
| `log(step)` | a line in `FixtureBuilder.log` |
| `notScripted(reason)` | stops this design as `not_scripted` with your reason |

What Creo.JS can and can't do (PTC's public Creo.JS reference): `Solid.CreateFeature` is listed as "Not implemented
in the current release" (only the paid Object TOOLKIT builds features from element trees), so a function can't
draw a sketch and extrude it from scratch. What it can do: open files, copy them (`CopyAndRetrieve`), change
dimensions and parameters, suppress or resume features (`ExecuteFeatureOps`), place a UDF (`CreateUDFGroup`), run a
mapkey (`RunMacro`), assemble components (`AssembleComponent`), regenerate, measure, save and export. Build with
those, or make a design by hand and let the builder check and pack it.

The rules each design follows (from the booklet):

- Real Creo features, as the steps and the Creo tool table say; fully constrained sketches; millimeters.
- Start from the design's `template` (`mmns_part_solid_abs`, `mmns_part_sheetmetal_abs`, `mmns_asm_design_abs`).
- A twin is its base with the one change in `twin_change`, nothing else.
- Assemblies use the part files named in `uses`, from the same folder.
- If a step has no exact Creo match, use the closest tool and say what you did (a `ctx.log` line is enough).

## Making designs by hand

Make the part from its `steps` in `creo_fixtures.json` (or the booklet), save it in the run folder as its `file`
name, and run the builder. It opens your file, checks it against the answer key, exports STEP and packs it. A
`failed` row tells you which number is off. Mix freely: some designs scripted, some by hand.

## Privacy

Nothing in `results.json` or the log is a path or a name. The builder runs only in a folder outside your user
folder (Creo writes the folder it saves in into every file), and blanks personal parameters before each save.
`pack_creo.ps1` refuses a folder inside your user folder or OneDrive. It scans every file, raw and inside its
compressed streams, for your user folder, OneDrive, user name and PC name. A design whose file has one is marked
`failed` in the zipped `results.json`, and its files are left out (it names them). The log and `results.json` go in
with those replaced by `%USERPROFILE%`, `%USERNAME%` and `%COMPUTERNAME%`. Each STEP copy in the zip carries only its bare file
name in its header, `Fixture Builder` as author and no organization; the copy in your folder is unchanged. Your files stay private unless you tell us they may join the public test collection
(CC0).

## Sending work back

Native CAD files (.prt, .asm…) carry your Windows user and computer name inside them; we keep native files private and publish only STEP and files we've checked clean.

- **Fixtures:** the zip `pack_creo.ps1` made, to **Dutchy** in a Discord direct message.
- **Code:** your `creo_recipes.creojs`, zipped, to Dutchy in a Discord direct message or in your Creo thread.
  Contributions are CC0 (public domain). Original code only: no PTC sample code, no `creojs.js`, no other PTC
  files. We fold your functions into the published kit, so the next person with another Creo release runs the
  same thing. If the parent itself needs a change, say what and why; we change its generator so every release
  gets it.

## Prompts for your own agent

Paste one into your coding agent, in the folder where you downloaded the kit files.

**1. Script the designs in Creo.JS**

```text
You are writing Creo.JS code for the Creo Fixture Builder. Read these first, in this folder (downloaded next to
https://fixtures.dutchmancad.xyz/builders/creo/KIT.md): KIT.md (the contract), creo_fixtures.json (every
design, its steps, its Creo tools, its expected values), creo_recipes.creojs (where your code goes) and
build_creo.html (the parent; read it, never edit it). Work only in creo_recipes.creojs.
Goal: as many designs as possible built with real Creo features and passing the parent's check (volume within 1e-4
relative, bounding box within 0.01 mm). Creo.JS cannot create features (Solid.CreateFeature is not implemented), so
use the routes KIT.md lists: template parts I make once by hand, dimension and parameter changes, feature
suppress/resume, UDFs, mapkeys, assembling components. Start with P01a and its twin P01b, then the other P designs,
then S (sheet metal), then A (assemblies). Each round: write a few functions, I run build_creo.html in Creo and
give you results.json and FixtureBuilder.log; fix the failures from Creo's exact error text. A design you cannot
build must call ctx.notScripted with the Creo fact that stops it, never a vague reason. If you need a template part
or a mapkey recorded, give me numbered click-by-click steps. Original code only: never copy PTC sample code or
files. Never write my name, my PC name or a path into any file. When a round is done, run pack_creo.ps1 and I send
the zip, and creo_recipes.creojs, to Dutchy in a Discord direct message.
```

**2. Make the designs by hand, with the builder as the checker**

```text
Help me make the Creo fixtures by hand. Read KIT.md and creo_fixtures.json in this folder
(downloaded next to https://fixtures.dutchmancad.xyz/builders/creo/KIT.md). For each design in order (P first, then S,
then A), give me numbered click-by-click steps for my Creo release from its "steps", the Creo tool table
("creo_tools") and its "template": which template, which plane, which values, the file name to save as, and for
a twin, which one value to change from its base. Keep each design to one short list. After every few designs I
run build_creo.html with "Use files already in the folder" ticked and give you results.json; for a failed row,
tell me what to fix from the measured numbers. Twins with a "single_change" are made by the builder itself, so
skip those once their base passes. At the end I run pack_creo.ps1 and send the zip to Dutchy in a Discord direct
message.
```
