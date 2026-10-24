"""Extract our booklet figures and draw the two missing recipe diagrams."""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ['FIXTURE_SOURCE'])  # a checkout of the recipes repository
booklet = (SOURCE / 'recipes.html').read_text()
STYLE = '''<style>text{font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:11px;fill:#1d2321}.b{font-weight:600}.w{fill:#8a5a00}.a{fill:#1f6f5c}</style>'''
defs = re.search(r'<svg id="figdefs".*?<defs>(.*?)</defs>', booklet, re.S).group(1)


def save(name, content, width=340, height=230, extra_defs=''):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
           % (width, height, width, height))
    svg += STYLE + '<defs>' + defs + extra_defs + '</defs>' + content + '</svg>\n'
    (ROOT / 'docs/img' / (name + '-drawing.svg')).write_text(svg)


# Preserve the complete original Fig. 1, including its edge callouts.
figure1 = re.search(r'<svg viewBox="0 0 340 230"[^>]*>(.*?)</svg>', booklet, re.S).group(1)
save('p01a', figure1 + '<text x="220" y="214">Height 10 mm</text>')

# Preserve all three Fig. 3 datum illustrations, not just one option.
figure3 = re.search(r'<svg viewBox="0 0 480 205"[^>]*>(.*?)</svg>', booklet, re.S).group(1)
save('s02a', figure3 + '''<text x="10" y="214" class="b">S02a: 100 × 60 mm base · thickness 2 · inside R1 · 90°</text>
<text x="10" y="232">Height 20 mm; datum and bend position follow the part's defaults.</text>''', 480, 245)

# A02a side section in XZ. Ring centred at x=20, z=10, as in render.
# Scale 3 px/mm; the ring's two walls are x=-10..0 and 40..50.
save('a02a', '''
<text x="18" y="18" class="b">A02a · side section (XZ) · mm</text>
<g transform="translate(0,24)">
<path d="M50 180H110V150H50Z" fill="#c9ddd4" stroke="#1d2321" stroke-width="1.5"/>
<path d="M50 150V30H80V150ZM200 150V30H230V150Z" fill="#e2efe9" stroke="#1d2321" stroke-width="1.5"/>
<path d="M50 150H80" stroke="#1f6f5c" stroke-width="3"/>
<text x="120" y="169" class="a">Mate: offset 0</text>
<path d="M123 159L72 151" stroke="#1f6f5c" fill="none" marker-end="url(#ar)"/>
<path d="M50 26V9M230 26V9M52 12H228" stroke="#5b6662" fill="none"/>
<text x="140" y="10" text-anchor="middle">Ø60 outside / Ø40 inside</text>
<path d="M237 30H262M237 150H262M255 32V148" stroke="#1d2321" fill="none" marker-start="url(#ar)" marker-end="url(#ar)"/>
<text x="266" y="94">40</text>
<text x="18" y="202">Block: 20 × 30 × 10; ring bottom at z = 10.</text>
<text x="18" y="219">Ring centre x = 20, y = 0; sideways position is free.</text>
</g>
''', height=260)

save('f04a', '''
<text x="18" y="18" class="b">F04a · top view · mm</text>
<rect x="72" y="38" width="80" height="120" fill="#e2efe9" stroke="#1d2321" stroke-width="1.5"/>
<circle cx="112" cy="98" r="10" fill="white" stroke="#1d2321" stroke-width="1.5"/>
<path d="M95 98H129M112 81V115" stroke="#5b6662" stroke-dasharray="3 3"/>
<path d="M72 165V187M152 165V187M74 180H150" stroke="#1d2321" fill="none" marker-start="url(#ar)" marker-end="url(#ar)"/>
<text x="112" y="197" text-anchor="middle">20 (X)</text>
<path d="M159 38H183M159 158H183M176 40V156" stroke="#1d2321" fill="none" marker-start="url(#ar)" marker-end="url(#ar)"/>
<text x="184" y="103">30 (Y)</text>
<path d="M235 57H161L120 91" stroke="#1d2321" fill="none" marker-end="url(#ar)"/>
<text x="210" y="48" class="b">Ø5 through</text>
<text x="210" y="73">at (0, 0, 10)</text>
<text x="18" y="219">Height 10 mm · hole at the top face centre.</text>
''')
