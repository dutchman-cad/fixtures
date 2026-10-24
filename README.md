# CAD Fixture Recipes

We're building open, clean-room readers for native CAD files ([cadmpeg](https://github.com/cadmpeg/cadmpeg) and [SolidCraft](https://github.com/tangency-labs/solidcraft), used by [Dutchman](https://github.com/dutchman-cad/dutchman)). To test them we need small, known files made in the real apps: a block, a fillet, a flange, and two parts with a mate, each changing one thing at a time. Volunteers make them from short recipes, and every file helps.

**Portal:** https://fixtures.tailb5574c.ts.net/
**Community:** [Dutchman CAD on Discord](https://discord.gg/yTcseBEdeu)

## How it works

1. **Build a tiny part.** Follow the recipe on screen. Example: P01a is a 20 × 30 mm rectangle pulled up 10 mm.
2. **Make its twin.** Open P01a, change one thing, and Save As P01b. Here, 10 mm becomes 12 mm.
3. **Upload it.** Each file is checked right away. If something's off, you'll see what and why. Then on to the next one.

## Join in

- **Get your personal link:** ask in [Discord](https://discord.gg/yTcseBEdeu). It signs you in; there's no account or password.
- **Pick your app and year.** The portal walks you through each file, one per screen, with the recipe and a drawing. It takes about 15 to 45 minutes, depending on how far you go, and partial sets are welcome.
- **Drop each file on its box.** It's checked in seconds and you see the result. Questions go to a chat with the team.
- **You choose** whether your files join a public test collection (CC0) or stay private, for testing only.

## Programs

The recipes are written for **Inventor**, **Fusion**, **SolidWorks**, **Creo**, and **CATIA**, in any year or release. Each year stores files a little differently, so a year nobody has covered yet is especially welcome; the portal shows which ones are wanted. Fusion updates every month, so several sets from different people are worth more than one.

FreeCAD is free and scriptable, so we make its sets ourselves from the same recipes: no FreeCAD files needed from volunteers. The sets for FreeCAD 0.21.2, 1.0.2, and 1.1.4 (parts, sheet metal, history recipes, and, from 1.0, assemblies) are [free to download (CC0)](https://github.com/dutchman-cad/fixtures/releases).

Use something else? Tell us in [Discord](https://discord.gg/yTcseBEdeu) which program and year, and we'll add recipes for it.

## Test files

Public test files live in `files/<program>/<version>/`, one file per recipe and twin (`P01a.FCStd`), with a `manifest.json` per set: the recipe ID, the program build, the expected values from the booklet, what was measured, and the check result. They are CC0, so cadmpeg, other CAD readers, or anyone else may use them as an external test set.

Today that is the FreeCAD 0.21.2, 1.0.2, and 1.1.4 sets, which we make from the recipes. Volunteer files join only when their sender chose CC0, and only after a check that nothing private is inside them. The release zips are built from these folders (`tools/release/freecad-zips.sh`), so the two always match.

## Help

Ask anything in the [Dutchman CAD Discord](https://discord.gg/yTcseBEdeu), or use the team chat inside the portal. The latest recipe booklet (PDF) is linked from the portal. Already helping and lost your link? Ask in Discord for a new one.
