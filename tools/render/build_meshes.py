"""Run with FreeCADCmd; render-only geometry, never submitted fixtures."""
import json
import math
import os
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ['FIXTURE_SOURCE'])  # a checkout of the recipes repository
OUT = ROOT / '.render-tmp'
OUT.mkdir(exist_ok=True)
V = App.Vector


def export(recipe, shapes, expected_volume):
    meshes = []
    volume = sum(s.Volume for s in shapes)
    assert all(s.isValid() and len(s.Solids) == 1 for s in shapes), recipe
    assert abs(volume - expected_volume) < 0.001, (recipe, volume)
    for shape in shapes:
        points, triangles = shape.tessellate(0.12)
        meshes.append({'vertices': [[p.x, p.y, p.z] for p in points],
                       'triangles': [list(t) for t in triangles]})
    (OUT / (recipe + '.json')).write_text(json.dumps(meshes))
    print('%s: %.3f mm^3, %d triangles' %
          (recipe, volume, sum(len(m['triangles']) for m in meshes)))


doc = App.openDocument(str(SOURCE / 'generated/freecad-1.1.4/P01a.FCStd'))
# The body's tip is the finished part, not intermediate sketch geometry.
bodies = [o for o in doc.Objects if o.TypeId == 'PartDesign::Body']
assert len(bodies) == 1
export('p01a', [bodies[0].Shape], 6000)
App.closeDocument(doc.Name)

# S02a: constant 2 mm wall, R1 inside / R3 outside bend. Outside
# height datum (Fig. 3 A), bend contained within the original y=60 edge.
# Base ends tangent at y=57; upright inside y=58, outside y=60.
base = Part.makeBox(100, 57, 2)
upright = Part.makeBox(100, 2, 17, V(0, 58, 3))
outer = Part.makeCylinder(3, 100, V(0, 57, 3), V(1, 0, 0))
inner = Part.makeCylinder(1, 100, V(0, 57, 3), V(1, 0, 0))
quadrant = Part.makeBox(100, 3, 3, V(0, 57, 0))
bend = outer.cut(inner).common(quadrant)
flange = base.fuse(bend).fuse(upright).removeSplitter()
export('s02a', [flange], 100 * (57 * 2 + 17 * 2 + math.pi * 2))

# A02a: one face mate fixes z only. Choose x=20, y=0 for the ring
# centre to show the contact and both parts; in-plane placement is free.
block = Part.makeBox(20, 30, 10, V(-10, -15, 0))
ring = Part.makeCylinder(30, 40, V(20, 0, 10)).cut(
    Part.makeCylinder(20, 40, V(20, 0, 10)))
export('a02a', [block, ring], 6000 + math.pi * 500 * 40)

# F04a: the visible result of the centred simple through hole.
# This Part boolean is for illustration, not a history fixture.
hole = block.cut(Part.makeCylinder(2.5, 10, V(0, 0, 0)))
export('f04a', [hole], 6000 - math.pi * 2.5**2 * 10)
