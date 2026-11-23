# Fixture Builders: contributing

A Fixture Builder is a script that runs inside a CAD program and makes the booklet's recipes there, with real
features, so a volunteer gets a whole set in one run instead of drawing every part by hand. We publish builders for
Inventor, SolidWorks, Fusion, Solid Edge, Onshape, Alibre Design and FreeCAD on
<https://fixtures.dutchmancad.xyz/builders/>. This folder is where contributors work on builders for programs we
can't run ourselves.

| Program | Folder | State |
|---|---|---|
| Creo Parametric | [creo/](creo/) | Creo.JS kit: fixture list, parent builder, one function per design to write. Start with [creo/KIT.md](creo/KIT.md) |

## What every builder does

These rules are the same for every program, so results from any builder read back the same way.

1. **One run, one new folder.** Never delete, empty, overwrite or reuse an output folder. A taken name gets `-2`,
   `-3` and so on.
2. **Every design appears in `results.json`**, in booklet order, one row each:
   `{"id": "P01a", "status": "ok" | "failed" | "not_scripted", "error": "...", "files": ["p01a.prt", "p01a.step"],
   "app": "...", "version": "...", "build": "...", "builder": "<builder version>", "seconds": 1.2}`.
   `failed` carries the program's exact error text. `not_scripted` carries a reason that names the fact that
   stops it (the API call that is missing, and what was tried), never "not done". Nothing is skipped silently.
3. **Checked against the answer key.** A part's volume and bounding box are measured and compared with the
   booklet's expected values before it is saved; a part that doesn't match is `failed`, with the numbers.
4. **Native file plus STEP.** Each design is saved in the program's own format, with a STEP copy (AP242 if the
   program offers it, otherwise AP214) next to it.
5. **Privacy first.** Author, company and similar fields are blanked before every save. No user name, PC name or
   path goes into any file, log or `results.json` (file names only). New builders also scan every file for the
   user and PC name before zipping and leave out any file that still has one (Creo's `pack_creo.ps1` does).
6. **A log.** `FixtureBuilder.log` lines: `<time> builder=<version> recipe=<id> step=<what happened>`.
7. **One zip, one finish line.** The run ends with one zip, named after the program, version and build, and this
   message: `N recipes: X built, Y failed, Z not scripted (details in FixtureBuilder.log).` followed by
   `Next: send this zip to Dutchy in a Discord direct message:` and the zip's path.
8. **Builder versions** are `YYYY.MM.DD.N`, the date the version was made, counting up within a day.

## How to contribute

- **Code:** open a pull request that changes the files the program's guide marks as yours (for Creo,
  `creo/creo_recipes.creojs`), or send that file to Dutchy in a Discord direct message. Files marked generated are made by our generator from the recipe spec, so every
  program and release gets the same fix; if one of them needs a change, say what and why in the pull request and
  we change the generator.
- **Licence:** contributions to this repository are CC0 (public domain), like the test files.
- **Original code only.** No sample code, headers, libraries or other files from the CAD vendor's SDK, and no
  code copied from another program's documentation. Use the vendor's public API reference to learn what a call
  does, then write your own.
- **No personal data** in code, logs, tests or commit messages.
- **Fixtures** a builder made go to Dutchy as the zip, in a Discord direct message, not into a pull request. Files
  join the public collection in `files/` only when their maker chose CC0 and after our privacy check.
- **Questions:** the [Dutchman CAD Discord](https://discord.gg/yTcseBEdeu), in the fixtures help forum.

## Using a coding agent

Each program's guide has ready prompts for an agent (Creo: the end of [creo/KIT.md](creo/KIT.md)). Point the agent
at the program's folder in this repository; the guide, the fixture list and the parent builder are all it needs.
