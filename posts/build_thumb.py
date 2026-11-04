"""Render posts/thumb_backtest.svg from posts/thumb_backtest.json (made by thumb_data.py)."""
import json
from pathlib import Path

D = Path(__file__).resolve().parent
d = json.loads((D / "thumb_backtest.json").read_text())
N, T = d["months"], d["train_months"]
W, H, x0, x1, y0, y1 = 240, 140, 30, 230, 14, 104
lo, hi = 0.3, 0.9
X = lambda t: x0 + (x1 - x0) * t / (N - 1)
Y = lambda v: y1 - (y1 - y0) * (min(max(v, lo), hi) - lo) / (hi - lo)
pts = lambda s, a, b: " ".join(f"{X(i):.1f},{Y(s[i]):.1f}" for i in range(a, b) if s[i] == s[i])
act, mod = d["actual"], d["model"]
first = next(i for i, v in enumerate(mod) if v == v)
grid = "".join(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" stroke="var(--line)" stroke-width=".6"/>'
               f'<text x="{x0 - 4}" y="{Y(v) + 3:.1f}" font-size="8.5" text-anchor="end" fill="var(--muted)" font-family="system-ui,sans-serif">{int(v * 100)}%</text>' for v in (0.4, 0.6, 0.8))
svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Median reported and forecast oil rate for {d["n"]} Alberta wells, each scaled to its own peak; forecast fitted on the first {T} months">'
       f'<rect x="{X(T):.1f}" y="8" width="{x1 - X(T) + 4:.1f}" height="{y1 - 8}" rx="4" fill="var(--accent)" fill-opacity=".12"/>{grid}'
       f'<polyline points="{pts(act, 0, N)}" fill="none" stroke="var(--fg)" stroke-opacity=".75" stroke-width="1.8" stroke-linejoin="round"/>'
       f'<polyline points="{pts(mod, first, T + 1)}" fill="none" stroke="var(--accent)" stroke-width="2.4" stroke-linecap="round"/>'
       f'<polyline points="{pts(mod, T, N)}" fill="none" stroke="var(--accent)" stroke-width="2.4" stroke-dasharray="5 4" stroke-linecap="round"/>'
       f'<text x="{x0}" y="{y1 + 13}" font-size="8.5" fill="var(--muted)" font-family="system-ui,sans-serif">fit: first {T} months</text>'
       f'<text x="{x1 + 2}" y="{y1 + 13}" font-size="8.5" fill="var(--accent)" text-anchor="end" font-family="system-ui,sans-serif">test: next {N - T}</text>'
       f'<text x="{x0}" y="{y1 + 26}" font-size="8.5" fill="var(--muted)" font-family="system-ui,sans-serif">Median of {d["n"]} {d["label"]} wells · <tspan fill="var(--fg)">&#9473; reported</tspan> <tspan fill="var(--accent)">&#9473; forecast</tspan></text></svg>')
(D / "thumb_backtest.svg").write_text(svg)
