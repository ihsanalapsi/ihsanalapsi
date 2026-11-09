#!/usr/bin/env python3
"""Build the static SVGs of this profile: the banner and the project cards.

Crimson Orbit colours (charcoal, deep, burgundy, red, ivory). The text keeps
its real fonts: Geist and Geist Mono are subset to the glyphs each SVG uses
and embedded as WOFF2, since an SVG shown as an image can't load anything
from outside. Motion is CSS/SMIL only and stops under prefers-reduced-motion.

Needs fontTools and brotli (pip install fonttools brotli). From the repo root:
    python3 scripts/build_static.py
The daily parts (terminal card, latest articles) are scripts/update.py.
"""
import base64
import io
import math
import pathlib

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
OUT = ROOT / "assets"

DEEP, CHAR, WINE, RED, HI, IVORY = "#100C0D", "#1B1716", "#470C17", "#E90507", "#FF3B45", "#F0EDE2"
PANEL2 = "#17120F"
W74 = "rgba(255,255,255,.74)"
LINE = "rgba(240,237,226,.12)"

# The iA mark, exactly as public/brand/ia-mark-light.svg on the site, with white ink (designs).
MARK_VIEWBOX = (35.31, 62.22, 441.38, 387.56)
MARK_INK = [
    "123.25,163.58 35.31,225.16 35.31,440.83 123.25,343.16",
    "252.94,62.22 160.52,222.29 160.52,296.82 219.37,194.89 366.53,449.78 476.69,449.78",
    "269.29,329.04 168.06,329.04 59.35,449.78 109.49,449.78 184.65,366.30 290.80,366.30",
]
MARK_BLOCK = "123.25,73.35 35.31,134.93 35.31,196.05 123.25,134.47"


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Face:
    """A variable font: measures text and emits a subset @font-face."""

    def __init__(self, file, family):
        self.path = FONTS / file
        self.family = family
        self.upm = TTFont(self.path)["head"].unitsPerEm
        self._instances = {}

    def _instance(self, wght):
        if wght not in self._instances:
            self._instances[wght] = instancer.instantiateVariableFont(TTFont(self.path), {"wght": wght})
        return self._instances[wght]

    def width(self, text, size, wght=400, tracking=0.0):
        """Advance width in px (kerning left out; close enough to centre a line)."""
        font = self._instance(wght)
        cmap, hmtx = font.getBestCmap(), font["hmtx"]
        units = sum(hmtx[cmap.get(ord(ch), ".notdef")][0] for ch in text)
        return units * size / self.upm + tracking * size * len(text)

    def css(self, text):
        font = TTFont(self.path)
        options = subset.Options()
        options.flavor = "woff2"
        options.layout_features = ["*"]
        options.notdef_outline = True
        subsetter = subset.Subsetter(options)
        subsetter.populate(text=text + " ")
        subsetter.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        return f'@font-face{{font-family:"{self.family}";src:url(data:font/woff2;base64,{data}) format("woff2");font-weight:100 900}}'


SANS = Face("Geist-Variable.woff2", "Geist")
MONO = Face("GeistMono-Variable.woff2", "Geist Mono")


def mark(x, y, height):
    vx, vy, vw, vh = MARK_VIEWBOX
    s = height / vh
    ink = "".join(f'<polygon points="{p}" fill="#FFFFFF"/>' for p in MARK_INK)
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({s:.5f}) translate({-vx} {-vy})" role="img" aria-label="iA">'
            f'{ink}<polygon points="{MARK_BLOCK}" fill="{RED}"/></g>'), vw * s


def ellipse_path(cx, cy, rx, ry):
    """Clockwise from the left end, so a point moving along it passes over the top first."""
    return f"M {cx - rx} {cy} a {rx} {ry} 0 1 1 {2 * rx} 0 a {rx} {ry} 0 1 1 {-2 * rx} 0"


def grid(w, h, cell, uid):
    return (f'<pattern id="g{uid}" width="{cell}" height="{cell}" patternUnits="userSpaceOnUse">'
            f'<path d="M {cell} 0 L 0 0 0 {cell}" fill="none" stroke="rgba(240,237,226,.05)" stroke-width="1"/></pattern>'
            f'<radialGradient id="gm{uid}" cx="50%" cy="50%" r="60%"><stop offset=".35" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="m{uid}"><rect width="{w}" height="{h}" fill="url(#gm{uid})"/></mask>')


REDUCED = "@media (prefers-reduced-motion: reduce){.motion{display:none}.spin{animation:none}}"


# --- Banner -----------------------------------------------------------------

def banner():
    w, h, cx, cy = 1280, 320, 640, 160
    name, role, site = "Ihsan Alapsi", "Software Engineer & Penetration Tester", "IHSANALAPSI.DEV"
    name_size, role_size, site_size = 76, 24, 14
    name_w = SANS.width(name, name_size, 700, -0.04)
    role_w = SANS.width(role, role_size, 400, -0.01)
    site_w = MONO.width(site, site_size, 500, 0.28) + 22
    mark_h, gap = 92, 30
    mark_svg_w = MARK_VIEWBOX[2] * mark_h / MARK_VIEWBOX[3]
    text_w = max(name_w, role_w, site_w)
    total = mark_svg_w + gap + 1 + gap + text_w
    left = cx - total / 2
    mark_svg, _ = mark(left, cy - mark_h / 2, mark_h)
    div_x = left + mark_svg_w + gap
    tx = div_x + 1 + gap
    orbit = ellipse_path(cx, cy, 590, 146)
    fonts = SANS.css(name + role) + MONO.css(site)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Ihsan Alapsi, Software Engineer and Penetration Tester, ihsanalapsi.dev">
<style>{fonts}
.name{{font:700 {name_size}px "Geist",sans-serif;letter-spacing:-.04em;fill:#fff}}
.role{{font:400 {role_size}px "Geist",sans-serif;letter-spacing:-.01em;fill:{W74}}}
.site{{font:500 {site_size}px "Geist Mono",monospace;letter-spacing:.28em;fill:{HI}}}
{REDUCED}</style>
<defs>
<clipPath id="clip"><rect width="{w}" height="{h}" rx="18"/></clipPath>
<linearGradient id="bg" x1="0" x2="1"><stop offset="0" stop-color="{DEEP}"/><stop offset=".5" stop-color="{CHAR}"/><stop offset="1" stop-color="{DEEP}"/></linearGradient>
<radialGradient id="wine" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{WINE}" stop-opacity=".62"/><stop offset="1" stop-color="{WINE}" stop-opacity="0"/></radialGradient>
<linearGradient id="orbit" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{RED}" stop-opacity="0"/><stop offset=".18" stop-color="{RED}" stop-opacity=".75"/><stop offset=".5" stop-color="{HI}" stop-opacity=".3"/><stop offset=".82" stop-color="{RED}" stop-opacity=".85"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></linearGradient>
<radialGradient id="glow"><stop offset="0" stop-color="{RED}" stop-opacity=".45"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>
{grid(w, h, 32, "b")}
</defs>
<g clip-path="url(#clip)">
<rect width="{w}" height="{h}" fill="url(#bg)"/>
<ellipse cx="{cx}" cy="{cy}" rx="{w * .42}" ry="{h * .75}" fill="url(#wine)"/>
<rect width="{w}" height="{h}" fill="url(#gb)" mask="url(#mb)"/>
<g transform="rotate(-4 {cx} {cy})">
<path d="{orbit}" fill="none" stroke="url(#orbit)" stroke-width="1.6"/>
<circle cx="{cx - 470}" cy="{cy - 88}" r="12" fill="url(#glow)"/><circle cx="{cx - 470}" cy="{cy - 88}" r="3" fill="{HI}"/>
<circle cx="{cx + 300}" cy="{cy + 126}" r="12" fill="url(#glow)"/><circle cx="{cx + 300}" cy="{cy + 126}" r="3" fill="{HI}"/>
<g class="motion"><circle r="18" fill="url(#glow)"/><circle r="4.5" fill="{RED}"/><animateMotion dur="14s" repeatCount="indefinite" path="{orbit}"/></g>
</g>
{mark_svg}
<rect x="{div_x:.1f}" y="{cy - 70}" width="1" height="140" fill="{LINE}"/>
<rect x="{div_x - 1:.1f}" y="{cy - 70}" width="3" height="28" fill="{RED}"/>
<text class="name" x="{tx:.1f}" y="{cy - 14}">{esc(name)}</text>
<text class="role" x="{tx:.1f}" y="{cy + 30}">{esc(role)}</text>
<circle cx="{tx + 4:.1f}" cy="{cy + 63}" r="4" fill="{RED}"/>
<text class="site" x="{tx + 22:.1f}" y="{cy + 68}">{site}</text>
</g>
</svg>
'''


# --- Project cards ------------------------------------------------------------

def icon_symarket(x, y):
    """A phone holding five market rows, one of them lit."""
    rows = "".join(
        f'<rect x="{x + 52}" y="{y + 34 + i * 17}" width="{36 if i != 2 else 36}" height="9" rx="3" fill="{RED if i == 2 else "rgba(240,237,226,.28)"}"/>'
        for i in range(5))
    return (f'<rect x="{x + 40}" y="{y + 10}" width="60" height="120" rx="12" fill="none" stroke="rgba(240,237,226,.8)" stroke-width="2.5"/>'
            f'<rect x="{x + 62}" y="{y + 18}" width="16" height="3" rx="1.5" fill="rgba(240,237,226,.5)"/>{rows}')


def icon_dietly(x, y):
    """A plan ring in three parts with a leaf in the middle."""
    cx, cy, r = x + 70, y + 70, 52
    c = 2 * math.pi * r
    def arc(start, length, colour, width=10):
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colour}" stroke-width="{width}" '
                f'stroke-dasharray="{length * c:.1f} {c:.1f}" stroke-dashoffset="{-start * c:.1f}" transform="rotate(-90 {cx} {cy})" stroke-linecap="round"/>')
    leaf = (f'<path d="M {cx - 16} {cy + 14} C {cx - 18} {cy - 10} {cx + 2} {cy - 22} {cx + 18} {cy - 18} C {cx + 20} {cy + 4} {cx + 2} {cy + 18} {cx - 16} {cy + 14} Z" '
            f'fill="none" stroke="rgba(240,237,226,.85)" stroke-width="2.5"/>'
            f'<path d="M {cx - 16} {cy + 14} L {cx + 8} {cy - 8}" stroke="{RED}" stroke-width="2.5" stroke-linecap="round"/>')
    return arc(0.02, 0.42, RED) + arc(0.5, 0.26, "rgba(240,237,226,.8)") + arc(0.82, 0.14, "rgba(240,237,226,.3)") + leaf


def icon_muhassan(x, y):
    """A shield with a keyhole."""
    cx = x + 70
    shield = (f'M {cx} {y + 8} L {cx + 50} {y + 26} L {cx + 50} {y + 66} C {cx + 50} {y + 98} {cx + 26} {y + 122} {cx} {y + 132} '
              f'C {cx - 26} {y + 122} {cx - 50} {y + 98} {cx - 50} {y + 66} L {cx - 50} {y + 26} Z')
    return (f'<path d="{shield}" fill="rgba(71,12,23,.35)" stroke="rgba(240,237,226,.85)" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<circle cx="{cx}" cy="{y + 62}" r="11" fill="{RED}"/>'
            f'<path d="M {cx - 6} {y + 68} L {cx + 6} {y + 68} L {cx + 9} {y + 96} L {cx - 9} {y + 96} Z" fill="{RED}"/>')


def icon_nexus(x, y):
    """A radar: rings, cross-hairs, a turning sweep and three contacts."""
    cx, cy = x + 70, y + 70
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(240,237,226,{a})" stroke-width="1.5"/>'
                    for r, a in ((60, .35), (40, .25), (20, .2)))
    cross = (f'<path d="M {cx - 60} {cy} L {cx + 60} {cy} M {cx} {cy - 60} L {cx} {cy + 60}" stroke="rgba(240,237,226,.15)" stroke-width="1"/>')
    sweep = (f'<g class="spin" style="transform-origin:{cx}px {cy}px;animation:spin 6s linear infinite">'
             f'<path d="M {cx} {cy} L {cx + 60} {cy} A 60 60 0 0 0 {cx + 60 * math.cos(math.radians(-40)):.1f} {cy + 60 * math.sin(math.radians(-40)):.1f} Z" fill="url(#sweep)"/>'
             f'<path d="M {cx} {cy} L {cx + 60} {cy}" stroke="{RED}" stroke-width="2"/></g>')
    dots = (f'<circle cx="{cx + 26}" cy="{cy - 30}" r="4" fill="{HI}"/><circle cx="{cx - 34}" cy="{cy + 14}" r="3" fill="rgba(240,237,226,.8)"/>'
            f'<circle cx="{cx + 12}" cy="{cy + 40}" r="3" fill="rgba(240,237,226,.6)"/>')
    return rings + cross + sweep + dots


CARDS = [
    ("symarket", "CO-FOUNDER · LEAD ENGINEER", "SyMarket", ("A Syrian marketplace that brings", "five markets into one app."), ("React Native", "Next.js", "Supabase"), icon_symarket),
    ("dietly", "CO-FOUNDER", "Dietly", ("A platform for nutritionists:", "patients, meal plans, AI tools."), ("Next.js", "Flutter", "Supabase"), icon_dietly),
    ("muhassan", "PENTEST SERVICE", "Muhassan", ("Penetration testing and hardening", "before a platform goes live."), ("Pentest", "Hardening", "Reports"), icon_muhassan),
    ("nexus-rec", "OPEN SOURCE · PYPI", "Nexus-REC", ("Automated recon and vulnerability", "assessment framework."), ("Python", "OSINT", "Security"), icon_nexus),
]


def card(slug, kicker, title, desc, chips, icon):
    w, h, pad = 640, 300, 40
    chip_size, chip_pad, chip_gap = 17, 14, 10
    chip_svg, x = [], pad
    for chip in chips:
        cw = MONO.width(chip, chip_size, 500, 0.02) + 2 * chip_pad
        chip_svg.append(f'<rect x="{x:.1f}" y="222" width="{cw:.1f}" height="38" rx="19" fill="rgba(240,237,226,.04)" stroke="rgba(240,237,226,.18)"/>'
                        f'<text class="chip" x="{x + chip_pad:.1f}" y="247">{esc(chip)}</text>')
        x += cw + chip_gap
    fonts = SANS.css(title + "".join(desc)) + MONO.css(kicker + "".join(chips))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}: {esc(" ".join(desc))}">
<style>{fonts}
.kicker{{font:500 16px "Geist Mono",monospace;letter-spacing:.2em;fill:{HI}}}
.title{{font:700 44px "Geist",sans-serif;letter-spacing:-.035em;fill:#fff}}
.desc{{font:400 21px "Geist",sans-serif;letter-spacing:-.005em;fill:{W74}}}
.chip{{font:500 {chip_size}px "Geist Mono",monospace;letter-spacing:.02em;fill:{W74}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
{REDUCED}</style>
<defs>
<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CHAR}"/><stop offset="1" stop-color="{PANEL2}"/></linearGradient>
<radialGradient id="wine" cx="82%" cy="45%" r="45%"><stop offset="0" stop-color="{WINE}" stop-opacity=".55"/><stop offset="1" stop-color="{WINE}" stop-opacity="0"/></radialGradient>
<radialGradient id="sweep" cx="0" cy="0" r="1"><stop offset="0" stop-color="{RED}" stop-opacity=".05"/><stop offset="1" stop-color="{RED}" stop-opacity=".45"/></radialGradient>
</defs>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="url(#panel)" stroke="{LINE}"/>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="url(#wine)"/>
<rect x="{pad}" y="0.5" width="56" height="3" fill="{RED}"/>
<path d="M {w - 52} 40 L {w - 38} 26 M {w - 49} 26 L {w - 38} 26 L {w - 38} 37" fill="none" stroke="rgba(240,237,226,.45)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<text class="kicker" x="{pad}" y="62">{esc(kicker)}</text>
<text class="title" x="{pad}" y="118">{esc(title)}</text>
<text class="desc" x="{pad}" y="160">{esc(desc[0])}</text>
<text class="desc" x="{pad}" y="190">{esc(desc[1])}</text>
{"".join(chip_svg)}
{icon(w - 200, 72)}
</svg>
'''


def main():
    (OUT / "banner.svg").write_text(banner())
    for slug, *rest in CARDS:
        (OUT / f"card-{slug}.svg").write_text(card(slug, *rest))
    for p in sorted(OUT.glob("*.svg")):
        print(p.name, p.stat().st_size)


if __name__ == "__main__":
    main()
