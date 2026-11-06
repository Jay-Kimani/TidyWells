"""Generate the analysis posts (recovery, seasonality) and the monthly snapshot posts from
posts/monthly_agg.csv and posts/recovery.json. Aggregates only. Then run posts/build_feed.py.
    python posts/gen_posts.py
"""
import csv
import math
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = "2026-11-04"   # date of the first batch of posts
import datetime as _dt
TODAY = _dt.date.today().isoformat()
try:   # keep the dates of posts that already exist; only new posts get today's date
    OLD = {p_["slug"]: p_["date"] for p_ in json.loads((ROOT / "posts" / "posts.json").read_text())}
except Exception:
    OLD = {}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
F = 'font-family="system-ui,sans-serif"'
M3_BBL, E3M3_MCF = 6.28981, 35.3147

# ---------- page shell (taken from the first post so all pages match) ----------
_t = (ROOT / "docs" / "posts" / "decline-backtest.html").read_text(encoding="utf-8")
PRE = _t[:_t.index("<article>")]
POST = _t[_t.index("</article>"):]
LICENCE = ('<p><small>Contains information licensed from Petrinex public data (Alberta, Saskatchewan) and the BC Energy Regulator; '
           'Crown copyright of the provinces is acknowledged. Tidywells is not affiliated with any regulator.</small></p>')


def page(slug, title, body):
    pre = re.sub(r"<title>.*?</title>", f"<title>{title} · Tidywells</title>", PRE, count=1)
    (ROOT / "docs" / "posts" / f"{slug}.html").write_text(pre + "<article>" + body + POST, encoding="utf-8")


def fig(svg, cap, take=None):
    tk = f'<p class="take">{take}</p>' if take else ""
    return f'<figure class="fig">{tk}<div class="tw">{svg}</div><figcaption>{cap}</figcaption></figure>'


def pct(x, d=0, sign=True):
    s = f"{abs(x):.{d}f}%"
    return ("+" if x >= 0 else "−") + s if sign else f"{x:.{d}f}%"


# ---------- data ----------
rows = list(csv.DictReader(open(ROOT / "posts" / "monthly_agg.csv")))
vol, wells = defaultdict(dict), defaultdict(dict)
for r in rows:
    k = (r["province"], r["product"])
    d = int(r["days_in_month"])
    f = M3_BBL if r["product"] == "OIL" else E3M3_MCF
    unit = f / 1000 if r["product"] == "OIL" else f / 1000      # oil: thousand bbl/d ; gas: MMcf/d (10^3 m3 * 35.3147 = Mcf; /1000 = MMcf)
    vol[k][r["month"]] = float(r["volume"]) / d * unit
    wells[k][r["month"]] = int(r["wells"])
GROUPS = [("Alberta oil", "AB", "OIL"), ("Alberta gas", "AB", "GAS"), ("Saskatchewan oil", "SK", "OIL"),
          ("Saskatchewan gas", "SK", "GAS"), ("BC oil", "BC", "OIL"), ("BC gas", "BC", "GAS")]
ALL = sorted(next(iter(vol.values())))
UNIT = {"OIL": "thousand bbl/d", "GAS": "MMcf/d"}


def seasonal(k):
    ms = sorted(vol[k]); x = [vol[k][m] for m in ms]
    dev = defaultdict(list)
    for i in range(6, len(x) - 6):
        ma = (0.5 * x[i - 6] + sum(x[i - 5:i + 6]) + 0.5 * x[i + 6]) / 12
        dev[int(ms[i][5:])].append(100 * (x[i] / ma - 1))
    return dev


SEAS = {k: seasonal(k) for k in vol}
AVG = {k: {m: sum(v) / len(v) for m, v in d.items()} for k, d in SEAS.items()}

# ---------- chart helpers ----------
def lines_chart(series, xlabels, W=720, H=300, ylab="", ypct=True, colors=None, zero=True, labels_right=True):
    """series: list of (name, [values], color). x positions are indices."""
    x0, x1, y0, y1 = 70, W - 150, 16, H - 46
    allv = [v for _, s, _ in series for v in s if v is not None]
    lo, hi = min(allv + ([0] if zero else [])), max(allv + ([0] if zero else []))
    pad = (hi - lo) * 0.08; lo -= pad; hi += pad
    n = len(xlabels)
    X = lambda i: x0 + (x1 - x0) * i / (n - 1)
    Y = lambda v: y1 - (y1 - y0) * (v - lo) / (hi - lo)
    raw = (hi - lo) / 5
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 5, 10) if m * mag >= raw)
    step = max(step, 1)
    t = int(lo // step * step)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{ylab}">']
    while t <= hi:
        if t >= lo:
            o.append(f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{x1}" y2="{Y(t):.1f}" stroke="var(--line)" stroke-width="{1.2 if t == 0 else .6}"/>'
                     f'<text x="{x0 - 8}" y="{Y(t) + 4:.1f}" font-size="11.5" text-anchor="end" fill="var(--muted)" {F}>{t:+d}%</text>' if ypct else
                     f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{x1}" y2="{Y(t):.1f}" stroke="var(--line)" stroke-width=".6"/>'
                     f'<text x="{x0 - 8}" y="{Y(t) + 4:.1f}" font-size="11.5" text-anchor="end" fill="var(--muted)" {F}>{t:,}</text>')
        t += step
    for i, lab in enumerate(xlabels):
        o.append(f'<text x="{X(i):.1f}" y="{y1 + 18}" font-size="11.5" text-anchor="middle" fill="var(--muted)" {F}>{lab}</text>')
    o.append(f'<text x="12" y="{(y0 + y1) / 2}" font-size="11.5" text-anchor="middle" fill="var(--muted)" transform="rotate(-90 12 {(y0 + y1) / 2})" {F}>{ylab}</text>')
    ends = []
    for name, s, col in series:
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s) if v is not None)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.4" stroke-linejoin="round"/>')
        last = max(i for i, v in enumerate(s) if v is not None)
        ends.append((Y(s[last]), name + " " + ((f"{round(s[last]):+d}%" if round(s[last]) else "0%") if ypct else f"{s[last]:,.0f}"), col))
        o.append(f'<circle cx="{X(last):.1f}" cy="{Y(s[last]):.1f}" r="3.4" fill="{col}"/>')
    ends.sort(); prev = -99
    for yy, name, col in ends:
        yy = max(yy, prev + 15); prev = yy
        o.append(f'<text x="{x1 + 10}" y="{yy + 4:.1f}" font-size="12" font-weight="600" fill="{col}" {F}>{name}</text>')
    return "".join(o) + "</svg>"


COL = {"Alberta gas": "#6aa6f0", "BC gas": "#5fd0c0", "Saskatchewan gas": "#e0a458", "Alberta oil": "#d98bb0", "Saskatchewan oil": "#b9a3f0"}

# =====================================================================
# Analysis 2: recovery
# =====================================================================
R = json.loads((ROOT / "posts" / "recovery.json").read_text())
ORDER = [("AB oil", "Alberta oil"), ("SK oil", "Saskatchewan oil"), ("SK gas", "Saskatchewan gas"), ("BC gas", "BC gas")]
rng = lambda key, d=0: f"{min(R[k][key] for k, _ in ORDER):.{d}f} to {max(R[k][key] for k, _ in ORDER):.{d}f}"
t_rec = "".join(f"<tr><td>{n}</td><td>{R[k]['n']}</td><td>{R[k]['recovered_share']:.0f}%</td><td>{pct(R[k]['recovered_lift_median'])}</td></tr>" for k, n in ORDER)
t_dip = "".join(f"<tr><td>{n}</td><td>{R[k]['dip_share_all']:.0f}%</td><td>{pct(R[k]['err_dip'])}</td><td>{pct(R[k]['err_nodip'])}</td></tr>" for k, n in ORDER)
t_rd = "".join(f"<tr><td>{n}</td><td>{R[k]['n_rec_dip']}</td><td>{pct(R[k]['err_rec_dip'])}</td><td>{R[k]['n_rec_nodip']}</td><td>{pct(R[k]['err_rec_nodip'])}</td></tr>" for k, n in ORDER)


def fig_bars():
    W, H, x0, y0, y1 = 720, 300, 56, 20, 250
    lo, hi = -60, 0
    Y = lambda v: y0 + (y1 - y0) * (v - hi) / (lo - hi)
    gw = (W - x0 - 20) / 4
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Median forecast error with and without a low month before the forecast">']
    for t in range(-60, 1, 10):
        o.append(f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{W - 20}" y2="{Y(t):.1f}" stroke="var(--line)" stroke-width="{1.2 if t == 0 else .6}"/>'
                 f'<text x="{x0 - 8}" y="{Y(t) + 4:.1f}" font-size="11.5" text-anchor="end" fill="var(--muted)" {F}>{t}%</text>')
    for i, (k, n) in enumerate(ORDER):
        gx = x0 + gw * i + gw / 2
        for j, (key, col) in enumerate((("err_nodip", "var(--accent)"), ("err_dip", "#e0a458"))):
            v = R[k][key]; bx = gx - 38 + j * 40
            o.append(f'<rect x="{bx:.1f}" y="{Y(0):.1f}" width="34" height="{Y(v) - Y(0):.1f}" rx="3" fill="{col}"/>'
                     f'<text x="{bx + 17:.1f}" y="{Y(v) + 14:.1f}" font-size="11.5" text-anchor="middle" fill="#06162e" {F}>{v:.0f}%</text>')
        o.append(f'<text x="{gx:.1f}" y="{y1 + 20}" font-size="12" text-anchor="middle" fill="var(--fg)" {F}>{n}</text>')
    o.append(f'<rect x="{x0}" y="{H - 22}" width="12" height="12" rx="2" fill="var(--accent)"/><text x="{x0 + 18}" y="{H - 12}" font-size="12" fill="var(--fg)" {F}>no low month before the forecast</text>'
             f'<rect x="{x0 + 260}" y="{H - 22}" width="12" height="12" rx="2" fill="#e0a458"/><text x="{x0 + 278}" y="{H - 12}" font-size="12" fill="var(--fg)" {F}>a low month in the last 6 months of history</text></svg>')
    return "".join(o)


BL = ["< -75%", "-75 to -50", "-50 to -25", "-25 to -10", "-10 to +10", "+10 to +25", "+25 to +50", "+50 to +75", "> +75"]


def fig_hist():
    nb = 9
    def pool(key):
        tot = [0] * 10
        for k, _ in ORDER:
            for i, c in enumerate(R[k][key]): tot[i] += c
        # merge the first bin (-1.0..-0.75 plus anything below is excluded by histogram) and the last two bins
        a = tot[:9]; a[8] += tot[9]
        s = sum(a)
        return [100 * c / s for c in a], s
    rec, nr = pool("hist_recovered"); dec, nd = pool("hist_declining")
    W, H, x0, y0, y1 = 720, 300, 56, 20, 236
    mx = max(max(rec), max(dec)) * 1.12
    Y = lambda v: y1 - (y1 - y0) * v / mx
    gw = (W - x0 - 20) / nb
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Distribution of forecast errors for recovered and declining wells">']
    for t in range(0, int(mx) + 1, 10):
        o.append(f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{W - 20}" y2="{Y(t):.1f}" stroke="var(--line)" stroke-width=".6"/>'
                 f'<text x="{x0 - 8}" y="{Y(t) + 4:.1f}" font-size="11.5" text-anchor="end" fill="var(--muted)" {F}>{t}%</text>')
    for i in range(nb):
        gx = x0 + gw * i
        for j, (s, col) in enumerate(((dec, "var(--accent)"), (rec, "#e0a458"))):
            o.append(f'<rect x="{gx + 6 + j * (gw - 12) / 2:.1f}" y="{Y(s[i]):.1f}" width="{(gw - 14) / 2:.1f}" height="{y1 - Y(s[i]):.1f}" rx="2" fill="{col}"/>'
                     f'<text x="{gx + 6 + j * (gw - 12) / 2 + (gw - 14) / 4:.1f}" y="{Y(s[i]) - 4:.1f}" font-size="10" text-anchor="middle" fill="var(--fg)" {F}>{s[i]:.0f}%</text>')
        o.append(f'<text x="{gx + gw / 2:.1f}" y="{y1 + 16}" font-size="10.5" text-anchor="middle" fill="var(--muted)" {F}>{BL[i]}</text>')
    o.append(f'<text x="{(x0 + W) / 2}" y="{y1 + 34}" font-size="11.5" text-anchor="middle" fill="var(--muted)" {F}>forecast error on the 12-month volume (forecast vs reported)</text>'
             f'<rect x="{x0}" y="{H - 16}" width="12" height="12" rx="2" fill="var(--accent)"/><text x="{x0 + 18}" y="{H - 6}" font-size="12" fill="var(--fg)" {F}>wells that kept declining ({nd})</text>'
             f'<rect x="{x0 + 250}" y="{H - 16}" width="12" height="12" rx="2" fill="#e0a458"/><text x="{x0 + 268}" y="{H - 6}" font-size="12" fill="var(--fg)" {F}>wells that recovered ({nr})</text></svg>')
    return "".join(o)


TK_BARS = f"For wells with a low month in the last six months of history, the typical forecast ran {abs(max(R[k]['err_dip'] for k, _ in ORDER)):.0f}% to {abs(min(R[k]['err_dip'] for k, _ in ORDER)):.0f}% low."
TK_HIST = "Wells that kept declining cluster around zero error; wells that recovered are shifted toward under-forecasts."
rec_body = f'''<h1>Why the decline curve runs low: wells that bounce back</h1>
<p><span class="chip">November 2026</span><span class="chip">Illustrative, not for reserves or investment decisions</span></p>
<p>In the <a href="decline-backtest.html">first backtest</a> every group of wells was forecast a little low, and nearly all of that miss sat in wells whose rate went back up after the training window. Here we look closer: how big is the bounce, and can anything in the history <i>before</i> the forecast warn you? We reuse the same wells and fits as the first post.</p>
<h2>1. How big is the bounce?</h2>
<p>A well counts as recovered if its average rate over the 12 test months was higher than its average over the last three months of history.</p>
<div class="tw"><table><tr><th>Group</th><th>Wells tested</th><th>Share recovered</th><th>Median lift, recovered wells</th></tr>{t_rec}</table></div>
<p><small>Lift = average test-window rate vs the average of the last three months of history, median across recovered wells.</small></p>
<p>Between {rng("recovered_share")}% of wells recovered, but the typical lift was modest: {rng("recovered_lift_median")}% above the last three months. A recovery does not need to be dramatic to leave a declining-curve forecast low, because the curve keeps falling while these wells flatten out.</p>
<h2>2. A low month just before the forecast</h2>
<p>One thing you <i>can</i> see at forecast time is a dip in the history. We flagged a well if its lowest month in the last six months of history was below half of its median rate over the last twelve. That is a rough sign of downtime, a curtailment or a data gap right where the curve is anchored.</p>
<div class="tw"><table><tr><th>Group</th><th>Wells with a low month</th><th>Median error: with a low month</th><th>Median error: without</th></tr>{t_dip}</table></div>
{fig(fig_bars(), "<b>Figure 1.</b> Median forecast error on the 12-month volume, for wells with and without a low month in the last six months of history. Real data, same wells as the first post.", take=TK_BARS)}
<p>Only {rng("dip_share_all")}% of wells had such a month, yet for them the typical forecast ran {abs(max(R[k]["err_dip"] for k, _ in ORDER)):.0f}% to {abs(min(R[k]["err_dip"] for k, _ in ORDER)):.0f}% low, two to five times the miss of the other wells ({abs(max(R[k]["err_nodip"] for k, _ in ORDER)):.0f}% to {abs(min(R[k]["err_nodip"] for k, _ in ORDER)):.0f}% low). A fit that starts from a depressed final stretch tends to extrapolate a rate that is too low.</p>
<h2>3. The dip is only part of the story</h2>
<p>Recovered wells also ran low when there was <i>no</i> low month in the history, so the dip does not explain everything.</p>
<div class="tw"><table><tr><th>Group</th><th>Recovered, with low month</th><th>Median error</th><th>Recovered, no low month</th><th>Median error</th></tr>{t_rd}</table></div>
{fig(fig_hist(), "<b>Figure 2.</b> Distribution of forecast errors, all four groups pooled. Wells that kept declining cluster around zero; wells that recovered spread toward under-forecasts. Real data.", take=TK_HIST)}
<p>Wells that kept declining are centred on zero error. Recovered wells are shifted toward under-forecasts, with or without a visible dip. We cannot see why a well recovered from this data; restarts, workovers, new completions and operating changes would all look alike here.</p>
<h2>What this means in practice</h2>
<ul><li>Before trusting a fit, look at the last six months of history. A low month right at the end is a warning that the forecast will probably run low.</li><li>Treat a recovery allowance as a normal part of a portfolio forecast: {rng("recovered_share")}% of wells in these samples ended up above their recent rate.</li><li>We have not tested a fix. Two obvious experiments are fitting with the dip months removed, and anchoring on a median instead of the last months. They are candidates for a future post.</li></ul>
<h2>Limits</h2>
<ul><li>Same sample as the first post: up to 500 wells per group that kept producing, so wells that shut in for good are excluded.</li><li>The recovered flag uses the test window, which you would not have at forecast time. The low-month flag uses history only, so it is the one you could act on.</li><li>The half-of-median threshold is a rule of thumb we chose; we did not tune it, and other thresholds would give different counts.</li><li>One time window (January 2022 to September 2026).</li><li>The Alberta oil group includes wells licensed for crude bitumen; we did not separate them.</li></ul>
<h2>Reproduce it</h2>
<p>Code: <a href="https://github.com/Jay-Kimani/TidyWells">github.com/Jay-Kimani/TidyWells</a>, <code>posts/recovery.py</code>. Download the files yourself from Petrinex and the BC Energy Regulator; we do not host the data.</p>
<p>Illustrative only. Not for reserves reporting or investment decisions.</p>{LICENCE}'''
page("recovery-low-forecasts", "Why the decline curve runs low", rec_body)

# =====================================================================
# Analysis 3: seasonality
# =====================================================================
SERIES = ["Alberta gas", "BC gas", "Saskatchewan gas", "Alberta oil", "Saskatchewan oil"]
key = {n: (p, pr) for n, p, pr in GROUPS}
fa = lines_chart([(n, [round(AVG[key[n]][m], 2) for m in range(1, 13)], COL[n]) for n in SERIES], SHORT, ylab="rate vs its 12-month trend", ypct=True)
# raw alberta gas by calendar month, one line per year
yrs = ["2022", "2023", "2024", "2025"]
ycol = {"2022": "#8a96a3", "2023": "#5fd0c0", "2024": "#e0a458", "2025": "#6aa6f0"}
fb = lines_chart([(y, [round(vol[("AB", "GAS")][f"{y}-{m:02d}"]) for m in range(1, 13)], ycol[y]) for y in yrs], SHORT,
                 ylab="Alberta gas, MMcf/d", ypct=False, zero=False)
def swing_row(n):
    a = AVG[key[n]]; hi_m = max(a, key=a.get); lo_m = min(a, key=a.get)
    return f"<tr><td>{n}</td><td>{SHORT[hi_m - 1]} ({pct(a[hi_m], 1)})</td><td>{SHORT[lo_m - 1]} ({pct(a[lo_m], 1)})</td><td>{a[hi_m] - a[lo_m]:.0f} points</td></tr>"
t_sw = "".join(swing_row(n) for n in SERIES)
ag, bg, sg, ao, so = (AVG[key[n]] for n in ("Alberta gas", "BC gas", "Saskatchewan gas", "Alberta oil", "Saskatchewan oil"))
sw = lambda a: max(a.values()) - min(a.values())
TK_S1 = f"Alberta gas runs about {abs(ag[1]):.0f}% above trend in January and {abs(ag[5]):.0f}% below it in May; Alberta oil swings only about {sw(ao):.0f} points over the year."
TK_S2 = f"Peak to trough, Alberta gas swings about {sw(ag):.0f} points between calendar months."
seas_body = f'''<h1>Gas has a season. Oil mostly doesn't.</h1>
<p><span class="chip">November 2026</span><span class="chip">Illustrative, not for reserves or investment decisions</span></p>
<p>Before comparing one month of production with another, it helps to know what is normal for that month. We added up reported production for Alberta, Saskatchewan and BC from January 2022 to September 2026 and measured how far each calendar month usually sits above or below its own yearly trend. The answer is very different for gas and for oil.</p>
<h2>What we did</h2>
<ul><li><b>Data:</b> province-wide monthly totals from the same public files as the other posts (Petrinex for Alberta and Saskatchewan, the BC Energy Regulator for BC). Totals are a sum of well-level rows, so they are not official provincial statistics.</li><li><b>Rate:</b> monthly volume divided by calendar days, so short months do not look low.</li><li><b>Seasonal effect:</b> each month's rate divided by a centred 12-month moving average, minus one. We average that for each calendar month across the years where it can be computed (four years, 2022 to 2025).</li></ul>
<h2>1. Gas moves with the seasons</h2>
{fig(fa, "<b>Figure 1.</b> Average distance of each calendar month from its 12-month trend, 2022 to 2025. Real data.", take=TK_S1)}
<p>Alberta gas runs about {abs(ag[1]):.0f}% above trend in January and {abs(ag[12]):.0f}% in December, and about {abs(ag[5]):.0f}% below it in May and {abs(ag[9]):.0f}% in September. BC gas follows the same shape ({abs(bg[1]):.0f}% above in January, {abs(bg[9]):.0f}% below in September). Saskatchewan gas barely has a season (between {pct(sg[4])} and {pct(sg[1])}).</p>
<div class="tw"><table><tr><th>Series</th><th>Highest month</th><th>Lowest month</th><th>Swing</th></tr>{t_sw}</table></div>
{fig(fb, "<b>Figure 2.</b> Alberta gas production by calendar month, one line per year. Real data.", take=TK_S2)}
<p>The winter peak and late-spring to autumn trough are consistent with winter demand and summer maintenance, but this data shows what happened, not why. The Alberta gas swing is about {sw(ag):.0f} points from peak to trough month.</p>
<h2>2. Oil is much flatter</h2>
<p>Alberta oil moves within about {sw(ao):.0f} points over the year (weakest in {SHORT[min(ao, key=ao.get) - 1]} at {pct(min(ao.values()), 1)}, strongest in {SHORT[max(ao, key=ao.get) - 1]} at {pct(max(ao.values()), 1)}), and Saskatchewan oil within about {sw(so):.0f} points. Those are small next to the gas swings, and with four years of data a single unusual month can move them. We left BC oil out because its totals are small and noisy.</p>
<h2>What this means in practice</h2>
<ul><li>When a gas month is up or down 5 to 10% on the previous month, check the calendar before reading anything into it. Compare with the same month a year earlier instead.</li><li>For oil, month-to-month moves are mostly not seasonal, so a change of a few percent is more likely to be real.</li><li>A decline curve fitted to a gas well should expect seasonal bumps; a fit that ends on a winter peak will look more optimistic than one ending in the summer.</li></ul>
<h2>Limits</h2>
<ul><li>Only four years per calendar month. A one-off event, for example a wildfire evacuation or a pipeline outage, can move the average for a single month.</li><li>The totals include only what appears in the public well-level files, and recent months can be revised.</li><li>Alberta oil includes crude bitumen from wells licensed for it, so its small seasonal swing partly reflects bitumen operations.</li><li>The trend adjustment is a simple moving average and cannot separate seasonality from a steady rise or fall within a year.</li></ul>
<h2>Reproduce it</h2>
<p>Code: <a href="https://github.com/Jay-Kimani/TidyWells">github.com/Jay-Kimani/TidyWells</a>, <code>posts/monthly_agg.py</code> and <code>posts/gen_posts.py</code>. Download the files yourself from Petrinex and the BC Energy Regulator; we do not host the data.</p>
<p>Illustrative only. Not for reserves reporting or investment decisions.</p>{LICENCE}'''
page("gas-has-a-season", "Gas has a season. Oil mostly doesn't.", seas_body)

# =====================================================================
# Monthly snapshots
# =====================================================================
def mini_panels(upto):
    ms = [m for m in ALL if m <= upto]
    PW, PH = 220, 110
    W, H = 3 * PW + 40, 2 * (PH + 68) + 4
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Production rate by group since January 2022">']
    for idx, (name, p, pr) in enumerate(GROUPS):
        ox, oy = 14 + (idx % 3) * (PW + 10), 26 + (idx // 3) * (PH + 68)
        s = [vol[(p, pr)][m] for m in ms]
        lo, hi = min(s), max(s); pad = (hi - lo) * 0.12 or 1
        lo -= pad; hi += pad
        X = lambda i: ox + (PW - 12) * i / (len(ms) - 1)
        Y = lambda v: oy + PH - PH * (v - lo) / (hi - lo)
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s))
        o.append(f'<text x="{ox}" y="{oy - 10}" font-size="12.5" font-weight="600" fill="var(--fg)" {F}>{name}</text>')
        o.append(f'<line x1="{ox}" y1="{oy + PH}" x2="{ox + PW - 12}" y2="{oy + PH}" stroke="var(--line)"/>')
        o.append(f'<polyline points="{pts}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round"/>')
        o.append(f'<circle cx="{X(len(ms) - 1):.1f}" cy="{Y(s[-1]):.1f}" r="3.5" fill="var(--accent)"/>')
        for y in range(2022, int(upto[:4]) + 1):
            i = ms.index(f"{y}-01")
            o.append(f'<text x="{X(i):.1f}" y="{oy + PH + 14}" font-size="10.5" fill="var(--muted)" text-anchor="middle" {F}>{y}</text>')
        o.append(f'<text x="{ox}" y="{oy + PH + 28}" font-size="10.5" fill="var(--muted)" {F}>{UNIT[pr]}, {fmt(s[-1], pr)} in {SHORT[int(upto[5:]) - 1]}</text>')
    return "".join(o) + "</svg>"


def fmt(v, pr):
    return f"{v:,.0f}" if (pr == "GAS" or v >= 100) else f"{v:,.1f}"


def prev_month(m, back):
    y, mo = int(m[:4]), int(m[5:])
    mo -= back
    while mo <= 0: y -= 1; mo += 12
    return f"{y}-{mo:02d}"


SNAPS = [m for m in ALL if m >= "2024-01"]
posts = json.loads((ROOT / "posts" / "posts.json").read_text())
posts = [p for p in posts if p.get("kind") not in ("snapshot",) and p["slug"] not in ("recovery-low-forecasts", "gas-has-a-season")]
for p in posts:
    p.setdefault("kind", "analysis")
posts += [
    dict(title="Why the decline curve runs low: wells that bounce back", slug="recovery-low-forecasts", date=PUB, kind="analysis", thumb="recovery",
         summary="About 35 to 50% of wells recover after the training window. A low month just before the forecast multiplies the typical miss by two to five, but does not explain all of it."),
    dict(title="Gas has a season. Oil mostly doesn't.", slug="gas-has-a-season", date=PUB, kind="analysis", thumb="season",
         summary="Alberta and BC gas run 6 to 10% above trend in winter and below it through summer and early autumn. Oil barely moves with the calendar."),
]
for i, m in enumerate(SNAPS):
    y, mo = int(m[:4]), int(m[5:]); name = f"{MONTHS[mo - 1]} {y}"
    pm, ly = prev_month(m, 1), prev_month(m, 12)
    trs, moves, yoys = [], [], []
    for gname, p, pr in GROUPS:
        v = vol[(p, pr)]
        mom, yoy = 100 * (v[m] / v[pm] - 1), 100 * (v[m] / v[ly] - 1)
        if gname != "BC oil":   # tiny and noisy, so left out of the headline sentences
            moves.append((abs(mom), gname, mom)); yoys.append((yoy, gname))
        trs.append(f"<tr><td>{gname}</td><td>{fmt(v[m], pr)}</td><td>{pct(mom, 1)}</td><td>{pct(yoy, 1)}</td><td>{wells[(p, pr)][m]:,}</td></tr>")
    moves.sort(reverse=True); yoys.sort()
    big = moves[0]
    ag_s, bg_s = AVG[("AB", "GAS")][mo], AVG[("BC", "GAS")][mo]
    prev_l = f'<a href="snapshot-{SNAPS[i - 1]}.html">&larr; {MONTHS[int(SNAPS[i - 1][5:]) - 1]} {SNAPS[i - 1][:4]}</a>' if i else ""
    next_l = f'<a href="snapshot-{SNAPS[i + 1]}.html">{MONTHS[int(SNAPS[i + 1][5:]) - 1]} {SNAPS[i + 1][:4]} &rarr;</a>' if i + 1 < len(SNAPS) else ""
    sdate = OLD.get(f"snapshot-{m}", TODAY)
    dlm = f"{MONTHS[int(sdate[5:7]) - 1]} {sdate[:4]}"
    pubchip = "Published retrospectively, November 2026" if m <= "2026-09" else f"Published {dlm}"
    body = f'''<h1>Monthly snapshot: {name}</h1>
<p><span class="chip">Data month: {name}</span><span class="chip">{pubchip}</span><span class="chip">Illustrative</span></p>
<p>Average daily production reported for {name} in the public well-level files for Alberta and Saskatchewan (Petrinex) and BC (BC Energy Regulator), compared with the previous month and with {MONTHS[mo - 1]} {y - 1}. Rates are monthly volume divided by calendar days, so month length does not distort the comparison.</p>
<div class="tw"><table><tr><th>Group</th><th>Average rate</th><th>vs {MONTHS[int(pm[5:]) - 1][:3]} {pm[:4]}</th><th>vs {SHORT[mo - 1]} {y - 1}</th><th>Wells producing</th></tr>{"".join(trs)}</table></div>
<p><small>Rates: thousand bbl/d for oil, MMcf/d for gas. "Wells producing" counts well rows with volume above zero in the month. Oil and gas rows for the same well are counted separately.</small></p>
{fig(mini_panels(m), f"<b>Figure.</b> Average daily rate by group, January 2022 to {name}. The dot marks {name}. Real data from the same files.")}
<h2>What stands out</h2>
<ul><li>Biggest move from the previous month (BC oil excluded, it is small and noisy): <b>{big[1]}</b> at {pct(big[2], 1)}.</li><li>Compared with a year earlier, {yoys[-1][1]} was highest at {pct(yoys[-1][0], 1)} and {yoys[0][1]} lowest at {pct(yoys[0][0], 1)}.</li><li>Seasonal context: in 2022 to 2025, {MONTHS[mo - 1]} was typically {pct(ag_s, 1)} against trend for Alberta gas and {pct(bg_s, 1)} for BC gas (see <a href="gas-has-a-season.html">Gas has a season</a>), so part of a gas move in {MONTHS[mo - 1]} is the calendar.</li></ul>
<h2>Notes</h2>
<ul><li>These are sums of public well-level rows, not official provincial statistics. Rows with masked well IDs would be left out; none were present in the files we used.</li><li>Figures come from files downloaded in {dlm}; operators can revise earlier months, so numbers here may differ from what was first reported at the time.</li><li>This page reports what the data shows and does not explain causes.</li><li>Alberta oil includes crude bitumen from wells licensed for it (about three quarters of the oil-product volume over the last 12 months; see <a href="licensed-vs-producing.html">the inventory post</a>).</li></ul>
<p>{prev_l}{" &nbsp;·&nbsp; " if prev_l and next_l else ""}{next_l}</p>
<p>Code: <a href="https://github.com/Jay-Kimani/TidyWells">github.com/Jay-Kimani/TidyWells</a>, <code>posts/monthly_agg.py</code> and <code>posts/gen_posts.py</code>. Illustrative only, not for reserves reporting or investment decisions.</p>{LICENCE}'''
    page(f"snapshot-{m}", f"Monthly snapshot: {name}", body)
    v = vol
    summ = (f"Alberta oil averaged {fmt(v[('AB', 'OIL')][m], 'OIL')} thousand bbl/d ({pct(100 * (v[('AB', 'OIL')][m] / v[('AB', 'OIL')][ly] - 1), 1)} on a year earlier); "
            f"Alberta gas {fmt(v[('AB', 'GAS')][m], 'GAS')} MMcf/d ({pct(100 * (v[('AB', 'GAS')][m] / v[('AB', 'GAS')][ly] - 1), 1)}); BC gas {fmt(v[('BC', 'GAS')][m], 'GAS')} MMcf/d.")
    posts.append(dict(title=f"Monthly snapshot: {name}", slug=f"snapshot-{m}", date=sdate, period=m, kind="snapshot", summary=summ))
(ROOT / "posts" / "posts.json").write_text(json.dumps(posts, indent=2), encoding="utf-8")
print(len(posts), "posts")


# ---------- thumbnails for the two analysis posts ----------
def thumb_season():
    W, H, x0, x1, y0, y1 = 240, 140, 30, 230, 14, 104
    lo, hi = -12, 12
    X = lambda i: x0 + (x1 - x0) * i / 11
    Y = lambda v: y1 - (y1 - y0) * (v - lo) / (hi - lo)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Alberta gas and oil distance from trend by calendar month">']
    for v in (-10, 0, 10):
        o.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" stroke="var(--line)" stroke-width="{1.1 if v == 0 else .6}"/>'
                 f'<text x="{x0 - 4}" y="{Y(v) + 3:.1f}" font-size="8.5" text-anchor="end" fill="var(--muted)" {F}>{v:+d}%</text>')
    for n, col in (("Alberta oil", "var(--fg)"), ("Alberta gas", "var(--accent)")):
        a = AVG[key[n]]
        o.append(f'<polyline points="{" ".join(f"{X(m - 1):.1f},{Y(a[m]):.1f}" for m in range(1, 13))}" fill="none" stroke="{col}" stroke-width="{2.4 if "gas" in n else 1.8}" stroke-linejoin="round"/>')
    for m in (1, 4, 7, 10):
        o.append(f'<text x="{X(m - 1):.1f}" y="{y1 + 12}" font-size="8.5" text-anchor="middle" fill="var(--muted)" {F}>{SHORT[m - 1]}</text>')
    o.append(f'<text x="{x0}" y="{y1 + 26}" font-size="8.5" fill="var(--muted)" {F}>vs 12-month trend, 2022-25 · <tspan fill="var(--accent)">&#9473; gas</tspan> <tspan fill="var(--fg)">&#9473; oil</tspan></text></svg>')
    return "".join(o)


def thumb_recovery():
    W, H, x0, y0, y1 = 240, 140, 30, 14, 104
    Y = lambda v: y0 + (y1 - y0) * (-v) / 50
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Median forecast error with and without a low month before the forecast">']
    for v in (0, -20, -40):
        o.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{W - 8}" y2="{Y(v):.1f}" stroke="var(--line)" stroke-width=".6"/>'
                 f'<text x="{x0 - 4}" y="{Y(v) + 3:.1f}" font-size="8.5" text-anchor="end" fill="var(--muted)" {F}>{v}%</text>')
    gw = (W - 8 - x0) / 4
    for i, (k, n) in enumerate(ORDER):
        gx = x0 + gw * i + gw / 2
        for j, (kk, col) in enumerate((("err_nodip", "var(--accent)"), ("err_dip", "#e0a458"))):
            v = R[k][kk]
            o.append(f'<rect x="{gx - 17 + j * 17:.1f}" y="{Y(0):.1f}" width="15" height="{Y(v) - Y(0):.1f}" rx="2" fill="{col}"/>')
        o.append(f'<text x="{gx:.1f}" y="{y1 + 12}" font-size="8" text-anchor="middle" fill="var(--muted)" {F}>{n.split()[0][:3] if n != "BC gas" else "BC"} {n.split()[-1]}</text>')
    o.append(f'<text x="{x0}" y="{y1 + 26}" font-size="8.5" fill="var(--muted)" {F}>median error · <tspan fill="var(--accent)">&#9632; no low month</tspan> <tspan fill="#e0a458">&#9632; low month</tspan></text></svg>')
    return "".join(o)


(ROOT / "posts" / "thumb_season.svg").write_text(thumb_season())
(ROOT / "posts" / "thumb_recovery.svg").write_text(thumb_recovery())
