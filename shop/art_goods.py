"""Apparel, sticker and notebook artwork (typographic, no company names or logos) plus garment mockups.
Run: python3 shop/art_goods.py OUTDIR  (after art.py)  -> OUTDIR/svg/*.svg and OUTDIR/manifest.json for shop/render.js"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from art import MONO, SANS, SERIF, SYMBOL, esc, text  # noqa: E402

INKS = {
    "light": dict(ink="#f4f7ff", accent="#4da8ff", muted="#9fb0d6", name="Light ink (for dark garments)"),
    "dark": dict(ink="#111a33", accent="#0a58ca", muted="#51597a", name="Dark ink (for light garments)"),
}
SUB = '<tspan baseline-shift="sub" font-size="0.6em">i</tspan>'
SUP = lambda s: f'<tspan baseline-shift="super" font-size="0.6em">{s}</tspan>'


def curve(cx, y, w, h, c, b=1.0, di=1.6, sw=14):
    """Small decline-curve glyph with axes, centred on cx, top at y."""
    x0 = cx - w / 2
    pts = []
    for k in range(0, 61):
        tt = k / 60 * 3.0
        q = math.exp(-di * tt) if b == 0 else (1 + b * di * tt) ** (-1 / b)
        pts.append(f"{x0 + w * k / 60:.1f},{y + h - h * q:.1f}")
    return (f'<line x1="{x0}" y1="{y}" x2="{x0}" y2="{y + h}" stroke="{c["muted"]}" stroke-width="6" stroke-linecap="round"/>'
            f'<line x1="{x0}" y1="{y + h}" x2="{x0 + w}" y2="{y + h}" stroke="{c["muted"]}" stroke-width="6" stroke-linecap="round"/>'
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{c["accent"]}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')


def wheel(cx, cy, r, c):
    o = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["accent"]}" stroke-width="22"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{r * 0.16:.1f}" fill="{c["ink"]}"/>']
    for k in range(6):
        a = k * math.pi / 3
        o.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + r * math.cos(a):.1f}" y2="{cy + r * math.sin(a):.1f}" stroke="{c["ink"]}" stroke-width="16" stroke-linecap="round"/>')
    return "".join(o)


def wave(cx, y, w, h, c):
    pts = " ".join(f"{cx - w / 2 + w * k / 80:.1f},{y + h / 2 - h / 2 * math.sin(k / 80 * 2 * math.pi - math.pi / 2):.1f}" for k in range(81))
    return f'<polyline points="{pts}" fill="none" stroke="{c["accent"]}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>'


def stack(lines, y, c, gap=1.08):
    """lines: (text, size, weight, family, colour key, spacing). Returns svg and the y after the last line."""
    o = []
    for s, size, w, fam, ck, sp in lines:
        y += size * 0.86
        o.append(text(600, y, s, size, c[ck], fam, w, anchor="middle", spacing=sp))
        y += size * (gap - 0.86)
    return "".join(o), y


def design_svg(inner):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1600" width="1200" height="1600">{inner}</svg>'


BRAND_ON = True  # sticker art carries the url; apparel carries a chest logo instead


def brand(c):
    if not BRAND_ON:
        return ""
    return text(600, 1490, "tidywells.com", 34, c["muted"], SANS, 600, anchor="middle", spacing=6)


def d_hyperbolic(c):
    a, y = stack([("HYPERBOLIC", 158, 800, SANS, "ink", 2), ("DECLINE", 158, 800, SANS, "ink", 8)], 330, c)
    return a + curve(600, y + 40, 640, 260, c, 1.0) + text(600, y + 470, "my motivation", 100, c["accent"], SERIF, 600, anchor="middle", style="italic") + brand(c)


def d_b1(c):
    return (text(600, 700, "b = 1.0", 270, c["ink"], MONO, 700, anchor="middle") +
            text(600, 800, "HARMONIC DECLINE", 66, c["muted"], SANS, 700, anchor="middle", spacing=14) +
            curve(600, 880, 640, 320, c, 1.0) + brand(c))


def d_shutin(c):
    a, y = stack([("SHUT-IN,", 170, 800, SANS, "ink", 4), ("NOT SHUT", 148, 800, SANS, "accent", 2), ("DOWN.", 148, 800, SANS, "accent", 14)], 640, c)
    return wheel(600, 400, 170, c) + a + brand(c)


def d_arps(c):
    return (text(600, 640, "ARPS", 320, c["ink"], SANS, 800, anchor="middle", spacing=6) +
            text(600, 840, "WAS RIGHT.", 164, c["accent"], SANS, 800, anchor="middle", spacing=2) +
            text(600, 980, f"q = q{SUB} / (1 + b·D{SUB}·t){SUP('1/b')}", 54, c["muted"], MONO, 500, anchor="middle") + brand(c))


def d_equation(c):
    return (text(250, 700, "q(t) =", 130, c["ink"], SERIF, 600, style="italic") +
            text(870, 650, f"q{SUB}", 150, c["ink"], SERIF, 600, anchor="middle", style="italic") +
            f'<line x1="520" y1="690" x2="1130" y2="690" stroke="{c["accent"]}" stroke-width="12" stroke-linecap="round"/>' +
            text(825, 840, f"(1 + b·D{SUB}·t){SUP('1/b')}", 92, c["ink"], SERIF, 600, anchor="middle", style="italic") +
            text(600, 1060, "J.J. ARPS · 1945", 56, c["accent"], SANS, 700, anchor="middle", spacing=14) +
            text(600, 1130, "still the best argument in the oil patch", 46, c["muted"], SERIF, 400, anchor="middle", style="italic") + brand(c))


def d_zeros(c):
    a, y = stack([("LEADING", 190, 800, SANS, "ink", 2), ("ZEROS", 190, 800, SANS, "ink", 8), ("MATTER.", 190, 800, SANS, "accent", 2)], 420, c)
    return text(600, 330, "0001234", 150, c["muted"], MONO, 700, anchor="middle", extra='opacity="0.35"') + a + text(600, y + 60, "WELL ID 0001234 ≠ 1234", 46, c["muted"], SYMBOL, 600, anchor="middle", spacing=6) + brand(c)


def d_units(c):
    a, y = stack([("CHECK", 220, 800, SANS, "ink", 4), ("THE", 220, 800, SANS, "ink", 40), ("UNITS.", 220, 800, SANS, "accent", 4)], 340, c)
    return a + text(600, y + 90, "m³ · Mcf · MMcf · boe", 62, c["muted"], MONO, 500, anchor="middle") + brand(c)


def d_season(c):
    a, y = stack([("GAS HAS", 200, 800, SANS, "ink", 4), ("A SEASON.", 190, 800, SANS, "accent", 0)], 380, c)
    return a + wave(600, y + 80, 760, 240, c) + text(600, y + 470, "J F M A M J J A S O N D", 52, c["muted"], MONO, 500, anchor="middle", spacing=8) + brand(c)


def d_retire(c):
    a, y = stack([("WELLS DON'T", 150, 800, SANS, "ink", 2), ("RETIRE.", 190, 800, SANS, "accent", 6), ("THEY DECLINE.", 112, 800, SANS, "ink", 4)], 330, c)
    return a + curve(600, y + 60, 640, 260, c, 0.6) + brand(c)


def d_bounded(c):
    a, y = stack([("BOUNDED FIT.", 150, 800, SANS, "ink", 2), ("BOUNDED", 190, 800, SANS, "accent", 4), ("OPTIMISM.", 190, 800, SANS, "accent", 4)], 380, c)
    return a + text(600, y + 100, "0 ≤ b ≤ 2", 96, c["muted"], SYMBOL, 600, anchor="middle") + brand(c)


def d_p50(c):
    return (text(600, 760, "P50", 440, c["ink"], MONO, 700, anchor="middle") +
            text(600, 940, "ENERGY", 190, c["accent"], SANS, 800, anchor="middle", spacing=14) +
            text(600, 1060, "not optimistic. not pessimistic. just the median.", 40, c["muted"], SERIF, 400, anchor="middle", style="italic") + brand(c))


def d_licensed(c):
    return (text(600, 560, "LICENSED", 200, c["ink"], SANS, 800, anchor="middle", spacing=2) +
            text(600, 860, "≠", 340, c["accent"], SYMBOL, 700, anchor="middle") +
            text(600, 1060, "PRODUCING", 200, c["ink"], SANS, 800, anchor="middle", spacing=2) +
            text(600, 1160, "a licence is not a production report.", 46, c["muted"], SERIF, 400, anchor="middle", style="italic") + brand(c))


def bold(lines, acc, c, size_cap=250):
    """Clean stacked slogan: heavy Inter caps, one accent line, thin rule. Fits a 1000px box."""
    n = len(lines)
    size = min(size_cap, 1000 / (0.64 * max(len(l) for l in lines)), 900 / (n * 1.0))
    y = 700 - size * n / 2 + size * 0.80
    o = []
    for i, l in enumerate(lines):
        o.append(text(600, y + i * size, l.replace("'", "&#39;"), round(size), c["accent"] if i == acc else c["ink"], SANS, 800, anchor="middle", spacing=-round(size * 0.01)))
    ry = y + (n - 1) * size + size * 0.40
    o.append(f'<line x1="470" y1="{ry:.0f}" x2="730" y2="{ry:.0f}" stroke="{c["muted"]}" stroke-width="6" stroke-linecap="round"/>')
    return "".join(o)


def d_pipeline(c):
    return bold(["BUILD", "THE", "PIPELINE"], 2, c) + brand(c)


def d_tanker(c):
    return bold(["SCRAP", "THE", "TANKER", "BAN"], 3, c) + brand(c)


def d_ottawa(c):
    return bold(["OTTAWA", "DOESN'T", "PUMP", "OIL."], 3, c) + brand(c)


def d_quiet(c):
    return bold(["PIPELINE", "OR QUIET.", "PICK ONE."], 2, c) + brand(c)


def d_money(c):
    return bold(["POWERED", "BY OIL", "MONEY."], 2, c) + brand(c)


def d_camp(c):
    return bold(["CAMP", "LIFE."], 1, c) + brand(c)


def d_darcy(c):
    return (text(600, 500, "DARCY&#39;S LAW", 120, c["ink"], SANS, 800, anchor="middle", spacing=8) +
            text(330, 800, "q =", 150, c["ink"], SERIF, 600, style="italic") +
            text(830, 725, "k · A · ΔP", 130, c["ink"], SERIF, 600, anchor="middle", style="italic") +
            f'<line x1="520" y1="790" x2="1140" y2="790" stroke="{c["accent"]}" stroke-width="12" stroke-linecap="round"/>' +
            text(830, 925, "μ · L", 130, c["ink"], SERIF, 600, anchor="middle", style="italic") +
            text(600, 1100, "HOW FLUID MOVES THROUGH ROCK", 46, c["accent"], SANS, 700, anchor="middle", spacing=10) +
            text(600, 1170, "H. Darcy · 1856", 44, c["muted"], SERIF, 400, anchor="middle", style="italic") + brand(c))


def d_gaslaw(c):
    return (text(600, 700, "pV = znRT", 230, c["ink"], SERIF, 600, anchor="middle", style="italic") +
            text(600, 860, "THE REAL GAS LAW", 70, c["accent"], SANS, 800, anchor="middle", spacing=12) +
            text(600, 960, "z is the part the textbook leaves out", 50, c["muted"], SERIF, 400, anchor="middle", style="italic") + brand(c))


DESIGNS = [  # slug, name, fn, garment
    ("build-the-pipeline", "Build the Pipeline", d_pipeline, "hoodie"),
    ("ottawa-doesnt-pump-oil", "Ottawa Doesn't Pump Oil", d_ottawa, "hoodie"),
    ("shut-in-not-shut-down", "Shut-In, Not Shut Down", d_shutin, "hoodie"),
    ("hyperbolic-decline", "Hyperbolic Decline: My Motivation", d_hyperbolic, "hoodie"),
    ("arps-was-right", "Arps Was Right", d_arps, "hoodie"),
    ("powered-by-oil-money", "Powered by Oil Money", d_money, "tee"),
    ("scrap-the-tanker-ban", "Scrap the Tanker Ban", d_tanker, "tee"),
    ("pipeline-or-quiet", "Pipeline or Quiet. Pick One.", d_quiet, "tee"),
    ("camp-life", "Camp Life", d_camp, "tee"),
    ("darcys-law", "Darcy's Law", d_darcy, "tee"),
    ("pv-znrt", "pV = znRT", d_gaslaw, "tee"),
    ("check-the-units", "Check the Units", d_units, "tee"),
]
STICKER_SLUGS = ["build-the-pipeline", "scrap-the-tanker-ban", "ottawa-doesnt-pump-oil", "pipeline-or-quiet", "powered-by-oil-money", "shut-in-not-shut-down", "hyperbolic-decline", "camp-life", "darcys-law", "pv-znrt"]
MUG_SLUGS = ["build-the-pipeline", "ottawa-doesnt-pump-oil", "powered-by-oil-money", "hyperbolic-decline", "check-the-units"]
HATS = [("build-the-pipeline", ["BUILD THE", "PIPELINE"]), ("ottawa-doesnt-pump-oil", ["OTTAWA DOESN'T", "PUMP OIL."])]
TOQUES = [("build-the-pipeline", ["BUILD THE PIPELINE"]), ("camp-life", ["CAMP LIFE."]), ("powered-by-oil-money", ["POWERED BY", "OIL MONEY."])]
STICKERS = STICKER_SLUGS
GARMENT_COLORS = {"black": "#17191f", "navy": "#16233f", "sand": "#d9cfba", "white": "#f1f1ee", "heather": "#9ca2ab"}


def garment(kind, color):
    shade = '<linearGradient id="sh" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".10"/><stop offset="1" stop-color="#000" stop-opacity=".16"/></linearGradient>'
    if kind == "tee":
        body = "M 300 150 L 380 128 Q 450 196 520 128 L 600 150 L 770 236 L 706 350 L 646 318 L 646 790 L 254 790 L 254 318 L 194 350 L 130 236 Z"
        extra = f'<path d="M 380 128 Q 450 196 520 128" fill="none" stroke="#000" stroke-opacity=".25" stroke-width="10"/>'
    else:
        body = "M 296 196 L 378 172 Q 450 250 522 172 L 604 196 L 780 330 L 730 650 L 650 626 L 650 806 L 250 806 L 250 626 L 170 650 L 120 330 Z"
        extra = (f'<path d="M 330 176 Q 450 30 570 176 L 540 236 Q 450 300 360 236 Z" fill="{color}"/>'
                 '<path d="M 330 176 Q 450 30 570 176 L 540 236 Q 450 300 360 236 Z" fill="url(#sh)"/>'
                 '<path d="M 372 238 Q 450 296 528 238" fill="none" stroke="#000" stroke-opacity=".3" stroke-width="10"/>'
                 '<line x1="418" y1="280" x2="410" y2="400" stroke="#e8e8e8" stroke-width="8" stroke-linecap="round"/>'
                 '<line x1="482" y1="280" x2="490" y2="400" stroke="#e8e8e8" stroke-width="8" stroke-linecap="round"/>'
                 '<path d="M 330 650 L 570 650 L 600 770 L 300 770 Z" fill="#000" fill-opacity=".14"/>')
    return f'<defs>{shade}</defs><path d="{body}" fill="{color}"/><path d="{body}" fill="url(#sh)"/>{extra}'


def chest_logo_svg(c):
    """Small left-chest mark: decline-curve glyph + serif wordmark, 1200x600 (4 x 2 inch at 300 dpi)."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 600" width="1200" height="600">'
            + curve(215, 170, 270, 260, c, 1.0, 1.6, 20) + text(420, 365, "Tidywells", 170, c["ink"], SERIF, 600) + '</svg>')


def garment_back(kind, color):
    shade = '<linearGradient id="sh" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".10"/><stop offset="1" stop-color="#000" stop-opacity=".16"/></linearGradient>'
    if kind == "tee":
        body = "M 300 150 L 380 132 Q 450 150 520 132 L 600 150 L 770 236 L 706 350 L 646 318 L 646 790 L 254 790 L 254 318 L 194 350 L 130 236 Z"
        extra = '<path d="M 380 132 Q 450 150 520 132" fill="none" stroke="#000" stroke-opacity=".25" stroke-width="10"/>'
    else:
        body = "M 296 196 L 378 172 Q 450 190 522 172 L 604 196 L 780 330 L 730 650 L 650 626 L 650 806 L 250 806 L 250 626 L 170 650 L 120 330 Z"
        extra = (f'<path d="M 330 176 Q 450 150 570 176 L 585 300 Q 450 360 315 300 Z" fill="{color}"/>'
                 '<path d="M 330 176 Q 450 150 570 176 L 585 300 Q 450 360 315 300 Z" fill="url(#sh)"/>'
                 '<path d="M 316 300 Q 450 360 584 300" fill="none" stroke="#000" stroke-opacity=".3" stroke-width="9"/>')
    return f'<defs>{shade}</defs><path d="{body}" fill="{color}"/><path d="{body}" fill="url(#sh)"/>{extra}'


def _frame(inner):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 900" width="900" height="900">'
            '<defs><radialGradient id="bg" cx=".5" cy=".42" r=".75"><stop offset="0" stop-color="#f4f6fb"/><stop offset="1" stop-color="#d9deea"/></radialGradient></defs>'
            '<rect width="900" height="900" fill="url(#bg)"/>' + inner + '</svg>')


def _front_g(kind, gcolor):
    c = INKS["light"]
    cy = 226 if kind == "tee" else 340
    logo = chest_logo_svg(c).replace('width="1200" height="600"', f'x="522" y="{cy}" width="92" height="46"')
    return garment(kind, GARMENT_COLORS[gcolor]) + logo


def _back_g(slug, kind, gcolor):
    c = INKS["light"]
    fn = [d for d in DESIGNS if d[0] == slug][0][2]
    y = 225 if kind == "tee" else 345
    h = 430 if kind == "tee" else 420
    w = h * 0.75
    return garment_back(kind, GARMENT_COLORS[gcolor]) + f'<svg x="{450 - w / 2:.0f}" y="{y}" width="{w:.0f}" height="{h}" viewBox="0 0 1200 1600">{fn(c)}</svg>'


def _label(x, text_, y=868):
    return f'<text x="{x}" y="{y}" font-family="Inter,sans-serif" font-size="22" font-weight="600" fill="#6a7390" text-anchor="middle" letter-spacing="4">{text_}</text>'


def mockup_front(slug, kind, gcolor):
    return _frame('<ellipse cx="450" cy="830" rx="300" ry="26" fill="#000" fill-opacity=".10"/>' + _front_g(kind, gcolor) + _label(450, "FRONT"))


def mockup_back(slug, kind, gcolor):
    return _frame('<ellipse cx="450" cy="830" rx="300" ry="26" fill="#000" fill-opacity=".10"/>' + _back_g(slug, kind, gcolor) + _label(450, "BACK PRINT"))


def mockup_both(slug, kind, gcolor):
    sc = 0.58
    L = f'<g transform="translate({25 - 120 * sc:.1f},{450 - 418 * sc:.1f}) scale({sc})">{_front_g(kind, gcolor)}</g>'
    R = f'<g transform="translate({470 - 120 * sc:.1f},{450 - 418 * sc:.1f}) scale({sc})">{_back_g(slug, kind, gcolor)}</g>'
    return _frame(L + R + _label(216, "FRONT", 790) + _label(661, "BACK PRINT", 790))


def _fn(slug):
    return [d for d in DESIGNS if d[0] == slug][0][2]


def mug_art(slug, ink):
    """11 oz mug wrap, 2475 x 1155: the portrait design centred."""
    c = INKS[ink]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2475 1155" width="2475" height="1155">'
            f'<svg x="{(2475 - 866) / 2:.0f}" y="0" width="866" height="1155" viewBox="0 0 1200 1600">{_fn(slug)(c)}</svg></svg>')


def mug_mockup(slug):
    c = INKS["light"]
    d = ('<defs><linearGradient id="mg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2a2d35"/><stop offset=".45" stop-color="#1b1d23"/><stop offset="1" stop-color="#0f1013"/></linearGradient></defs>')
    body = ('<ellipse cx="430" cy="800" rx="230" ry="26" fill="#000" fill-opacity=".12"/>'
            '<path d="M 600 330 C 720 330 720 560 600 560" fill="none" stroke="#17191f" stroke-width="40" stroke-linecap="round"/>'
            '<path d="M 262 270 L 262 740 Q 262 790 430 790 Q 598 790 598 740 L 598 270 Z" fill="url(#mg)"/>'
            '<ellipse cx="430" cy="270" rx="168" ry="30" fill="#2f333c"/><ellipse cx="430" cy="270" rx="150" ry="22" fill="#0b0c0e"/>')
    art = f'<svg x="320" y="330" width="220" height="293" viewBox="0 0 1200 1600">{_fn(slug)(c)}</svg>'
    return _frame(d + body + art + _label(450, "11 OZ MUG, WRAP PRINT"))


def hat_art(lines):
    n = len(lines)
    size = min(230, 1250 / (0.62 * max(len(l) for l in lines)))
    y0 = 300 - size * n / 2 + size * 0.80
    t = "".join(text(675, y0 + i * size * 1.02, l.replace("'", "&#39;"), round(size), "#ffffff", SANS, 800, anchor="middle", spacing=-3) for i, l in enumerate(lines))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1350 600" width="1350" height="600">{t}</svg>'


def hat_mockup(lines, color="#17191f"):
    """Three-quarter view of a curved-brim cap: crown, front panel with embroidery, brim projecting forward-left."""
    fs = min(44, 236 / (0.62 * max(len(l) for l in lines)))
    t = "".join(text(0, k * fs * 1.18, l.replace("'", "&#39;"), round(fs, 1), "#ffffff", SANS, 800, anchor="middle", spacing=-1) for k, l in enumerate(lines))
    defs = ('<defs><linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".14"/><stop offset="1" stop-color="#000" stop-opacity=".25"/></linearGradient></defs>')
    crown = ('<path d="M 262 520 C 236 330 330 190 500 188 C 650 186 736 300 730 470 C 728 520 726 540 720 556 C 600 600 400 596 262 520 Z"')
    brim = ('<path d="M 262 520 C 190 556 120 604 112 650 C 108 676 150 690 230 678 C 360 660 480 626 612 590 C 500 586 380 566 262 520 Z"')
    pieces = (f'{crown} fill="{color}"/>{crown} fill="url(#cg)"/>'
              '<path d="M 500 190 C 470 300 480 420 520 590" fill="none" stroke="#000" stroke-opacity=".25" stroke-width="5"/>'
              '<circle cx="500" cy="188" r="13" fill="#101216"/>'
              f'{brim} fill="{color}"/>{brim} fill="url(#cg)"/>'
              '<path d="M 262 520 C 380 566 500 586 612 590" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="7"/>'
              f'<g transform="translate(410,360) skewY(-5) rotate(-4)">{t.replace("<text ", "<text transform=\"scale(.95,1)\" ")}</g>')
    return _frame(defs + '<ellipse cx="440" cy="710" rx="290" ry="22" fill="#000" fill-opacity=".10"/>' + pieces + _label(450, "EMBROIDERED HAT"))


def toque_art(lines):
    n = len(lines)
    size = min(190, 1000 / (0.62 * max(len(l) for l in lines)))
    y0 = 225 - size * n / 2 + size * 0.80
    t = "".join(text(525, y0 + i * size * 1.02, l.replace("'", "&#39;"), round(size), "#ffffff", SANS, 800, anchor="middle", spacing=-2) for i, l in enumerate(lines))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1050 450" width="1050" height="450">{t}</svg>'


def toque_mockup(lines, color="#17191f"):
    inner = toque_art(lines).split(">", 1)[1].rsplit("</svg>", 1)[0]
    ribs = "".join(f'<line x1="{x}" y1="330" x2="{x + (x - 450) * 0.04:.0f}" y2="470" stroke="#000" stroke-opacity=".16" stroke-width="4"/>' for x in range(280, 630, 24))
    defs = '<defs><linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".12"/><stop offset="1" stop-color="#000" stop-opacity=".22"/></linearGradient></defs>'
    body = f'<path d="M 232 500 C 206 270 330 150 450 150 C 570 150 694 270 668 500 Z" fill="{color}"/><path d="M 232 500 C 206 270 330 150 450 150 C 570 150 694 270 668 500 Z" fill="url(#cg)"/>'
    cuff = f'<rect x="212" y="450" width="476" height="190" rx="34" fill="{color}"/><rect x="212" y="450" width="476" height="190" rx="34" fill="url(#cg)"/>'
    cuff += '<rect x="212" y="450" width="476" height="190" rx="34" fill="none" stroke="#000" stroke-opacity=".3" stroke-width="5"/>'
    txt = f'<svg x="300" y="478" width="300" height="129" viewBox="0 0 1050 450">{inner}</svg>'
    return _frame(defs + '<ellipse cx="450" cy="690" rx="260" ry="22" fill="#000" fill-opacity=".10"/>' + body + ribs + cuff + txt + _label(450, "CUFFED TOQUE, EMBROIDERED"))


def mockup(slug, kind, gcolor, light_ink):
    c = INKS["light" if light_ink else "dark"]
    fn = [d for d in DESIGNS if d[0] == slug][0][2]
    inner = fn(c)
    y = 270 if kind == "tee" else 330
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 900" width="900" height="900">'
            '<defs><radialGradient id="bg" cx=".5" cy=".42" r=".75"><stop offset="0" stop-color="#f4f6fb"/><stop offset="1" stop-color="#d9deea"/></radialGradient></defs>'
            '<rect width="900" height="900" fill="url(#bg)"/><ellipse cx="450" cy="830" rx="300" ry="26" fill="#000" fill-opacity=".10"/>'
            + garment(kind, GARMENT_COLORS[gcolor]) +
            f'<svg x="290" y="{y}" width="320" height="427" viewBox="0 0 1200 1600">{inner}</svg></svg>')


def sticker_svg(slug):
    c = INKS["light"]
    fn = [d for d in DESIGNS if d[0] == slug][0][2]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1200" width="1200" height="1200">'
            '<rect x="30" y="30" width="1140" height="1140" rx="190" fill="#ffffff"/>'
            '<rect x="78" y="78" width="1044" height="1044" rx="150" fill="#101a31"/>'
            f'<svg x="228" y="110" width="744" height="992" viewBox="0 0 1200 1600">{fn(c)}</svg></svg>')


def cover_svg(kind):
    W, H = 1650, 2550
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#101a31"/>']
    for k in range(1, 26):
        o.append(f'<line x1="0" y1="{k * 100}" x2="{W}" y2="{k * 100}" stroke="#1d2a4a" stroke-width="2"/>')
    for k in range(1, 17):
        o.append(f'<line x1="{k * 100}" y1="0" x2="{k * 100}" y2="{H}" stroke="#1d2a4a" stroke-width="2"/>')
    c = INKS["light"]
    if kind == "decline-log":
        o.append(text(825, 560, "DECLINE", 230, c["ink"], SANS, 800, anchor="middle", spacing=6))
        o.append(text(825, 780, "LOG", 230, c["accent"], SANS, 800, anchor="middle", spacing=40))
        o.append(curve(825, 1000, 1000, 640, c, 1.0, sw=20))
        o.append(text(825, 1900, "WELL ____________________", 60, c["muted"], MONO, 500, anchor="middle"))
        o.append(text(825, 2010, "STARTED ________________", 60, c["muted"], MONO, 500, anchor="middle"))
    else:
        o.append(text(825, 520, "WELL FILE", 230, c["ink"], SANS, 800, anchor="middle", spacing=4))
        o.append(text(825, 680, "notes, numbers, nonsense", 80, c["accent"], SERIF, 600, anchor="middle", style="italic"))
        o.append(wheel(825, 1250, 330, c))
        o.append(text(825, 2000, "OWNER ___________________", 60, c["muted"], MONO, 500, anchor="middle"))
    o.append(text(825, 2400, "tidywells.com", 50, c["muted"], SANS, 600, anchor="middle", spacing=8))
    return "".join(o) + "</svg>"


def main(out):
    (out / "svg").mkdir(parents=True, exist_ok=True)
    jobs = []
    global BRAND_ON
    for ink in ("light", "dark"):
        (out / "svg" / f"chest-logo-{ink}.svg").write_text(chest_logo_svg(INKS[ink]), encoding="utf-8")
        jobs.append({"src": f"svg/chest-logo-{ink}.svg", "out": f"print/apparel/tidywells-chest-logo-{ink}-ink-1200x600.png", "w": 1200, "h": 600, "scale": 1, "type": "png", "transparent": True})
    for slug, name, fn, kind in DESIGNS:
        BRAND_ON = False
        for ink in ("light", "dark"):
            svg = design_svg(fn(INKS[ink]))
            (out / "svg" / f"apparel-{slug}-{ink}.svg").write_text(svg, encoding="utf-8")
            jobs.append({"src": f"svg/apparel-{slug}-{ink}.svg", "out": f"print/apparel/{slug}-{ink}-ink-3600x4800.png", "w": 1200, "h": 1600, "scale": 3, "type": "png", "transparent": True})
        gc = "navy" if slug in ("arps-was-right", "build-the-pipeline") else "black"
        for suffix, fn_ in (("", mockup_both), ("-back", mockup_back), ("-front", mockup_front)):
            (out / "svg" / f"mockup-{slug}{suffix}.svg").write_text(fn_(slug, kind, gc), encoding="utf-8")
            jobs.append({"src": f"svg/mockup-{slug}{suffix}.svg", "out": f"web/mockup-{slug}{suffix}.jpg", "w": 720, "h": 720, "scale": 1, "type": "jpeg", "quality": 88})
        BRAND_ON = True
    for slug in MUG_SLUGS:
        for ink, nm in (("light", "black-mug"), ("dark", "white-mug")):
            (out / "svg" / f"mug-{slug}-{ink}.svg").write_text(mug_art(slug, ink), encoding="utf-8")
            jobs.append({"src": f"svg/mug-{slug}-{ink}.svg", "out": f"print/mugs/{slug}-{nm}-2475x1155.png", "w": 2475, "h": 1155, "scale": 1, "type": "png", "transparent": True})
        (out / "svg" / f"mug-{slug}-mock.svg").write_text(mug_mockup(slug), encoding="utf-8")
        jobs.append({"src": f"svg/mug-{slug}-mock.svg", "out": f"web/mug-{slug}.jpg", "w": 720, "h": 720, "scale": 1, "type": "jpeg", "quality": 88})
    for slug, lines in HATS:
        (out / "svg" / f"hat-{slug}.svg").write_text(hat_art(lines), encoding="utf-8")
        jobs.append({"src": f"svg/hat-{slug}.svg", "out": f"print/hats/{slug}-embroidery-1350x600.png", "w": 1350, "h": 600, "scale": 1, "type": "png", "transparent": True})
        (out / "svg" / f"hat-{slug}-mock.svg").write_text(hat_mockup(lines), encoding="utf-8")
        jobs.append({"src": f"svg/hat-{slug}-mock.svg", "out": f"web/hat-{slug}.jpg", "w": 720, "h": 720, "scale": 1, "type": "jpeg", "quality": 88})
    for slug, lines in TOQUES:
        (out / "svg" / f"toque-{slug}.svg").write_text(toque_art(lines), encoding="utf-8")
        jobs.append({"src": f"svg/toque-{slug}.svg", "out": f"print/toques/{slug}-embroidery-1050x450.png", "w": 1050, "h": 450, "scale": 1, "type": "png", "transparent": True})
        (out / "svg" / f"toque-{slug}-mock.svg").write_text(toque_mockup(lines), encoding="utf-8")
        jobs.append({"src": f"svg/toque-{slug}-mock.svg", "out": f"web/toque-{slug}.jpg", "w": 720, "h": 720, "scale": 1, "type": "jpeg", "quality": 88})
    for slug in STICKERS:
        (out / "svg" / f"sticker-{slug}.svg").write_text(sticker_svg(slug), encoding="utf-8")
        jobs.append({"src": f"svg/sticker-{slug}.svg", "out": f"print/stickers/{slug}-1200x1200.png", "w": 1200, "h": 1200, "scale": 1, "type": "png", "transparent": True})
        jobs.append({"src": f"svg/sticker-{slug}.svg", "out": f"web/sticker-{slug}.png", "w": 600, "h": 600, "scale": 1, "type": "png", "transparent": True})
    for kind in ("decline-log", "well-file"):
        (out / "svg" / f"cover-{kind}.svg").write_text(cover_svg(kind), encoding="utf-8")
        jobs.append({"src": f"svg/cover-{kind}.svg", "out": f"print/notebooks/{kind}-1650x2550.png", "w": 1650, "h": 2550, "scale": 1, "type": "png"})
        jobs.append({"src": f"svg/cover-{kind}.svg", "out": f"web/cover-{kind}.jpg", "w": 600, "h": 928, "scale": 1, "type": "jpeg", "quality": 86})
    # posters (from art.py output already in out/svg)
    for p in sorted((out / "svg").glob("poster-*.svg")):
        n = p.stem
        jobs.append({"src": f"svg/{n}.svg", "out": f"print/posters/{n}-18x24in-5400x7200.png", "w": 1800, "h": 2400, "scale": 3, "type": "png"})
        jobs.append({"src": f"svg/{n}.svg", "out": f"web/{n}.jpg", "w": 720, "h": 960, "scale": 1, "type": "jpeg", "quality": 86})
    json.dump(jobs, open(out / "manifest.json", "w"), indent=0)
    print("jobs", len(jobs))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
