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


DESIGNS = [  # slug, name, fn, garment, tagline
    ("hyperbolic-decline", "Hyperbolic Decline: My Motivation", d_hyperbolic, "hoodie"),
    ("b-equals-1", "b = 1.0", d_b1, "tee"),
    ("shut-in-not-shut-down", "Shut-In, Not Shut Down", d_shutin, "hoodie"),
    ("arps-was-right", "Arps Was Right", d_arps, "hoodie"),
    ("arps-equation", "The Arps Equation", d_equation, "tee"),
    ("leading-zeros-matter", "Leading Zeros Matter", d_zeros, "tee"),
    ("check-the-units", "Check the Units", d_units, "tee"),
    ("gas-has-a-season", "Gas Has a Season", d_season, "tee"),
    ("wells-dont-retire", "Wells Don't Retire. They Decline.", d_retire, "hoodie"),
    ("bounded-optimism", "Bounded Fit. Bounded Optimism.", d_bounded, "tee"),
    ("p50-energy", "P50 Energy", d_p50, "tee"),
    ("licensed-not-producing", "Licensed ≠ Producing", d_licensed, "tee"),
]
STICKERS = ["hyperbolic-decline", "b-equals-1", "shut-in-not-shut-down", "arps-was-right", "leading-zeros-matter", "check-the-units"]
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


def mockup_back(slug, kind, gcolor):
    c = INKS["light"]
    fn = [d for d in DESIGNS if d[0] == slug][0][2]
    y = 225 if kind == "tee" else 345
    h = 430 if kind == "tee" else 420
    w = h * 0.75
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 900" width="900" height="900">'
            '<defs><radialGradient id="bg" cx=".5" cy=".42" r=".75"><stop offset="0" stop-color="#f4f6fb"/><stop offset="1" stop-color="#d9deea"/></radialGradient></defs>'
            '<rect width="900" height="900" fill="url(#bg)"/><ellipse cx="450" cy="830" rx="300" ry="26" fill="#000" fill-opacity=".10"/>'
            + garment_back(kind, GARMENT_COLORS[gcolor]) +
            f'<svg x="{450 - w / 2:.0f}" y="{y}" width="{w:.0f}" height="{h}" viewBox="0 0 1200 1600">{fn(c)}</svg>'
            '<text x="450" y="868" font-family="Inter,sans-serif" font-size="22" font-weight="600" fill="#6a7390" text-anchor="middle" letter-spacing="4">BACK PRINT</text></svg>')


def mockup_front(slug, kind, gcolor):
    c = INKS["light"]
    cy = 232 if kind == "tee" else 352
    logo = chest_logo_svg(c).replace('width="1200" height="600"', f'x="520" y="{cy}" width="112" height="56"')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="100 70 700 700" width="900" height="900">'
            '<defs><radialGradient id="bg" cx=".5" cy=".42" r=".75"><stop offset="0" stop-color="#f4f6fb"/><stop offset="1" stop-color="#d9deea"/></radialGradient></defs>'
            '<rect x="0" y="0" width="900" height="900" fill="url(#bg)"/>' + garment(kind, GARMENT_COLORS[gcolor]) + logo +
            '</svg>')


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
        gc = "black" if slug not in ("arps-was-right", "gas-has-a-season") else "navy"
        (out / "svg" / f"mockup-{slug}.svg").write_text(mockup_back(slug, kind, gc), encoding="utf-8")
        jobs.append({"src": f"svg/mockup-{slug}.svg", "out": f"web/mockup-{slug}.jpg", "w": 720, "h": 720, "scale": 1, "type": "jpeg", "quality": 88})
        (out / "svg" / f"mockup-{slug}-front.svg").write_text(mockup_front(slug, kind, gc), encoding="utf-8")
        jobs.append({"src": f"svg/mockup-{slug}-front.svg", "out": f"web/mockup-{slug}-front.jpg", "w": 720, "h": 720, "scale": 1, "type": "jpeg", "quality": 88})
        BRAND_ON = True
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
