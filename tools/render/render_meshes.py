"""Standard-library triangle renderer: isometric projection and painter sorting."""
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PALETTE = ('#b4d0c4', '#c9ddd4', '#e2efe9')
VIEW = (-1 / math.sqrt(3), -1 / math.sqrt(3), 1 / math.sqrt(3))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def normal(a, b, c):
    u, v = sub(b, a), sub(c, a)
    n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    length = math.sqrt(dot(n, n))
    return tuple(x / length for x in n) if length else (0, 0, 0)


def project(p):
    x, y, z = p
    return ((x - y) / math.sqrt(2), (-x - y - 2*z) / math.sqrt(6))


def render(recipe):
    meshes = json.loads((ROOT / '.render-tmp' / (recipe + '.json')).read_text())
    points = [project(v) for mesh in meshes for v in mesh['vertices']]
    lo = [min(p[i] for p in points) for i in (0, 1)]
    hi = [max(p[i] for p in points) for i in (0, 1)]
    scale = min(300 / (hi[0]-lo[0]), 200 / (hi[1]-lo[1]))

    def xy(p):
        x, y = project(p)
        return (170 + scale*(x-(lo[0]+hi[0])/2), 115 + scale*(y-(lo[1]+hi[1])/2))

    layers = []
    for mesh in meshes:
        # Weld coincident tessellation vertices across CAD face boundaries.
        vertices, lookup, remap = [], {}, {}
        for i, v in enumerate(mesh['vertices']):
            key = tuple(round(c, 6) for c in v)
            if key not in lookup:
                lookup[key] = len(vertices)
                vertices.append(v)
            remap[i] = lookup[key]
        triangles = [tuple(remap[i] for i in t) for t in mesh['triangles']]
        normals = [normal(*(vertices[i] for i in t)) for t in triangles]
        adjacent = defaultdict(list)
        for ti, t in enumerate(triangles):
            for a, b in zip(t, t[1:] + t[:1]):
                adjacent[tuple(sorted((a, b)))].append(ti)
        sharp = {edge for edge, ts in adjacent.items()
                 if len(ts) == 1 or any(dot(normals[a], normals[b]) < math.cos(math.radians(20))
                                       for a in ts for b in ts)}
        # Merge adjacent coplanar triangles into polygon loops, including
        # inner loops for annular faces. This removes antialiasing seams.
        neighbors = defaultdict(set)
        for ts in adjacent.values():
            for a in ts:
                for b in ts:
                    if a != b and dot(normals[a], normals[b]) > 1 - 1e-8:
                        neighbors[a].add(b)
        seen = set()
        for ti in range(len(triangles)):
            if ti in seen:
                continue
            group, pending = set(), [ti]
            while pending:
                current = pending.pop()
                if current in group:
                    continue
                group.add(current)
                pending.extend(neighbors[current] - group)
            seen.update(group)
            n = normals[ti]
            if dot(n, VIEW) <= 1e-8:
                continue
            boundary = []
            for member in group:
                t = triangles[member]
                for a, b in zip(t, t[1:] + t[:1]):
                    if not any(other in group and other != member
                               for other in adjacent[tuple(sorted((a, b)))]):
                        boundary.append((a, b))
            following = dict(boundary)
            loops = []
            while following:
                first = next(iter(following))
                loop, current = [], first
                while True:
                    loop.append(current)
                    current = following.pop(current)
                    if current == first:
                        break
                loops.append(loop)
            path = ''.join('M' + 'L'.join('%.2f,%.2f' % xy(vertices[i]) for i in loop) + 'Z'
                           for loop in loops)
            light = dot(n, (-0.25, -0.45, 0.86))
            color = 2 if light > .65 else 1 if light > .1 else 0
            edges = []
            for a, b in boundary:
                edge = tuple(sorted((a, b)))
                # A boundary of the visible mesh is also a silhouette.
                silhouette = any(dot(normals[other], VIEW) <= 1e-8 for other in adjacent[edge])
                if edge in sharp or silhouette:
                    edges.append('M%.2f,%.2fL%.2f,%.2f' % (*xy(vertices[a]), *xy(vertices[b])))
            fragment = '<path d="%s" class="f%d" fill-rule="evenodd"/>' % (path, color)
            if edges:
                fragment += '<path d="%s" class="e"/>' % ''.join(edges)
            indices = {i for member in group for i in triangles[member]}
            depth = sum(dot(vertices[i], VIEW) for i in indices) / len(indices)
            layers.append((depth, fragment))
    # Planar regions have merged loops; no triangle diagonals are stroked.
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="340" height="230" viewBox="0 0 340 230">\n'
    svg += '<style>.f0,.f1,.f2{shape-rendering:crispEdges}.f0{fill:#b4d0c4}.f1{fill:#c9ddd4}.f2{fill:#e2efe9}.e{fill:none;stroke:#1d2321;stroke-width:1.15;stroke-linejoin:round}</style>\n'
    svg += '\n'.join(fragment for _, fragment in sorted(layers, key=lambda p: p[0])) + '\n</svg>\n'
    target = ROOT / 'docs/img' / (recipe + '-render.svg')
    target.write_text(svg)
    assert target.stat().st_size < 60000, target
    print(target.name, target.stat().st_size, 'bytes')


if __name__ == '__main__':
    for recipe in ('p01a', 's02a', 'a02a', 'f04a'):
        render(recipe)
