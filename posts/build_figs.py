"""Draw the article figures (inline SVG) into docs/posts/decline-backtest.html.
Needs posts/fig_curves.json (python posts/thumb_data.py ab|sk|bc FOLDER). Figure B uses the
'typical miss' table in the write-up (output of posts/backtest.py ... extra)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F = 'font-family="system-ui,sans-serif"'
cur = json.loads((ROOT / "posts" / "fig_curves.json").read_text())
ORDER = ["AB oil", "SK oil", "SK gas", "BC gas"]
NAMES = {"AB oil": "Alberta oil", "SK oil": "Saskatchewan oil", "SK gas": "Saskatchewan gas", "BC gas": "BC gas"}


def fig_a():
    N, T = 57, 45
    vals = [v for k in ORDER for s in ("actual", "model") for v in cur[k][s] if v == v]
    lo, hi = 0.2, 1.0
    PW, PH, gx, gy = 330, 190, 30, 36
    W, H = 2 * PW + gx + 40, 2 * PH + gy + 50
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Median reported and forecast rate for four groups of wells">']
    for idx, k in enumerate(ORDER):
        c = cur[k]
        ox, oy = 40 + (idx % 2) * (PW + gx), 26 + (idx // 2) * (PH + gy)
        x0, x1, y0, y1 = ox, ox + PW - 10, oy, oy + PH - 40
        X = lambda t: x0 + (x1 - x0) * t / (N - 1)
        Y = lambda v: y1 - (y1 - y0) * (min(max(v, lo), hi) - lo) / (hi - lo)
        pts = lambda s, a, b: " ".join(f"{X(i):.1f},{Y(s[i]):.1f}" for i in range(a, b) if s[i] == s[i])
        first = next(i for i, v in enumerate(c["model"]) if v == v)
        out.append(f'<text x="{x0}" y="{oy - 10}" font-size="13" font-weight="600" fill="var(--fg)" {F}>{NAMES[k]} <tspan fill="var(--muted)" font-weight="400">({c["n"]} wells)</tspan></text>')
        out.append(f'<rect x="{X(T):.1f}" y="{y0}" width="{x1 - X(T):.1f}" height="{y1 - y0}" fill="var(--accent)" fill-opacity=".12"/>')
        for v in (0.4, 0.6, 0.8, 1.0):
            out.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" stroke="var(--line)" stroke-width=".7"/>'
                       f'<text x="{x0 - 5}" y="{Y(v) + 4:.1f}" font-size="10.5" text-anchor="end" fill="var(--muted)" {F}>{int(v * 100)}%</text>')
        for m in (0, 12, 24, 36, 48):
            out.append(f'<text x="{X(m):.1f}" y="{y1 + 14}" font-size="10.5" text-anchor="middle" fill="var(--muted)" {F}>{m}</text>')
        out.append(f'<polyline points="{pts(c["actual"], 0, N)}" fill="none" stroke="var(--fg)" stroke-opacity=".8" stroke-width="1.8" stroke-linejoin="round"/>')
        out.append(f'<polyline points="{pts(c["model"], first, T + 1)}" fill="none" stroke="var(--accent)" stroke-width="2.4"/>')
        out.append(f'<polyline points="{pts(c["model"], T, N)}" fill="none" stroke="var(--accent)" stroke-width="2.4" stroke-dasharray="5 4"/>')
        out.append(f'<text x="{x1}" y="{y1 + 28}" font-size="10.5" text-anchor="end" fill="var(--muted)" {F}>months since Jan 2022</text>')
    ly = H - 8
    out.append(f'<text x="40" y="{ly}" font-size="11.5" fill="var(--fg)" {F}>&#9473; median reported</text>'
               f'<text x="175" y="{ly}" font-size="11.5" fill="var(--accent)" {F}>&#9473; median forecast (dashed = predicted 12 months)</text>'
               f'<text x="{W - 6}" y="{ly}" font-size="11.5" text-anchor="end" fill="var(--muted)" {F}>shaded = test window</text></svg>')
    return "".join(out)


def fig_b():
    data = {"Alberta oil": [36, 23, 17], "Saskatchewan oil": [34, 24, 17], "Saskatchewan gas": [29, 21, 16], "BC gas": [24, 19, 13]}
    cols = {"Alberta oil": "#5fd0c0", "Saskatchewan oil": "#6aa6f0", "Saskatchewan gas": "#e0a458", "BC gas": "#d98bb0"}
    W, H, x0, x1, y0, y1 = 720, 300, 60, 520, 20, 250
    xs = {24: x0, 36: x0 + (x1 - x0) * 12 / 21, 45: x1}
    Y = lambda v: y1 - (y1 - y0) * v / 40
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Typical forecast miss falls as months of history rise, for four groups">']
    for v in (0, 10, 20, 30, 40):
        o.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" stroke="var(--line)" stroke-width=".7"/>'
                 f'<text x="{x0 - 8}" y="{Y(v) + 4:.1f}" font-size="12" text-anchor="end" fill="var(--muted)" {F}>{v}%</text>')
    for m, x in xs.items():
        o.append(f'<text x="{x}" y="{y1 + 20}" font-size="12" text-anchor="middle" fill="var(--muted)" {F}>{m} months</text>')
    o.append(f'<text x="{(x0 + x1) / 2}" y="{y1 + 40}" font-size="12" text-anchor="middle" fill="var(--muted)" {F}>history used to fit the curve</text>')
    o.append(f'<text x="14" y="{(y0 + y1) / 2}" font-size="12" text-anchor="middle" fill="var(--muted)" transform="rotate(-90 14 {(y0 + y1) / 2})" {F}>typical miss on 12-month volume</text>')
    ends = []
    for k, ys in data.items():
        pts = [(xs[m], Y(v)) for m, v in zip((24, 36, 45), ys)]
        o.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{cols[k]}" stroke-width="2.6" stroke-linejoin="round"/>')
        for (a, b), v in zip(pts, ys):
            o.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4" fill="{cols[k]}"/>')
        ends.append([k, pts[-1][1], ys[-1]])
    ends.sort(key=lambda e: e[1])
    prev = -99
    for e in ends:
        yy = max(e[1], prev + 16); prev = yy
        o.append(f'<text x="{x1 + 14}" y="{yy + 4:.1f}" font-size="12.5" fill="{cols[e[0]]}" {F}>{e[0]} · {e[2]}%</text>')
    o.append(f'<text x="{x0 + 6}" y="{Y(36) - 10:.1f}" font-size="11.5" fill="var(--muted)" {F}>36% at 24 months, Alberta oil</text></svg>')
    return "".join(o)


def put(s, key, svg, cap):
    html = f'<figure class="fig"><div class="tw">{svg}</div><figcaption>{cap}</figcaption></figure>'
    return re.sub(rf"<!--{key}-->.*?<!--/{key}-->", lambda m: f"<!--{key}-->{html}<!--/{key}-->", s, flags=re.S)


p = ROOT / "docs" / "posts" / "decline-backtest.html"
s = p.read_text(encoding="utf-8")
s = put(s, "FIGA", fig_a(), "<b>Figure 1.</b> Median reported rate and median forecast for each group, with every well scaled to its own peak in the first 45 months. The forecast was fitted on months 0 to 45 only; the dashed part is the 12-month prediction. The forecast ends up below the reported curve in all four groups. Real data from the wells tested above.")
s = put(s, "FIGB", fig_b(), "<b>Figure 2.</b> Typical miss on the 12-month volume when the curve is fitted on 24, 36 or 45 months of history. More history cuts the miss in every group (values from the table above).")
p.write_text(s, encoding="utf-8")
print("figures written")
