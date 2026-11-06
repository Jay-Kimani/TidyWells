"""Tidywells shop artwork, generated as SVG from the open dataset (posters) or from text (apparel, stickers, covers).

Posters are computed from docs/data/tidywells-monthly-production.csv, so every number printed on one can be checked against the
open data. Run:  python3 shop/art.py OUTDIR   then rasterise with  node shop/render.js OUTDIR PRINTDIR PREVIEWDIR
Stdlib only. Fonts (SIL OFL): Fraunces, Inter, IBM Plex Mono; render.js loads them from @fontsource packages.
"""
import csv
import math
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "docs" / "data" / "tidywells-monthly-production.csv"
CONV = {"OIL": 6.2898 / 1000, "GAS": 35.3147 / 1000}
UNIT = {"OIL": "thousand barrels per day", "GAS": "million cubic feet per day"}
UNIT_SHORT = {"OIL": "thousand bbl/d", "GAS": "MMcf/d"}
PROV = {"AB": "Alberta", "SK": "Saskatchewan", "BC": "British Columbia"}
PNAME = {"OIL": "Oil", "GAS": "Gas"}
MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MS = [m[:3] for m in MON]
SERIF, SANS, MONO = "Fraunces, Georgia, serif", "Inter, Arial, sans-serif", "'IBM Plex Mono', 'DejaVu Sans Mono', monospace"
SYMBOL = "'DejaVu Sans', Inter, sans-serif"  # for glyphs the web fonts lack (≠ ≤ ³)

THEMES = {
    "night": dict(bg="#0a1020", panel="#101a31", ink="#eef3ff", muted="#8fa0c4", line="#26345a", accent="#2f9bff", accent2="#ff6b80", name="Night"),
    "paper": dict(bg="#f5f0e4", panel="#ece5d3", ink="#15203b", muted="#6a6f7d", line="#d3c9b3", accent="#0a58ca", accent2="#c4263f", name="Paper"),
}


def esc(s):
    return escape(str(s), quote=False)


def fmt(v, prod):
    return f"{v:,.0f}" if (prod == "GAS" or v >= 100) else f"{v:,.1f}"


def load():
    out = {}
    for r in csv.DictReader(open(CSV, newline="")):
        key = (r["province"], r["product"])
        y, m = int(r["month"][:4]), int(r["month"][5:])
        out.setdefault(key, {})[(y, m)] = float(r["volume"]) / float(r["days_in_month"]) * CONV[r["product"]]
    return out


def nice_ticks(lo, hi, n=5):
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if step >= raw:
            break
    v = math.floor(lo / step) * step
    ticks = []
    while v <= hi + step * 0.001:
        ticks.append(round(v, 10))
        v += step
    return ticks


def text(x, y, s, size, fill, family=SANS, weight=400, anchor="start", spacing=0, style="", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{spacing}" {("font-style=%r " % style).replace(chr(39), chr(34)) if style else ""}{extra}>{s}</text>')


# ---------------------------------------------------------------- poster shell
def shell(t, label, title, subtitle, body, stats, foot, edition):
    W, H = 1800, 2400
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
         f'<rect x="54" y="54" width="{W - 108}" height="{H - 108}" fill="none" stroke="{t["line"]}" stroke-width="3"/>',
         f'<rect x="78" y="78" width="{W - 156}" height="{H - 156}" fill="none" stroke="{t["line"]}" stroke-width="1.5"/>',
         text(150, 180, esc(label.upper()), 30, t["accent"], SANS, 700, spacing=9),
         text(150, 390, esc(title), min(168, int(1500 / (0.57 * len(title)))), t["ink"], SERIF, 700),
         text(150, 470, esc(subtitle), 40, t["muted"], SANS, 400)]
    o.append(body)
    if stats:
        n = len(stats)
        cw = 1500 / n
        o.append(f'<line x1="150" y1="1780" x2="1650" y2="1780" stroke="{t["line"]}" stroke-width="2"/>')
        for i, (big, small) in enumerate(stats):
            x = 150 + i * cw
            o.append(text(x, 1890, esc(big), 84 if big[0] in "+\u22120123456789" else 52, t["ink"], SERIF, 700))
            for j, ln in enumerate(small.split("\n")):
                o.append(text(x, 1950 + j * 37, esc(ln), 28, t["muted"], SANS, 500))
    o.append(f'<line x1="150" y1="2150" x2="1650" y2="2150" stroke="{t["line"]}" stroke-width="2"/>')
    for j, ln in enumerate(foot):
        o.append(text(150, 2196 + j * 33, esc(ln), 23, t["muted"], SANS, 400))
    o.append(text(150, 2304, esc(edition), 22, t["muted"], SANS, 600, spacing=3))
    o.append(text(1650, 2306, "tidywells.com", 40, t["ink"], SERIF, 700, anchor="end"))
    return "".join(o) + "</svg>"


FOOT_DATA = ["Source: Petrinex (Alberta, Saskatchewan) and BC Energy Regulator public data, aggregated by Tidywells.",
             "Rate = monthly volume divided by days in the month. Oil and gas are the OIL and GAS products in the regulators' files;",
             "totals can differ from other published provincial figures. The vertical axis does not start at zero."]


def line_poster(t, data, key):
    prov, prod = key
    s = data[key]
    months = sorted(s)
    vals = [s[m] for m in months]
    x0, x1, y0, y1 = 190, 1650, 650, 1620
    ticks = nice_ticks(min(vals) * 0.96, max(vals) * 1.10, 5)
    lo, hi = ticks[0], ticks[-1]
    n = len(months)
    X = lambda i: x0 + (x1 - x0) * i / (n - 1)
    Y = lambda v: y1 - (y1 - y0) * (v - lo) / (hi - lo)
    b = [f'<defs><linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["accent"]}" stop-opacity=".38"/><stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/></linearGradient></defs>']
    for v in ticks:
        b.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" stroke="{t["line"]}" stroke-width="1.5"/>')
        b.append(text(x0 - 20, Y(v) + 10, f"{v:,.0f}" if (prod == "GAS" or hi >= 100) else f"{v:,.1f}", 28, t["muted"], MONO, 500, anchor="end"))
    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
    b.append(f'<polygon points="{x0},{y1} {pts} {x1},{y1}" fill="url(#ar)"/>')
    b.append(f'<polyline points="{pts}" fill="none" stroke="{t["accent"]}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/>')
    for i, m in enumerate(months):
        if m[1] == 1:
            b.append(f'<line x1="{X(i):.1f}" y1="{y1}" x2="{X(i):.1f}" y2="{y1 + 18}" stroke="{t["muted"]}" stroke-width="2"/>')
            b.append(text(X(i), y1 + 62, str(m[0]), 32, t["muted"], MONO, 500, anchor="middle"))
    b.append(text(x0, y0 - 40, esc(UNIT[prod].upper()), 26, t["muted"], SANS, 600, spacing=4))
    # markers: peak and latest
    ip = max(range(n), key=lambda i: vals[i])
    il = n - 1
    marks = [(il, f"{MS[months[il][1] - 1]} {months[il][0]}: {fmt(vals[il], prod)}")]
    if il - ip > 3:
        marks.append((ip, f"Peak {MS[months[ip][1] - 1]} {months[ip][0]}: {fmt(vals[ip], prod)}"))
    for i, lab in marks:
        b.append(f'<circle cx="{X(i):.1f}" cy="{Y(vals[i]):.1f}" r="13" fill="{t["bg"]}" stroke="{t["accent2"]}" stroke-width="6"/>')
        b.append(text(X(i) - (18 if i == il else 0), Y(vals[i]) + (70 if i == il else -36), lab, 30, t["ink"], SANS, 700, anchor="end" if i == il else "middle"))
    last, prev = vals[-1], s.get((months[-1][0] - 1, months[-1][1]))
    yoy = (last / prev - 1) * 100
    since = (last / vals[0] - 1) * 100
    lo_i = min(range(n), key=lambda i: vals[i])
    sign = lambda v: ("+" if v >= 0 else "−") + f"{abs(v):.1f}%"
    stats = [(fmt(last, prod), f"{MON[months[-1][1] - 1]} {months[-1][0]}\n{UNIT_SHORT[prod]}"),
             (sign(yoy), "on a year earlier"),
             (fmt(vals[ip], prod), f"peak month\n{MON[months[ip][1] - 1]} {months[ip][0]}"),
             (sign(since), f"since {MON[months[0][1] - 1]} {months[0][0]}")]
    title = f"{PROV[prov]} {PNAME[prod]}"
    sub = f"Monthly production, {MON[months[0][1] - 1]} {months[0][0]} to {MON[months[-1][1] - 1]} {months[-1][0]}"
    ed = f"DATA THROUGH {MON[months[-1][1] - 1].upper()} {months[-1][0]}"
    return shell(t, "Tidywells · Canadian oil & gas data", title, sub, "".join(b), stats, FOOT_DATA, ed), {
        "latest": last, "yoy": yoy, "since": since, "peak": vals[ip], "latest_month": months[-1], "first": vals[0]}


def multiples_poster(t, data):
    keys = [("AB", "OIL"), ("AB", "GAS"), ("SK", "OIL"), ("SK", "GAS"), ("BC", "OIL"), ("BC", "GAS")]
    b = []
    pw, ph = 720, 290
    info = {}
    for idx, key in enumerate(keys):
        prov, prod = key
        s = data[key]
        months = sorted(s)
        vals = [s[m] for m in months]
        col, row = idx % 2, idx // 2
        ox, oy = 150 + col * 780, 620 + row * 500
        lo, hi = min(vals), max(vals)
        pad = (hi - lo) * 0.12 or 1
        lo -= pad
        hi += pad
        n = len(vals)
        X = lambda i: ox + pw * i / (n - 1)
        Y = lambda v: oy + ph - ph * (v - lo) / (hi - lo)
        last = vals[-1]
        prev = s[(months[-1][0] - 1, months[-1][1])]
        yoy = (last / prev - 1) * 100
        b.append(text(ox, oy - 64, f"{PROV[prov]} {PNAME[prod].lower()}", 42, t["ink"], SERIF, 700))
        b.append(text(ox, oy - 20, f"{fmt(last, prod)} {UNIT_SHORT[prod]}", 28, t["muted"], MONO, 500))
        b.append(f'<line x1="{ox}" y1="{oy + ph}" x2="{ox + pw}" y2="{oy + ph}" stroke="{t["line"]}" stroke-width="2"/>')
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        b.append(f'<polyline points="{pts}" fill="none" stroke="{t["accent"]}" stroke-width="5" stroke-linejoin="round"/>')
        b.append(f'<circle cx="{X(n - 1):.1f}" cy="{Y(last):.1f}" r="9" fill="{t["accent"]}"/>')
        for i, m in enumerate(months):
            if m[1] == 1:
                b.append(text(X(i), oy + ph + 40, str(m[0]), 24, t["muted"], MONO, 500, anchor="middle"))
        sg = "+" if yoy >= 0 else "−"
        b.append(text(ox, oy + ph + 84, f"{sg}{abs(yoy):.1f}% on a year earlier", 28, t["accent2"] if yoy < 0 else t["accent"], SANS, 700))
        info[key] = (last, yoy)
    months = sorted(data[keys[0]])
    ed = f"DATA THROUGH {MON[months[-1][1] - 1].upper()} {months[-1][0]}"
    foot = ["Source: Petrinex (Alberta, Saskatchewan) and BC Energy Regulator public data, aggregated by Tidywells.",
            "Each panel has its own vertical scale, which does not start at zero. Rate = monthly volume divided by days in the month.",
            "Oil in thousand bbl/d, gas in MMcf/d. Totals can differ from other published provincial figures."]
    return shell(t, "Tidywells · Canadian oil & gas data", "Five Years, Six Lines",
                 f"Oil and gas production in three provinces, January 2022 to {MON[months[-1][1] - 1]} {months[-1][0]}", "".join(b), None, foot, ed), info


def season_index(data, key, years=(2022, 2023, 2024, 2025)):
    s = data[key]
    idx = []
    for m in range(1, 13):
        r = []
        for y in years:
            mean = sum(s[(y, k)] for k in range(1, 13)) / 12
            r.append(s[(y, m)] / mean)
        idx.append(sum(r) / len(r))
    return idx


def season_poster(t, data):
    cx, cy, R = 900, 1180, 470
    keys = [("AB", "GAS", t["accent"]), ("BC", "GAS", t["accent2"])]
    idxs = {k[0]: season_index(data, (k[0], k[1])) for k in keys}
    allv = [v for ix in idxs.values() for v in ix]
    lo, hi = 0.80, max(1.20, math.ceil(max(allv) * 20) / 20)
    r_of = lambda v: R * 0.25 + (R * 0.75) * (v - lo) / (hi - lo)
    ang = lambda m: -math.pi / 2 + (m + 0.5) * 2 * math.pi / 12
    b = []
    for v in (0.9, 1.0, 1.1, 1.2):
        if lo <= v <= hi:
            dash = "" if v == 1.0 else 'stroke-dasharray="6 10"'
            b.append(f'<circle cx="{cx}" cy="{cy}" r="{r_of(v):.1f}" fill="none" stroke="{t["muted"] if v == 1.0 else t["line"]}" stroke-width="{3 if v == 1.0 else 2}" {dash}/>')
            b.append(text(cx + 10, cy - r_of(v) + 26, f"{v * 100:.0f}%", 24, t["muted"], MONO, 500))
    for m in range(12):
        a = ang(m)
        b.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + R * 1.02 * math.cos(a):.1f}" y2="{cy + R * 1.02 * math.sin(a):.1f}" stroke="{t["line"]}" stroke-width="1.5"/>')
        lx, ly = cx + (R + 70) * math.cos(a), cy + (R + 70) * math.sin(a) + 10
        b.append(text(lx, ly, MS[m], 32, t["ink"], SANS, 600, anchor="middle"))
    for prov, prod, col in keys:
        pts = []
        for m in range(12):
            a = ang(m)
            r = r_of(idxs[prov][m])
            pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
        b.append(f'<polygon points="{" ".join(pts)}" fill="{col}" fill-opacity=".16" stroke="{col}" stroke-width="7" stroke-linejoin="round"/>')
        for m in range(12):
            a = ang(m)
            r = r_of(idxs[prov][m])
            b.append(f'<circle cx="{cx + r * math.cos(a):.1f}" cy="{cy + r * math.sin(a):.1f}" r="9" fill="{col}"/>')
    b.append(f'<rect x="150" y="560" width="26" height="26" rx="6" fill="{t["accent"]}"/>' + text(190, 583, "Alberta gas", 32, t["ink"], SANS, 600))
    b.append(f'<rect x="440" y="560" width="26" height="26" rx="6" fill="{t["accent2"]}"/>' + text(480, 583, "British Columbia gas", 32, t["ink"], SANS, 600))
    ab, bc = idxs["AB"], idxs["BC"]
    hi_m = max(range(12), key=lambda m: ab[m])
    lo_m = min(range(12), key=lambda m: ab[m])
    pct = lambda v: ("+" if v >= 1 else "−") + f"{abs(v - 1) * 100:.0f}%"
    stats = [(pct(ab[hi_m]), f"Alberta, {MON[hi_m]}\nhighest month"), (pct(ab[lo_m]), f"Alberta, {MON[lo_m]}\nlowest month"),
             (pct(bc[max(range(12), key=lambda m: bc[m])]), f"BC, {MON[max(range(12), key=lambda m: bc[m])]}\nhighest month"),
             (pct(bc[min(range(12), key=lambda m: bc[m])]), f"BC, {MON[min(range(12), key=lambda m: bc[m])]}\nlowest month")]
    foot = ["Source: Petrinex and BC Energy Regulator public data, aggregated by Tidywells. Index = a calendar month's daily rate divided by that",
            "year's average daily rate, averaged over 2022 to 2025 (the four complete years). 100% is the year's average. Gas is the GAS product",
            "in the regulators' files."]
    return shell(t, "Tidywells · Canadian oil & gas data", "Gas Has a Season", "Alberta and BC gas by calendar month against each year's average",
                 "".join(b), stats, foot, "FOUR COMPLETE YEARS: 2022 TO 2025"), {"AB": ab, "BC": bc}


def arps(t_, b, di):
    return math.exp(-di * t_) if b == 0 else (1 + b * di * t_) ** (-1 / b)


def decline_poster(t, data):
    x0, x1, y0, y1 = 190, 1480, 650, 1560
    di, T = 0.5, 10.0
    curves = [(0, t["muted"], "b = 0"), (0.5, t["accent2"], "b = 0.5"), (1.0, t["accent"], "b = 1.0"), (1.5, t["ink"], "b = 1.5")]
    X = lambda v: x0 + (x1 - x0) * v / T
    Y = lambda q: y1 - (y1 - y0) * q
    b = []
    for q in (0, .25, .5, .75, 1.0):
        b.append(f'<line x1="{x0}" y1="{Y(q):.1f}" x2="{x1}" y2="{Y(q):.1f}" stroke="{t["line"]}" stroke-width="1.5"/>')
        b.append(text(x0 - 20, Y(q) + 10, f"{q * 100:.0f}%", 28, t["muted"], MONO, 500, anchor="end"))
    for yr in range(0, 11, 2):
        b.append(text(X(yr), y1 + 58, f"{yr}", 32, t["muted"], MONO, 500, anchor="middle"))
    b.append(text((x0 + x1) / 2, y1 + 112, "YEARS FROM START OF DECLINE", 26, t["muted"], SANS, 600, anchor="middle", spacing=4))
    b.append(text(x0, y0 - 40, "RATE AS A SHARE OF THE STARTING RATE", 26, t["muted"], SANS, 600, spacing=4))
    for bb, col, lab in curves:
        pts = " ".join(f"{X(tt / 10):.1f},{Y(arps(tt / 10, bb, di)):.1f}" for tt in range(0, 101))
        b.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{8 if bb == 1.0 else 6}" stroke-linecap="round"/>')
        yy = Y(arps(T, bb, di))
        b.append(text(x1 + 18, yy + 10, lab, 30, col, SANS, 700))
    stats = [("Exponential", "b = 0.\nThe same share is\nlost every year."),
             ("Hyperbolic", "0 < b < 2. The decline\nrate itself falls as\nthe well ages."),
             ("Harmonic", "b = 1. A special case\nof the hyperbolic\nfamily."),
             ("Tidywells", "Fits b from 0 to 2,\nso fitted curves\nstay realistic.")]
    foot = ["Illustration of the Arps family, q = qi / (1 + b \u00b7 Di \u00b7 t)^(1/b), with the same starting rate and an initial nominal",
            "decline Di of 50% per year. Real wells scatter around these shapes. Illustrative only, not for reserves reporting or",
            "investment decisions. Reference: Arps, J.J. (1945), Analysis of Decline Curves, Transactions of the AIME."]
    return shell(t, "Tidywells · Canadian oil & gas data", "Shape of a Decline",
                 "Four members of the Arps family, same start, different futures", "".join(b), stats, foot, "q = qi / (1 + b · Di · t)^(1/b)"), {}


OIL3 = ("AB", "SK", "BC")
AMBER = "#f2a93b"
FOOT_ZERO = ["Source: Petrinex (Alberta, Saskatchewan) and BC Energy Regulator public data, aggregated by Tidywells.",
             "Rate = monthly volume divided by days in the month. Oil is the OIL product in the regulators' files; totals can differ from",
             "other published provincial figures. 'Record' means the highest month in this dataset, January 2022 onward."]


def oil_total(data, ym):
    return sum(data[(p, "OIL")][ym] for p in OIL3)


def record_poster(t, data):
    """Stacked area of the three provinces' oil, zero baseline."""
    months = sorted(data[("AB", "OIL")])
    n = len(months)
    tot = [oil_total(data, m) for m in months]
    x0, x1, y0, y1 = 190, 1650, 650, 1620
    ticks = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500]
    hi = ticks[-1]
    X = lambda i: x0 + (x1 - x0) * i / (n - 1)
    Y = lambda v: y1 - (y1 - y0) * v / hi
    b = []
    for v in ticks:
        b.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" stroke="{t["line"]}" stroke-width="1.5"/>')
        b.append(text(x0 - 20, Y(v) + 10, f"{v:,.0f}", 28, t["muted"], MONO, 500, anchor="end"))
    cols = {"AB": t["accent"], "SK": AMBER, "BC": t["accent2"]}
    base = [0.0] * n
    for p in OIL3:
        top = [base[i] + data[(p, "OIL")][months[i]] for i in range(n)]
        up = " ".join(f"{X(i):.1f},{Y(top[i]):.1f}" for i in range(n))
        dn = " ".join(f"{X(i):.1f},{Y(base[i]):.1f}" for i in range(n - 1, -1, -1))
        b.append(f'<polygon points="{up} {dn}" fill="{cols[p]}" fill-opacity=".85"/>')
        base = top
    for i, m in enumerate(months):
        if m[1] == 1:
            b.append(f'<line x1="{X(i):.1f}" y1="{y1}" x2="{X(i):.1f}" y2="{y1 + 18}" stroke="{t["muted"]}" stroke-width="2"/>')
            b.append(text(X(i), y1 + 62, str(m[0]), 32, t["muted"], MONO, 500, anchor="middle"))
    b.append(text(x0, y0 - 40, "THOUSAND BARRELS PER DAY, THREE PROVINCES STACKED", 26, t["muted"], SANS, 600, spacing=4))
    ip = max(range(n), key=lambda i: tot[i])
    b.append(f'<circle cx="{X(ip):.1f}" cy="{Y(tot[ip]):.1f}" r="13" fill="{t["bg"]}" stroke="{t["ink"]}" stroke-width="6"/>')
    b.append(text(X(ip) - 24, Y(tot[ip]) - 30, f"Record {MS[months[ip][1] - 1]} {months[ip][0]}: {tot[ip]:,.0f}", 32, t["ink"], SANS, 700, anchor="end"))
    ab_mid = (Y(data[("AB", "OIL")][months[n // 2]] / 2))
    b.append(text(X(n // 2), ab_mid + 14, "ALBERTA", 40, t["bg"], SANS, 800, anchor="middle", spacing=8))
    sk_mid = Y(data[("AB", "OIL")][months[n // 4]] + data[("SK", "OIL")][months[n // 4]] / 2)
    b.append(text(X(n // 4), sk_mid + 12, "SASKATCHEWAN", 28, t["bg"], SANS, 800, anchor="middle", spacing=5))
    last = tot[-1]
    first = tot[0]
    since = (last / first - 1) * 100
    ab_share = data[("AB", "OIL")][months[-1]] / last * 100
    stats = [(f"{last:,.0f}", f"thousand bbl/d\n{MON[months[-1][1] - 1]} {months[-1][0]}"),
             (f"+{since:.1f}%", f"since {MON[months[0][1] - 1]} {months[0][0]}"),
             (f"{tot[ip]:,.0f}", f"record month\n{MON[months[ip][1] - 1]} {months[ip][0]}"),
             (f"{ab_share:.0f}%", "of it is Alberta")]
    return shell(t, "Tidywells · Canadian oil & gas data", "Record Barrels",
                 "Alberta, Saskatchewan and BC oil, stacked: the highest month since January 2022",
                 "".join(b), stats, FOOT_ZERO, f"DATA THROUGH {MON[months[-1][1] - 1].upper()} {months[-1][0]}"), {}


def peak_now(data):
    rows = []
    for key, s in data.items():
        months = sorted(s)
        vals = [s[m] for m in months]
        ip = max(range(len(vals)), key=lambda i: vals[i])
        rows.append((vals[-1] / vals[ip] * 100, key, months[ip]))
    rows.sort(reverse=True)
    return rows


def peak_now_poster(t, data):
    rows = peak_now(data)
    x0, x1 = 700, 1600
    b = [text(150, 600, "LATEST MONTH AS A SHARE OF EACH STREAM'S OWN BEST MONTH", 26, t["muted"], SANS, 600, spacing=4),
         f'<line x1="{x1}" y1="650" x2="{x1}" y2="1690" stroke="{t["ink"]}" stroke-width="3" stroke-dasharray="10 8"/>',
         text(x1, 640, "PEAK = 100%", 22, t["ink"], SANS, 700, anchor="end", spacing=2)]
    for i, (pct, (prov, prod), pm) in enumerate(rows):
        y = 700 + i * 160
        col = AMBER if prod == "OIL" else t["muted"]
        b.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="96" rx="10" fill="{t["panel"]}"/>')
        b.append(f'<rect x="{x0}" y="{y}" width="{(x1 - x0) * pct / 100:.1f}" height="96" rx="10" fill="{col}"/>')
        b.append(text(150, y + 46, f"{PROV[prov]} {PNAME[prod]}", 40, t["ink"], SANS, 800 if prod == "OIL" else 600))
        b.append(text(150, y + 86, f"peak {MON[pm[1] - 1]} {pm[0]}", 26, t["muted"], SANS, 500))
        b.append(text(x0 + (x1 - x0) * pct / 100 - 22, y + 66, f"{pct:.0f}%", 52, "#14213d" if prod == "OIL" else t["bg"], SERIF, 700, anchor="end"))
    top = rows[0]
    oil = [r for r in rows if r[1][1] == "OIL"]
    stats = [(f"{rows[0][0]:.1f}%", f"{PROV[rows[0][1][0]]} {PNAME[rows[0][1][1]].lower()}\nvs its peak"),
             (f"{oil[1][0]:.1f}%", f"{PROV[oil[1][1][0]]} {PNAME[oil[1][1][1]].lower()}\nvs its peak"),
             (f"{rows[-1][0]:.1f}%", f"{PROV[rows[-1][1][0]]} {PNAME[rows[-1][1][1]].lower()}\nvs its peak"),
             ("6", "streams: three oil,\nthree gas")]
    foot = ["Source: Petrinex (Alberta, Saskatchewan) and BC Energy Regulator public data, aggregated by Tidywells.",
            "Peak = the highest monthly rate of that stream since January 2022; latest = September 2026. Gas is seasonal, so winter",
            "peaks flatter the comparison against gas. BC oil is a very small stream. Bars start at zero."]
    return shell(t, "Tidywells · Canadian oil & gas data", "Peak vs Now", "How close each stream is to its own best month",
                 "".join(b), stats, foot, "DATA THROUGH SEPTEMBER 2026"), {}


def share_poster(t, data):
    last = (2026, 9)
    vals = {p: data[(p, "OIL")][last] for p in OIL3}
    tot = sum(vals.values())
    share = {p: vals[p] / tot * 100 for p in OIL3}
    # largest-remainder allocation of 100 dots
    dots = {p: int(share[p]) for p in OIL3}
    for p in sorted(OIL3, key=lambda q: share[q] - int(share[q]), reverse=True)[: 100 - sum(dots.values())]:
        dots[p] += 1
    seq = ["AB"] * dots["AB"] + ["SK"] * dots["SK"] + ["BC"] * dots["BC"]
    cols = {"AB": t["accent"], "SK": AMBER, "BC": t["accent2"]}
    b = [text(150, 600, "EACH DOT IS ONE BARREL IN EVERY 100 PRODUCED, SEPTEMBER 2026", 26, t["muted"], SANS, 600, spacing=4)]
    for k, p in enumerate(seq):
        r, c = divmod(k, 10)
        b.append(f'<circle cx="{225 + c * 97}" cy="{730 + r * 97}" r="38" fill="{cols[p]}"/>')
    lx = 1250
    for j, (p, lab) in enumerate((("AB", "Alberta"), ("SK", "Saskatchewan"), ("BC", "British Columbia"))):
        y = 760 + j * 260
        big = f"{dots[p]}" if dots[p] else "&lt;1"
        b.append(f'<circle cx="{lx}" cy="{y - 24}" r="18" fill="{cols[p]}"/>')
        b.append(text(lx + 40, y + 10, big, 110, t["ink"], SERIF, 700))
        b.append(text(lx + 40, y + 62, f"{lab}: {share[p]:.1f}%", 32, t["muted"], SANS, 600))
    stats = [(f"{vals['AB']:,.0f}", "Alberta, thousand\nbbl/d"), (f"{vals['SK']:,.0f}", "Saskatchewan,\nthousand bbl/d"),
             (f"{vals['BC']:,.1f}", "British Columbia,\nthousand bbl/d"), (f"{tot:,.0f}", "three provinces,\nthousand bbl/d")]
    foot = ["Source: Petrinex (Alberta, Saskatchewan) and BC Energy Regulator public data, aggregated by Tidywells.",
            "Rate = monthly volume divided by days in the month; dots are rounded to 100 by largest remainder, so BC oil rounds to under",
            "one dot. Oil is the OIL product in the regulators' files; totals can differ from other published provincial figures."]
    return shell(t, "Tidywells · Canadian oil & gas data", "86 of Every 100", "Barrels of oil per day: who produces what in the three provinces",
                 "".join(b), stats, foot, "DATA THROUGH SEPTEMBER 2026"), {}


def posters(data):
    out = {}
    series = [("AB", "OIL"), ("AB", "GAS"), ("SK", "OIL"), ("SK", "GAS"), ("BC", "OIL"), ("BC", "GAS")]
    for th, t in THEMES.items():
        for key in series:
            svg, _ = line_poster(t, data, key)
            out[f"poster-{key[0].lower()}-{key[1].lower()}-{th}"] = svg
        out[f"poster-five-years-{th}"] = multiples_poster(t, data)[0]
        out[f"poster-gas-season-{th}"] = season_poster(t, data)[0]
        out[f"poster-decline-shape-{th}"] = decline_poster(t, data)[0]
        out[f"poster-record-barrels-{th}"] = record_poster(t, data)[0]
        out[f"poster-peak-vs-now-{th}"] = peak_now_poster(t, data)[0]
        out[f"poster-86-of-100-{th}"] = share_poster(t, data)[0]
    return out


if __name__ == "__main__":
    out = Path(sys.argv[1])
    (out / "svg").mkdir(parents=True, exist_ok=True)
    data = load()
    n = 0
    for name, svg in posters(data).items():
        (out / "svg" / f"{name}.svg").write_text(svg, encoding="utf-8")
        n += 1
    print("posters", n)
