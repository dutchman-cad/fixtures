# CAD Fixture Recipes

We're building open, clean-room readers for native CAD files ([cadmpeg](https://github.com/cadmpeg/cadmpeg) and [SolidCraft](https://github.com/tangency-labs/solidcraft), used by [Dutchman](https://github.com/dutchman-cad/dutchman)). To test them we need small, known files made in the real apps: a block, a fillet, a flange, two parts with a mate, and a drawing of a part, each changing one thing at a time. Volunteers make them from short recipes, and every file helps.

**Portal:** https://fixtures.tailb5574c.ts.net/
**Community:** [Dutchman CAD on Discord](https://discord.gg/yTcseBEdeu)

## How it works

1. **Build a tiny part.** Follow the recipe on screen. Example: P01a is a 20 × 30 mm rectangle pulled up 10 mm.
2. **Make its twin.** Open P01a, change one thing, and Save As P01b. Here, 10 mm becomes 12 mm.
3. **Upload it.** Each file is checked right away. If something's off, you'll see what and why. Then on to the next one.

## Join in

- **Get your personal link:** join the [Discord](https://discord.gg/yTcseBEdeu) and type **/volunteer**. The link signs you in; there's no account or password.
- **Pick your app and year.** The portal walks you through each file, one per screen, with the recipe and a drawing. It takes about 15 to 45 minutes, depending on how far you go, and partial sets are welcome.
- **Drop each file on its box.** It's checked in seconds and you see the result. Questions go to a chat with the team.
- **You choose** whether your files join a public test collection (CC0) or stay private, for testing only.

## Programs

The recipes are written for **Inventor**, **Fusion**, **SolidWorks**, **Creo**, **CATIA**, and **NX**, in any year or release. Each year stores files a little differently, so a year nobody has covered yet is especially welcome; the portal shows which ones are wanted. Fusion updates every month, so several sets from different people are worth more than one.

Drawings are wanted too: Fusion, Inventor, and SolidWorks drawings each have their own recipes, from a single view to two sheets with views at three scales and dimensions. Each drawing is sent with a DXF of its sheets; a PDF is welcome but optional.

FreeCAD is free and scriptable, so we make its sets ourselves from the same recipes: no FreeCAD files needed from volunteers. The sets for FreeCAD 0.21.2, 1.0.2, and 1.1.4 (parts, sheet metal, history recipes, FreeCAD-only recipes, and, from 1.0, assemblies) are [free to download (CC0)](https://github.com/dutchman-cad/fixtures/releases).

Use something else? Tell us in [Discord](https://discord.gg/yTcseBEdeu) which program and year, and we'll add recipes for it.

## Want to help us improve?

Send us a design of your own: one CAD file and, if you can, a STEP export of the same design. Direct-message it to Dutchy on the [Discord](https://discord.gg/yTcseBEdeu), or, if you already have a portal link, use **Your own files** there. We compare what our readers get from your file with the STEP your program wrote.

Formats: Fusion (.f3d, .f3z), Inventor (.ipt, .iam), SolidWorks (.sldprt, .sldasm), CATIA V5 (.CATPart), Creo and NX (.prt, including numbered saves such as .prt.3), Creo View (.pvz), Rhino (.3dm), ACIS (.sat, .sab, .smt, .smb), FreeCAD (.FCStd), and IGES (.igs, .iges).

For the STEP export, pick AP242 if your program offers it, otherwise AP214; solid (B-rep), not mesh; the same units as the design; one file for an assembly. You choose whether your files stay private or join the public test collection (CC0).

A drawing helps too: send the drawing (Inventor .idw or .dwg, SolidWorks .slddrw, Creo .drw, CATIA .CATDrawing, or a Fusion drawing exported as a Fusion Archive, .f3z), the part or assembly it shows, and a DXF export of each sheet (or one .zip of them), all in one message; a PDF of the sheets is welcome but optional. The DXF is what we check the drawing against, so export it at scale 1:1, in millimetres, with text kept as text (not exploded), as AutoCAD 2000 or 2018 DXF.

## Test files

Public test files live in `files/<program>/<version>/`, one file per recipe and twin (`P01a.FCStd`), with a `manifest.json` per set: the recipe ID, the program build, the expected values from the booklet, what was measured, and the check result. They are CC0, so cadmpeg, other CAD readers, or anyone else may use them as an external test set.

Today that is the FreeCAD 0.21.2, 1.0.2, and 1.1.4 sets, which we make from the recipes. Volunteer files join only when their sender chose CC0, and only after a check that nothing private is inside them. The release zips are built from these folders (`tools/release/freecad-zips.sh`), so the two always match.

## Help

Ask anything in the [Dutchman CAD Discord](https://discord.gg/yTcseBEdeu), or use the team chat inside the portal. The latest recipe booklet (PDF) is linked from the portal. Already helping and lost your link? Ask in Discord for a new one.
