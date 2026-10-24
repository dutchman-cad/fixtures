# Example pictures

These are our own render-only FreeCAD shapes and booklet drawings. No volunteer
files or commercial CAD screenshots are used. Outputs are `docs/img/*.svg`.
Python uses only its standard library; FreeCAD uses public `Part` APIs.

From the checkout root, with FreeCAD 1.1.4 unpacked at the default runner path:

```sh
mkdir -p .render-tmp
export FIXTURE_SOURCE=/path/to/recipes-checkout   # has recipes.html and generated/freecad-1.1.4/
python tools/render/drawings.py
env HOME="$PWD/.render-tmp" \
  XDG_CONFIG_HOME="$PWD/.render-tmp/config" \
  XDG_DATA_HOME="$PWD/.render-tmp/data" \
  XDG_CACHE_HOME="$PWD/.render-tmp/cache" \
  /path/to/FreeCAD-1.1.4/usr/bin/freecadcmd \
  tools/render/build_meshes.py
python tools/render/render_meshes.py
```

`FIXTURE_SOURCE` contains our read-only `recipes.html` booklet (v1.23) and
`generated/freecad-1.1.4/P01a.FCStd` CC0 build. The scripts never write there.
FreeCAD's temporary home and triangle JSON stay in gitignored `.render-tmp/`.

- P01a loads the finished body of our CC0 build. Its drawing preserves Fig. 1,
  with an added height label and standalone SVG definitions and text styles.
- S02a is a 100 × 60 mm base with 2 mm wall, R1 inside bend, and 90° flange.
  The render uses Fig. 3 A: 20 mm from the outside bottom face, with the outside
  upright at y=60. S02a leaves datum and bend position to each app's defaults;
  this is one permitted illustration, not a claim that all apps agree.
  The drawing preserves all three Fig. 3 alternatives (bend enlarged as in the
  booklet), adding the base size, thickness, radius, and angle.
- A02a uses the P01/P02 dimensions and zero face-mate offset. A single mate leaves
  sideways placement free. Ring centre x=20, y=0, bottom z=10 makes contact visible.
  The new side section uses that same placement. These are placed solids for
  rendering; no assembly constraint solver or fixture history is claimed.
- F04a shows the centred Ø5 through hole in F01a's block. Its drawing is new.
  The Part boolean illustrates the finished shape, not a native hole feature.

The renderer projects tessellated shapes isometrically from (−X, −Y, +Z), culls
back faces, merges adjacent coplanar triangles, and sorts the resulting patches back to front
by centroid depth. Faces receive
one of three teal fills from their normals. Coincident mesh vertices are welded;
only boundary edges and edges with adjacent-normal angles over 20° are stroked.
Visible mesh boundaries also receive silhouette strokes. Triangle diagonals are
never outlined. Crisp fill rasterization avoids seams between curved patches;
outline strokes retain antialiasing. Smooth cylindrical silhouettes come from
the filled mesh. Backgrounds remain transparent; the page supplies a light panel
in both themes. The SVG size assertion is 60,000 bytes per rendered image.

`build_meshes.py` checks solid validity and analytic volumes. Painter sorting is
intended for these four static views, not arbitrary intersecting geometry.
