"""Second batch of analysis posts (inventory vs producing, shut-ins, new-well vintage, licensee concentration,
gas-oil ratio, data quality) from posts/study.json and posts/dq.json. Run after posts/gen_posts.py (it imports it).
    python posts/gen_posts2.py && python posts/build_feed.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_posts as g  # noqa: E402  (regenerates the first batch too)

ROOT, F, page, fig, pct, LICENCE, PUB = g.ROOT, g.F, g.page, g.fig, g.pct, g.LICENCE, g.PUB
S = json.loads((ROOT / "posts" / "study.json").read_text())
DQ = json.loads((ROOT / "posts" / "dq.json").read_text())
AB, SK, BC = S["AB"], S["SK"], S["BC"]
PAL = ["#6aa6f0", "#5fd0c0", "#e0a458", "#d98bb0", "#b9a3f0"]
n0 = lambda x: f"{x:,.0f}"
CHIPS = '<p><span class="chip">November 2026</span><span class="chip">Illustrative, not for reserves or investment decisions</span></p>'
REPRO = ('<h2>Reproduce it</h2><p>Code: <a href="https://github.com/Jay-Kimani/TidyWells">github.com/Jay-Kimani/TidyWells</a>, '
         '<code>posts/cache_matrix.py</code>, <code>posts/wells_study.py</code>, <code>posts/dq_study.py</code> and <code>posts/gen_posts2.py</code>. '
         'Download the files yourself from Petrinex and the BC Energy Regulator; we do not host the data.</p>'
         '<p>Illustrative only. Not for reserves reporting or investment decisions.</p>')


# ---------------- chart helpers ----------------
def nice_ticks(lo, hi, n=5):
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 5, 10) if m * mag >= raw)
    t, out = math.ceil(lo / step) * step, []
    while t <= hi + 1e-9:
        out.append(round(t, 10)); t += step
    return out


def chart(series, xl, W=720, H=300, ylab="", yfmt=lambda v: f"{v:g}", lo=None, hi=None, right=150):
    x0, x1, y0, y1 = 70, W - right, 16, H - 46
    allv = [v for s in series for v in s[1] if v is not None]
    lo = min(allv) if lo is None else lo
    hi = max(allv) if hi is None else hi
    pad = (hi - lo) * 0.06
    lo2, hi2 = lo - (pad if lo is None else 0), hi + pad
    n = len(xl)
    X = lambda i: x0 + (x1 - x0) * i / (n - 1)
    Y = lambda v: y1 - (y1 - y0) * (v - lo2) / (hi2 - lo2)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{ylab}">']
    for t in nice_ticks(lo2, hi2):
        o.append(f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{x1}" y2="{Y(t):.1f}" stroke="var(--line)" stroke-width=".7"/>'
                 f'<text x="{x0 - 8}" y="{Y(t) + 4:.1f}" font-size="11.5" text-anchor="end" fill="var(--muted)" {F}>{yfmt(t)}</text>')
    for i, lab in enumerate(xl):
        if lab:
            o.append(f'<text x="{X(i):.1f}" y="{y1 + 18}" font-size="11.5" text-anchor="middle" fill="var(--muted)" {F}>{lab}</text>')
    o.append(f'<text x="12" y="{(y0 + y1) / 2}" font-size="11.5" text-anchor="middle" fill="var(--muted)" transform="rotate(-90 12 {(y0 + y1) / 2})" {F}>{ylab}</text>')
    ends = []
    for s in series:
        name, vals, col = s[:3]
        dash = s[3] if len(s) > 3 else ""
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals) if v is not None)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.4" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
        last = max(i for i, v in enumerate(vals) if v is not None)
        ends.append((Y(vals[last]), name, col))
    ends.sort(); prev = -99
    for yy, name, col in ends:
        yy = max(yy, prev + 15); prev = yy
        o.append(f'<text x="{x1 + 10}" y="{yy + 4:.1f}" font-size="12" fill="{col}" {F}>{name}</text>')
    return "".join(o) + "</svg>"


def gbars(cats, series, ylab="", yfmt=lambda v: f"{v:g}", W=720, H=320, hi=None):
    x0, y0, y1 = 70, 18, H - 80
    hi = hi or max(v for s in series for v in s[1]) * 1.12
    Y = lambda v: y1 - (y1 - y0) * v / hi
    gw = (W - x0 - 14) / len(cats)
    k = len(series)
    bw = min(34, (gw - 14) / k)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{ylab}">']
    for t in nice_ticks(0, hi):
        o.append(f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{W - 14}" y2="{Y(t):.1f}" stroke="var(--line)" stroke-width=".7"/>'
                 f'<text x="{x0 - 8}" y="{Y(t) + 4:.1f}" font-size="11.5" text-anchor="end" fill="var(--muted)" {F}>{yfmt(t)}</text>')
    for i, c in enumerate(cats):
        gx = x0 + gw * i + gw / 2
        for j, (name, vals, col) in enumerate(series):
            bx = gx - bw * k / 2 + j * bw
            o.append(f'<rect x="{bx:.1f}" y="{Y(vals[i]):.1f}" width="{bw - 3:.1f}" height="{y1 - Y(vals[i]):.1f}" rx="2" fill="{col}"/>')
        o.append(f'<text x="{gx:.1f}" y="{y1 + 16}" font-size="11" text-anchor="middle" fill="var(--muted)" {F}>{c}</text>')
    o.append(f'<text x="12" y="{(y0 + y1) / 2}" font-size="11.5" text-anchor="middle" fill="var(--muted)" transform="rotate(-90 12 {(y0 + y1) / 2})" {F}>{ylab}</text>')
    lx = x0
    for name, _, col in series:
        o.append(f'<rect x="{lx}" y="{H - 24}" width="12" height="12" rx="2" fill="{col}"/><text x="{lx + 18}" y="{H - 14}" font-size="12" fill="var(--fg)" {F}>{name}</text>')
        lx += 30 + 7.2 * len(name)
    return "".join(o) + "</svg>"


def hbars(items, W=720, label_w=150):
    """items: (label, total, part). Grey bar = total, accent = part (producing)."""
    rh = 30
    H = rh * len(items) + 40
    x0, x1 = label_w, W - 215
    mx = max(t for _, t, _ in items)
    X = lambda v: x0 + (x1 - x0) * math.sqrt(v / mx)      # square-root scale so small groups stay visible
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Wells by status and how many produced in the last 12 months">']
    for i, (lab, t, p) in enumerate(items):
        y = 12 + i * rh
        o.append(f'<text x="{x0 - 10}" y="{y + 14}" font-size="12.5" text-anchor="end" fill="var(--fg)" {F}>{lab}</text>'
                 f'<rect x="{x0}" y="{y + 2}" width="{max(X(t) - x0, 1.5):.1f}" height="18" rx="3" fill="var(--line)"/>'
                 f'<rect x="{x0}" y="{y + 2}" width="{max(X(p) - x0, 0 if p == 0 else 1.5):.1f}" height="18" rx="3" fill="var(--accent)"/>'
                 f'<text x="{X(t) + 8:.1f}" y="{y + 15}" font-size="11.5" fill="var(--muted)" {F}>{n0(t)} · {100 * p / t:.0f}% producing</text>')
    o.append(f'<rect x="{x0}" y="{H - 20}" width="12" height="12" rx="2" fill="var(--line)"/><text x="{x0 + 18}" y="{H - 10}" font-size="12" fill="var(--fg)" {F}>wells listed</text>'
             f'<rect x="{x0 + 110}" y="{H - 20}" width="12" height="12" rx="2" fill="var(--accent)"/><text x="{x0 + 128}" y="{H - 10}" font-size="12" fill="var(--fg)" {F}>reported production, last 12 months</text></svg>')
    return "".join(o)


def thumb_frame(inner, cap):
    return (f'<svg viewBox="0 0 240 140" role="img" aria-label="{cap}">{inner}'
            f'<text x="30" y="132" font-size="8.5" fill="var(--muted)" {F}>{cap}</text></svg>')


def mini_lines(series, lo, hi, cap, ylab=lambda v: f"{v:g}", ticks=3):
    x0, x1, y0, y1 = 30, 230, 12, 104
    n = len(series[0][1])
    X = lambda i: x0 + (x1 - x0) * i / (n - 1)
    Y = lambda v: y1 - (y1 - y0) * (v - lo) / (hi - lo)
    o = ""
    for t in nice_ticks(lo, hi, ticks):
        o += f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{x1}" y2="{Y(t):.1f}" stroke="var(--line)" stroke-width=".6"/><text x="{x0 - 4}" y="{Y(t) + 3:.1f}" font-size="8.5" text-anchor="end" fill="var(--muted)" {F}>{ylab(t)}</text>'
    for name, vals, col in series:
        o += f'<polyline points="{" ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>'
    return thumb_frame(o, cap)


def mini_bars(cats, series, cap, hi=None):
    x0, x1, y0, y1 = 30, 230, 12, 104
    hi = hi or max(v for s in series for v in s[1]) * 1.1
    gw = (x1 - x0) / len(cats)
    bw = min(16, (gw - 4) / len(series))
    o = f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="var(--line)"/>'
    for i, c in enumerate(cats):
        gx = x0 + gw * i + gw / 2
        for j, (n, vals, col) in enumerate(series):
            h = (y1 - y0) * vals[i] / hi
            o += f'<rect x="{gx - bw * len(series) / 2 + j * bw:.1f}" y="{y1 - h:.1f}" width="{bw - 2:.1f}" height="{h:.1f}" rx="2" fill="{col}"/>'
        o += f'<text x="{gx:.1f}" y="{y1 + 11}" font-size="8" text-anchor="middle" fill="var(--muted)" {F}>{c}</text>'
    return thumb_frame(o, cap)


MONTHLBL = lambda n, start=0: [str(2022 + (start + i) // 12) if (start + i) % 12 == 0 else "" for i in range(n)]
posts_new = []


def add(slug, title, summary, body, thumb_svg):
    page(slug, title, body)
    (ROOT / "posts" / f"thumb_{slug}.svg").write_text(thumb_svg)
    posts_new.append(dict(title=title, slug=slug, date=g.OLD.get(slug, g.TODAY), kind="analysis", thumb=slug, summary=summary))


# =====================================================================
# 1. Inventory vs producing
# =====================================================================
ai, si = AB["inventory"], SK["inventory"]
bit = AB["bitumen"]
st_items = [(r["status"].replace("(blank)", "(blank status)"), r["n"], r["producing"]) for r in ai["by_status"]] + [("all other", ai["other_n"], ai["other_producing"])]
sk_items = [(r["status"].replace("(blank)", "(blank status)"), r["n"], r["producing"]) for r in si["by_status"][:6]] + [("all other", si["total"] - sum(r["n"] for r in si["by_status"][:6]), si["producing_last12"] - sum(r["producing"] for r in si["by_status"][:6]))]
ab_prod_status = {r["status"]: r for r in ai["by_status"]}
flow, pump = ab_prod_status["FLOW"], ab_prod_status["PUMP"]
body = f'''<h1>Most licensed wells aren't producing</h1>{CHIPS}
<p>"Alberta has 668,000 wells" is a common line, and it is true of the regulator's well file. It is a poor guide to how many wells make anything. We matched the Well Infrastructure files for Alberta and Saskatchewan against the production files, and counted which wells reported production in the last 12 months (October 2025 to September 2026).</p>
<h2>1. The headline</h2>
<div class="tw"><table><tr><th>Province</th><th>Wells in the infrastructure file</th><th>Reported production, last 12 months</th><th>Share</th></tr>
<tr><td>Alberta</td><td>{n0(ai["total"])}</td><td>{n0(ai["producing_last12"])}</td><td>{100 * ai["producing_last12"] / ai["total"]:.0f}%</td></tr>
<tr><td>Saskatchewan</td><td>{n0(si["total"])}</td><td>{n0(si["producing_last12"])}</td><td>{100 * si["producing_last12"] / si["total"]:.0f}%</td></tr></table></div>
<p><small>"Producing" means a positive oil or gas volume in at least one of the last 12 months in the public production files. Injection and disposal wells are not production wells.</small></p>
<p>About one well in five in Alberta, and one in four in Saskatchewan, reported production in the past year. The rest are abandoned, suspended, being drilled, injectors or simply idle.</p>
<h2>2. What the status field says</h2>
{fig(hbars(st_items), "<b>Figure 1.</b> Alberta wells by status in the infrastructure file, and how many reported production in the last 12 months. Bar length is on a square-root scale so small groups stay visible. Real data.")}
<p>The status codes are a good guide where they exist. Wells listed as flowing or pumping reported production {100 * flow["producing"] / flow["n"]:.0f}% and {100 * pump["producing"] / pump["n"]:.0f}% of the time; suspended and abandoned wells almost never did. But {n0(ai["blank_producing"])} wells with a <i>blank</i> status did report production, so filtering on status alone would drop them.</p>
{fig(hbars(sk_items, label_w=130), "<b>Figure 2.</b> The same view for Saskatchewan. Real data.")}
<h2>3. What is inside Alberta's "oil"</h2>
<p>Of Alberta's {n0(ai["producing_last12"])} producing wells, {n0(bit["producing_wells_bitumen"])} ({100 * bit["producing_wells_bitumen"] / ai["producing_last12"]:.0f}%) are licensed for crude bitumen, yet those wells account for about {bit["oil_volume_share_bitumen"]:.0f}% of the oil-product volume they reported over the last 12 months. In other words, a total labelled "Alberta oil" in the public volumetrics is mostly bitumen. That matters for every other post on this site: our Alberta oil numbers mix conventional oil and bitumen wells, and we did not separate them.</p>
<h2>What this means in practice</h2>
<ul><li>When you count wells, say which definition you mean: licensed, drilled, or reported production in a period.</li><li>Do not use status alone to find producers; check the production files too.</li><li>For Alberta oil volumes, remember the bitumen share. If you want conventional oil only, filter by the licence substance.</li></ul>
<h2>Limits</h2>
<ul><li>Counts are as of the files we downloaded in November 2026 and will drift.</li><li>The public production files do not cover every well type, so some real producers may be missing from the "producing" count.</li><li>A well that produced only briefly, or reported a tiny volume, counts the same as a large one.</li><li>"Bitumen" here means the licence substance, and the volume share compares the oil-product volumes of wells with that licence substance against all wells.</li></ul>{REPRO}{LICENCE}'''
add("licensed-vs-producing", "Most licensed wells aren't producing",
    f"Alberta's well file lists about {n0(round(ai['total'], -3))} wells and about {n0(round(ai['producing_last12'], -3))} reported production in the last year. Saskatchewan: {n0(round(si['total'], -3))} and {n0(round(si['producing_last12'], -3))}.",
    body, thumb_frame(
        "".join(f'<rect x="30" y="{y}" width="{w1:.1f}" height="22" rx="3" fill="var(--line)"/><rect x="30" y="{y}" width="{w2:.1f}" height="22" rx="3" fill="var(--accent)"/>'
                f'<text x="30" y="{y + 36}" font-size="9" fill="var(--muted)" {F}>{nm}</text>'
                for y, w1, w2, nm in ((16, 200, 200 * ai["producing_last12"] / ai["total"], f"Alberta {100 * ai['producing_last12'] / ai['total']:.0f}% producing"),
                                      (68, 200 * si["total"] / ai["total"], 200 * si["producing_last12"] / ai["total"], f"Sask. {100 * si['producing_last12'] / si['total']:.0f}%"))),
        "wells listed vs producing, last 12 months"))

# =====================================================================
# 2. Shut-ins and restarts
# =====================================================================
sa, ss, sb = AB["shutins"], SK["shutins"], BC["shutins"]
months = len(sa["cohort_survival"])
lab = MONTHLBL(months)
f1 = chart([("Alberta", sa["cohort_survival"], PAL[0]), ("Saskatchewan", ss["cohort_survival"], PAL[1]), ("BC", sb["cohort_survival"], PAL[2])],
           lab, ylab="still producing", yfmt=lambda v: f"{v:g}%", lo=65, hi=100)
rs, sp = sa["restart_pct"][9:], sa["stop_pct"][9:]      # from January 2023: restarts need earlier production inside the window
lab2 = MONTHLBL(len(rs), 12)
f2 = chart([("Stops", sp, PAL[3]), ("Restarts", rs, PAL[0])], lab2, ylab="% of producing wells, per month", yfmt=lambda v: f"{v:g}%", lo=0)
mean = lambda x: sum(x) / len(x)
SHORT = g.SHORT
mon_stop = {}
for i, v in enumerate(sp):
    mon_stop.setdefault((i + 12) % 12, []).append(v)
mon_rs = {}
for i, v in enumerate(rs):
    mon_rs.setdefault((i + 12) % 12, []).append(v)
top_stop = max(mon_stop, key=lambda k: mean(mon_stop[k])); top_rs = max(mon_rs, key=lambda k: mean(mon_rs[k]))
gb = lambda s: s["gap_buckets"]
body = f'''<h1>Shut-ins and restarts: how many wells stop, and do they come back?</h1>{CHIPS}
<p>Production files only show wells that are producing, so a well that stops simply disappears from the data. Here we follow wells month by month to see how many stop, how often a stop is temporary, and how long the gaps last. A well counts as producing in a month if it reported a positive oil or gas volume.</p>
<h2>1. Wells that were producing in January 2022</h2>
{fig(f1, f"<b>Figure 1.</b> Share of the wells that produced in January 2022 that were still producing in each later month. Real data: Alberta {n0(sa['cohort_n'])} wells, Saskatchewan {n0(ss['cohort_n'])}, BC {n0(sb['cohort_n'])}.")}
<p>By September 2026, {sa["cohort_survival"][-1]:.0f}% of the Alberta group, {ss["cohort_survival"][-1]:.0f}% of Saskatchewan and {sb["cohort_survival"][-1]:.0f}% of BC were still reporting production. The curves are not smooth declines: they wobble as wells stop and come back.</p>
<h2>2. How common are interruptions?</h2>
<div class="tw"><table><tr><th>Province</th><th>Wells that ever produced</th><th>Not producing in the last 6 months</th><th>Interrupted at least once (3+ months)</th></tr>
<tr><td>Alberta</td><td>{n0(sa["ever"])}</td><td>{n0(sa["stopped_6m"])} ({100 * sa["stopped_6m"] / sa["ever"]:.0f}%)</td><td>{n0(sa["interrupted_wells"])} ({sa["interrupted_share"]:.0f}%)</td></tr>
<tr><td>Saskatchewan</td><td>{n0(ss["ever"])}</td><td>{n0(ss["stopped_6m"])} ({100 * ss["stopped_6m"] / ss["ever"]:.0f}%)</td><td>{n0(ss["interrupted_wells"])} ({ss["interrupted_share"]:.0f}%)</td></tr>
<tr><td>BC</td><td>{n0(sb["ever"])}</td><td>{n0(sb["stopped_6m"])} ({100 * sb["stopped_6m"] / sb["ever"]:.0f}%)</td><td>{n0(sb["interrupted_wells"])} ({sb["interrupted_share"]:.0f}%)</td></tr></table></div>
<p><small>"Interrupted" = three or more consecutive months with no production between a well's first and last producing month. Wells that stopped and never restarted are not counted as interrupted.</small></p>
<p>Roughly one well in ten in Alberta and Saskatchewan had at least one gap of three months or more, and BC shows about three in ten. BC's file reports a row for every well and zone with producing days, so zero months are visible there, which may make interruptions easier to see; we would not read the difference as BC wells being less reliable.</p>
<h2>3. How long do the gaps last?</h2>
<div class="tw"><table><tr><th>Province</th><th>3 to 5 months</th><th>6 to 11 months</th><th>12 to 23 months</th><th>24 months or more</th></tr>
<tr><td>Alberta</td><td>{n0(gb(sa)["m3_5"])}</td><td>{n0(gb(sa)["m6_11"])}</td><td>{n0(gb(sa)["m12_23"])}</td><td>{n0(gb(sa)["m24plus"])}</td></tr>
<tr><td>Saskatchewan</td><td>{n0(gb(ss)["m3_5"])}</td><td>{n0(gb(ss)["m6_11"])}</td><td>{n0(gb(ss)["m12_23"])}</td><td>{n0(gb(ss)["m24plus"])}</td></tr>
<tr><td>BC</td><td>{n0(gb(sb)["m3_5"])}</td><td>{n0(gb(sb)["m6_11"])}</td><td>{n0(gb(sb)["m12_23"])}</td><td>{n0(gb(sb)["m24plus"])}</td></tr></table></div>
<p><small>Number of gaps (a well can have more than one), not number of wells.</small></p>
<p>Among the idle spells that ended with a restart, most were short. In Alberta, {100 * gb(sa)["m3_5"] / sum(gb(sa).values()):.0f}% were under six months and only {100 * gb(sa)["m24plus"] / sum(gb(sa).values()):.0f}% lasted two years or more. Wells that stopped and never came back are not in this table, so it says how long restarts take, not how likely they are.</p>
<h2>4. Stops and restarts through time</h2>
{fig(f2, "<b>Figure 2.</b> Alberta: wells that stopped (no production for the next three months) and wells that restarted (producing after at least three idle months), each as a share of wells producing the month before. Real data.")}
<p>From January 2023, in an average month about {mean(sp):.1f}% of producing Alberta wells stopped and about {mean(rs):.1f}% restarted (restarts cannot be seen in 2022 because we need earlier production inside the window). Stops were most common in {SHORT[top_stop - 1 if top_stop else 11]} on average and restarts in {SHORT[top_rs - 1 if top_rs else 11]}; with under five years of data we would not call that a pattern.</p>
<h2>What this means in practice</h2>
<ul><li>A well missing from a month's data is sometimes back soon: among wells that did restart, most idle spells were under six months.</li><li>Counts of "producing wells" move around by a percent or so a month for reasons that have nothing to do with drilling.</li><li>When you build a decline curve, expect a few wells in ten to have gaps that a smooth curve will not capture. See the <a href="recovery-low-forecasts.html">recovery post</a>.</li></ul>
<h2>Limits</h2>
<ul><li>A "stop" here is a lack of reported production; it could be a shut-in, a sale, a reporting gap or a change of well ID.</li><li>The window is January 2022 to September 2026, so wells that stopped before 2022 are not in the January 2022 group.</li><li>The last three months of the window cannot be checked for restarts, and wells that stopped near the end may still return.</li></ul>{REPRO}{LICENCE}'''
add("shut-ins-and-restarts", "Shut-ins and restarts: how many wells stop, and do they come back?",
    f"Of the wells producing in January 2022, {sa['cohort_survival'][-1]:.0f}% in Alberta, {ss['cohort_survival'][-1]:.0f}% in Saskatchewan and {sb['cohort_survival'][-1]:.0f}% in BC were still producing in September 2026; about one well in ten had a gap of three months or more.",
    body, mini_lines([("AB", sa["cohort_survival"], PAL[0]), ("SK", ss["cohort_survival"], PAL[1]), ("BC", sb["cohort_survival"], PAL[2])], 65, 100,
                     "still producing, Jan 2022 cohort", ylab=lambda v: f"{v:g}%"))

# =====================================================================
# 3. New wells by vintage
# =====================================================================
def vint(prov, cls):
    return {x["year"]: x for x in prov["vintage"]["groups"] if x["cls"] == cls}
va_o, va_g, vs_o, vs_g = vint(AB, "oil"), vint(AB, "gas"), vint(SK, "oil"), vint(SK, "gas")
YR = [2022, 2023, 2024, 2025]
idx = lambda d: [100 * d[y]["median"] / d[2022]["median"] for y in YR]
f1 = chart([("Alberta oil", idx(va_o), PAL[3]), ("Alberta gas", idx(va_g), PAL[0]), ("Saskatchewan oil", idx(vs_o), PAL[1])],
           [str(y) for y in YR], ylab="median first-6-month rate (2022 = 100)", yfmt=lambda v: f"{v:g}", lo=80, hi=150, right=160)
trs = ""
for pn, dd, unit in (("Alberta oil", va_o, "bbl/d"), ("Alberta gas", va_g, "Mcf/d"), ("Saskatchewan oil", vs_o, "bbl/d")):
    trs += f'<tr><td>{pn} ({unit})</td>' + "".join((f'<td>{dd[y]["median"]:,.0f} <small>(n {dd[y]["n"]:,})</small></td>' if y in dd else "<td>n/a</td>") for y in (2022, 2023, 2024, 2025, 2026)) + "</tr>"
hz = AB["vintage"]["by_drill"]
body = f'''<h1>Are new wells getting better? First-six-month rates by year</h1>{CHIPS}
<p class="muted"><b>Correction, 4 November 2026.</b> An earlier version of this post sorted wells into "oil" and "gas" with a rule that labelled most Alberta and Saskatchewan oil wells that also produce gas as gas wells. That mixed the groups and its headline (Alberta gas wells starting 19% stronger) was wrong. The numbers and conclusions below use a corrected rule.</p>
<p>Drillers talk about better completions and longer laterals. If that is working, wells that start producing later should start stronger. We looked at the first six producing months of new wells in Alberta and Saskatchewan, grouped by the year they first produced.</p>
<h2>What we did</h2>
<ul><li><b>New wells:</b> spud date in 2021 or later, and not already producing in January 2022, so older wells returning from a shut-in are left out.</li><li><b>Measure:</b> average daily rate over each well's first six producing months (oil in bbl/d, gas in Mcf/d). A well is "oil" if oil is at least half of its output on an energy basis (6 Mcf of gas counts as 1 bbl), otherwise "gas". We report medians.</li><li><b>Groups:</b> by the calendar year of the first producing month. Groups with fewer than 30 wells are dropped.</li></ul>
<h2>1. Newer Alberta oil wells start stronger; gas is noisier; Saskatchewan oil edges up</h2>
{fig(f1, "<b>Figure 1.</b> Median first-six-month rate for wells that first produced in each year, with 2022 set to 100. Real data; counts in the table below.")}
<div class="tw"><table><tr><th>Group (median)</th><th>2022</th><th>2023</th><th>2024</th><th>2025</th><th>2026 (first produced Jan to Mar)</th></tr>{trs}</table></div>
<p>Alberta oil wells that first produced in 2025 started at a median of {va_o[2025]["median"]:,.0f} bbl/d against {va_o[2022]["median"]:,.0f} in 2022, a rise of {100 * (va_o[2025]["median"] / va_o[2022]["median"] - 1):.0f}%, and the median rose in every year in between. Alberta gas wells moved from {va_g[2022]["median"]:,.0f} to {va_g[2025]["median"]:,.0f} Mcf/d ({100 * (va_g[2025]["median"] / va_g[2022]["median"] - 1):+.0f}%), but not steadily: the 2024 group was the highest at {va_g[2024]["median"]:,.0f}. Saskatchewan oil went from {vs_o[2022]["median"]:,.0f} to {vs_o[2025]["median"]:,.0f} bbl/d ({100 * (vs_o[2025]["median"] / vs_o[2022]["median"] - 1):+.0f}%). Saskatchewan has too few new gas wells under this rule to report (fewer than 30 in every year but one).</p>
<h2>2. Horizontal wells dominate new Alberta wells</h2>
<p>Among new Alberta wells, {hz["oil_horizontal"]["n"]:,} oil wells and {hz["gas_horizontal"]["n"]:,} gas wells are flagged horizontal in the infrastructure file, against only {hz["oil_other"]["n"]:,} and {hz["gas_other"]["n"]:,} that are not. The horizontal wells started at a median of {hz["oil_horizontal"]["median"]:,.0f} bbl/d (oil) and {hz["gas_horizontal"]["median"]:,.0f} Mcf/d (gas), against {hz["oil_other"]["median"]:,.0f} bbl/d and {hz["gas_other"]["median"]:,.0f} Mcf/d for the others. The rise from year to year is probably linked to what is being drilled, but this data cannot separate lateral length, completion size or location.</p>
<h2>What this means in practice</h2>
<ul><li>Do not forecast a 2025 Alberta oil well with a 2022 type curve; the median start is well above it.</li><li>Alberta gas starts are noisy from year to year, so one year's median is a weak basis for a type curve.</li><li>For Saskatchewan oil, older type curves are modestly low for newer wells.</li><li>Check horizontal versus vertical before comparing groups of wells.</li></ul>
<h2>Limits</h2>
<ul><li>Medians only; we did not adjust for lateral length, completion size, fluid mix or location.</li><li>The "oil" group in Alberta includes wells licensed for crude bitumen. The oil-or-gas rule is a simple energy cut-off; wells near it can be either, and condensate-rich gas wells are treated by their oil and gas volumes as reported.</li><li>First six months include any ramp-up and can be affected by early shut-ins.</li><li>2026 holds only wells that first produced in January to March, and groups under 30 wells are not shown.</li><li>A well drilled in 2021 or later but producing before 2022 is excluded, which removes some of the earliest 2022 starts.</li></ul>{REPRO}{LICENCE}'''
add("new-wells-by-vintage", "Are new wells getting better? First-six-month rates by year",
    f"Alberta oil wells that first produced in 2025 started {100 * (va_o[2025]['median'] / va_o[2022]['median'] - 1):.0f}% stronger than 2022 starters at the median; Alberta gas is noisier and Saskatchewan oil edged up. Corrected 4 November 2026.",
    body, mini_lines([("AO", idx(va_o), PAL[3]), ("AG", idx(va_g), PAL[0]), ("SO", idx(vs_o), PAL[1])], 80, 150,
                     "median first-6-month rate, 2022 = 100"))

# =====================================================================
# 4. Concentration
# =====================================================================
oa, os_ = AB["operators"], SK["operators"]
labs = [("1" if i == 0 else str(i + 1) if (i + 1) in (10, 25, 50, 75, 100) else "") for i in range(100)]
f1 = chart([("Alberta wells", oa["curve_wells"], PAL[0]), ("Alberta oil volume", oa["curve_oil"], PAL[3]),
            ("Saskatchewan wells", os_["curve_wells"], PAL[1]), ("Saskatchewan oil volume", os_["curve_oil"], PAL[2])],
           labs, ylab="share held by the top licensees", yfmt=lambda v: f"{v:g}%", lo=0, hi=100, right=185)
rows_t = ""
for nm, o in (("Alberta", oa), ("Saskatchewan", os_)):
    for n in ("1", "5", "10", "20", "50"):
        rows_t += f'<tr><td>{nm}, top {n}</td><td>{o["top_wells"][n]:.0f}%</td><td>{o["top_oil"][n]:.0f}%</td><td>{o["top_gas"][n]:.0f}%</td></tr>'
body = f'''<h1>How concentrated is production? Licensee shares in Alberta and Saskatchewan</h1>{CHIPS}
<p>A few large companies drill and own much of Canada's production, and a long tail of small ones own the rest. We measured how concentrated it is using the licensee on each well's licence, counting only wells that reported production in the last 12 months. We do not name companies: this is about the shape of the industry, not who is who.</p>
<h2>1. The numbers</h2>
<div class="tw"><table><tr><th>Group of licensees</th><th>Share of producing wells</th><th>Share of oil volume</th><th>Share of gas volume</th></tr>{rows_t}</table></div>
<p><small>{n0(oa["licensees"])} licensees hold Alberta's {n0(oa["wells"])} producing wells; {n0(os_["licensees"])} hold Saskatchewan's {n0(os_["wells"])}.</small></p>
<p>The five largest licensees hold {oa["top_wells"]["5"]:.0f}% of Alberta's producing wells and {os_["top_wells"]["5"]:.0f}% of Saskatchewan's. Saskatchewan is much more concentrated: its largest licensee alone holds {os_["top_wells"]["1"]:.0f}% of wells and {os_["top_oil"]["1"]:.0f}% of oil volume, against {oa["top_wells"]["1"]:.0f}% and {oa["top_oil"]["1"]:.0f}% in Alberta.</p>
<h2>2. How fast do the shares build up?</h2>
{fig(f1, "<b>Figure 1.</b> Cumulative share of producing wells and of oil volume held by the largest licensees (largest first, up to 100). Real data.")}
<p>The tail is long. {oa["small_licensees"]} Alberta licensees and {os_["small_licensees"]} in Saskatchewan have fewer than ten producing wells, and together they hold {oa["small_share"]:.1f}% and {os_["small_share"]:.1f}% of producing wells. Concentration in volume is higher than in wells in both provinces (clearly so in Alberta), which suggests the biggest licensees' wells are on average more productive.</p>
<h2>What this means in practice</h2>
<ul><li>In Saskatchewan, a handful of licensees decide most of the activity; in Alberta the same is true to a lesser degree.</li><li>Counting companies tells you little: hundreds exist, but ten of them hold {oa["top_wells"]["10"]:.0f}% (Alberta) and {os_["top_wells"]["10"]:.0f}% (Saskatchewan) of producing wells.</li><li>If you are building a data tool, expect to join on licensee code, not name, and expect the same company to appear under several names.</li></ul>
<h2>Limits</h2>
<ul><li>The licensee on the licence is not always the current operator: wells change hands without a new licence. These are licensee shares, not operator shares.</li><li>The same company may appear under more than one legal name, which would understate concentration.</li><li>Alberta oil volume includes bitumen from wells licensed for it, so "oil" shares there are partly bitumen.</li><li>BC's public files do not include operator names, so BC is not covered.</li><li>Counts are of wells producing in the last 12 months as of the files we downloaded.</li></ul>{REPRO}{LICENCE}'''
add("who-holds-the-wells", "How concentrated is production? Licensee shares in Alberta and Saskatchewan",
    f"The five largest licensees hold {oa['top_wells']['5']:.0f}% of Alberta's producing wells and {os_['top_wells']['5']:.0f}% of Saskatchewan's; Saskatchewan's largest alone holds {os_['top_oil']['1']:.0f}% of oil volume.",
    body, mini_lines([("AB", oa["curve_wells"][:50], PAL[0]), ("SK", os_["curve_wells"][:50], PAL[1])], 0, 100, "share of wells held by top licensees (1 to 50)", ylab=lambda v: f"{v:g}%"))

# =====================================================================
# 5. Gas-oil ratio
# =====================================================================
GB = ["no gas", "under 100", "100 to 300", "300 to 1,000", "1,000 to 3,000", "3,000 to 10,000", "over 10,000"]
grp = [("Alberta crude oil", AB["gor"]["oil"], PAL[0]), ("Alberta bitumen", AB["gor"]["bitumen"], PAL[3]), ("Saskatchewan oil", SK["gor"]["oil"], PAL[1]), ("BC oil", BC["gor"]["oil"], PAL[2])]
f1 = gbars(GB, [(n, [100 * c / d["n"] for c in d["hist"]], col) for n, d, col in grp], ylab="share of wells", yfmt=lambda v: f"{v:g}%", H=340)
rows_t = "".join(f'<tr><td>{n}</td><td>{d["n"]:,}</td><td>{d["median_with_gas"]:,.0f}</td><td>{100 * d["no_gas"] / d["n"]:.0f}%</td></tr>' for n, d, _ in grp)
body = f'''<h1>Gas-oil ratios: an "oil well" is not the same everywhere</h1>{CHIPS}
<p>The gas-oil ratio (GOR) is how much gas a well makes for each barrel of oil, in standard cubic feet per barrel (scf/bbl). It drives pipeline needs, flaring and economics, and it differs a lot between provinces and well types. We computed it for every well that reported oil in the last 12 months (October 2025 to September 2026) as its total gas volume divided by its total oil volume.</p>
<h2>1. The numbers</h2>
<div class="tw"><table><tr><th>Group</th><th>Oil wells</th><th>Median GOR, wells that report gas (scf/bbl)</th><th>Wells with no gas reported</th></tr>{rows_t}</table></div>
{fig(f1, "<b>Figure 1.</b> Distribution of well gas-oil ratios by group, as a share of the wells in each group. Real data.")}
<p>Alberta crude-oil wells have a median ratio of {AB["gor"]["oil"]["median_with_gas"]:,.0f} scf/bbl, about {AB["gor"]["oil"]["median_with_gas"] / SK["gor"]["oil"]["median_with_gas"]:.1f} times Saskatchewan's {SK["gor"]["oil"]["median_with_gas"]:,.0f}. BC oil wells ({BC["gor"]["oil"]["n"]:,} of them) look like Alberta crude oil at {BC["gor"]["oil"]["median_with_gas"]:,.0f}. Alberta wells licensed for bitumen sit at {AB["gor"]["bitumen"]["median_with_gas"]:,.0f}, far lower.</p>
<h2>2. The spread is wide</h2>
<p>Within each group the ratio spans two orders of magnitude. {100 * sum(AB["gor"]["oil"]["hist"][5:]) / AB["gor"]["oil"]["n"]:.0f}% of Alberta crude-oil wells make more than 3,000 scf/bbl, against {100 * sum(SK["gor"]["oil"]["hist"][5:]) / SK["gor"]["oil"]["n"]:.0f}% in Saskatchewan. A median hides this, so a "typical" oil well in a province is a poor stand-in for any one well.</p>
<h2>What this means in practice</h2>
<ul><li>Do not carry a gas-oil ratio from one province or well type to another; check which group your wells belong to.</li><li>Cleaning the licence substance (crude oil vs bitumen) before averaging changes Alberta's result a lot.</li><li>A well with oil but no reported gas is more often a reporting or tie-in matter than a real zero.</li></ul>
<h2>Limits</h2>
<ul><li>Ratios use reported volumes as they appear in the public files. Gas may be reported at a different point (for example solution gas at the battery) than oil.</li><li>The median is taken over wells that reported gas; wells with no gas are shown separately.</li><li>Alberta wells were grouped by licence substance (crude bitumen against everything else), not by reservoir.</li><li>One 12-month window, and rates as of the files downloaded in November 2026.</li></ul>{REPRO}{LICENCE}'''
add("gas-oil-ratio", "Gas-oil ratios: an \"oil well\" is not the same everywhere",
    f"Alberta crude-oil wells have a median gas-oil ratio of about {AB['gor']['oil']['median_with_gas']:,.0f} scf/bbl, Saskatchewan about {SK['gor']['oil']['median_with_gas']:,.0f}, and Alberta bitumen wells about {AB['gor']['bitumen']['median_with_gas']:,.0f}.",
    body, mini_bars(["<100", "100-300", "300-1k", "1-3k", "3-10k", ">10k"], [("AB", [100 * c / AB["gor"]["oil"]["n"] for c in AB["gor"]["oil"]["hist"][1:]], PAL[0]), ("SK", [100 * c / SK["gor"]["oil"]["n"] for c in SK["gor"]["oil"]["hist"][1:]], PAL[1])],
                    "well gas-oil ratio (scf/bbl), share of wells"))

# =====================================================================
# 6. Data quality
# =====================================================================
dA, dS, dB = DQ["AB"], DQ["SK"], DQ["BC"]
cats = ["duplicate well rows", "blank well status", "licence rows repeated", "missing spud date"]
vals = lambda d: [100 * d["infra_duplicate_rows"] / d["infra_rows"], 100 * d["blank_status_mode"] / d["infra_rows"], 100 * d["licence_duplicate_rows"] / d["licence_rows"], 100 * d["missing_spud"] / d["infra_rows"]]
f1 = gbars(cats, [("Alberta", vals(dA), PAL[0]), ("Saskatchewan", vals(dS), PAL[1])], ylab="share of file rows", yfmt=lambda v: f"{v:g}%")
zr = lambda d: "".join(f"<li><code>{k}</code>: {v['values_with_leading_zeros']:,} of {v['of']:,} values</li>" for k, v in list(d.items())[:4])
body = f'''<h1>What a naive load gets wrong: traps in Canadian well files</h1>{CHIPS}
<p>Most of the work in oil and gas data is cleaning, not analysis. We counted what goes wrong when you open the Alberta, Saskatchewan and BC regulator files with a default spreadsheet or <code>pandas.read_csv</code>, and what the Tidywells loaders do about each one. These are counts from the files we downloaded in November 2026.</p>
<h2>1. Codes lose their leading zeros</h2>
<p>Many identifier and code columns are made only of digits with leading zeros. Spreadsheets and default CSV readers turn them into numbers and drop the zeros, which breaks matches and makes different codes look equal.</p>
<p><b>Alberta Well Infrastructure</b> ({dA["infra_rows"]:,} rows), values that lose leading zeros:</p><ul>{zr(dA["lost_zero_infra"])}</ul>
<p><b>Saskatchewan Well Infrastructure</b> ({dS["infra_rows"]:,} rows):</p><ul>{zr(dS["lost_zero_infra"])}</ul>
<p><b>BC production file, 2025 onward</b> ({dB["zone_rows_2025_on"]:,} rows):</p><ul>{zr(dB["lost_zero_zone"])}</ul>
<p>Tidywells reads every column as text and pads licence numbers to seven characters.</p>
<h2>2. Repeated rows</h2>
{fig(f1, "<b>Figure 1.</b> Share of file rows affected by each problem, Alberta and Saskatchewan. Real counts from the downloaded files.")}
<div class="tw"><table><tr><th>Problem</th><th>Alberta</th><th>Saskatchewan</th></tr>
<tr><td>Rows in the Well Infrastructure file</td><td>{dA["infra_rows"]:,}</td><td>{dS["infra_rows"]:,}</td></tr>
<tr><td>Distinct wells</td><td>{dA["infra_unique_wells"]:,}</td><td>{dS["infra_unique_wells"]:,}</td></tr>
<tr><td>Extra rows for the same well</td><td>{dA["infra_duplicate_rows"]:,}</td><td>{dS["infra_duplicate_rows"]:,}</td></tr>
<tr><td>Licence rows repeated for the same licence</td><td>{dA["licence_duplicate_rows"]:,}</td><td>{dS["licence_duplicate_rows"]:,}</td></tr>
<tr><td>Wells with a blank status</td><td>{dA["blank_status_mode"]:,}</td><td>{dS["blank_status_mode"]:,}</td></tr>
<tr><td>Wells with no spud date</td><td>{dA["missing_spud"]:,}</td><td>{dS["missing_spud"]:,}</td></tr>
<tr><td>Spellings of licence status (raw, cleaned)</td><td>{dA["licence_status_spellings"]} → {dA["licence_status_clean"]}</td><td>{dS["licence_status_spellings"]} → {dS["licence_status_clean"]}</td></tr></table></div>
<p>If you count rows as wells, Alberta is off by {dA["infra_duplicate_rows"]:,}. Tidywells keeps one row per well, the one with the latest status date.</p>
<h2>3. Status and licence spelling</h2>
<p>Alberta's licence status appears in {dA["licence_status_spellings"]} spellings that reduce to {dA["licence_status_clean"]} real values after trimming and case-folding. Counting by raw text splits one status into several. A blank well status ({dA["blank_status_mode"]:,} Alberta wells, {100 * dA["blank_status_mode"] / dA["infra_rows"]:.0f}% of rows) is also common, and as the <a href="licensed-vs-producing.html">inventory post</a> shows, some of those wells are producing.</p>
<h2>4. Same word, different thing</h2>
<ul><li><b>Units:</b> liquids are in cubic metres, gas in thousands of cubic metres. Mixing them in one column is easy.</li><li><b>Rates:</b> Alberta and Saskatchewan give monthly volumes with no producing days; BC reports producing days, which changes the rate for wells that were down part of the month.</li><li><b>Duplicate column names:</b> the BC Well Index has {dB["index_columns"]} columns, with the names {", ".join(f"<code>{k}</code>" for k in sorted(dB["duplicate_header_names"]))} each appearing twice, so a plain read silently renames or overwrites one copy.</li><li><b>"Oil" is not one thing:</b> in Alberta it includes bitumen wells (about three quarters of the volume).</li></ul>
<h2>5. The good news</h2>
<p>Linking works when you handle the zeros: {dA["infra_licence_match_clean"]:.2f}% of Alberta well rows and {dS["infra_licence_match_clean"]:.0f}% of Saskatchewan well rows matched a licence record, so the two-file join from well ID to licensee is reliable.</p>
<h2>What this means in practice</h2>
<ul><li>Read everything as text first; convert deliberately.</li><li>De-duplicate by the latest status date before counting wells.</li><li>Normalise status and licence text before grouping.</li><li>Record units and day-count conventions next to every number.</li></ul>
<h2>Limits</h2>
<ul><li>These are counts of problems we found, not a complete audit; there may be others.</li><li>Row counts reflect the files as downloaded in November 2026.</li><li>The leading-zero lists show the first columns of each file; others are also affected.</li></ul>{REPRO}{LICENCE}'''
add("naive-load-traps", "What a naive load gets wrong: traps in Canadian well files",
    f"Default CSV loading drops leading zeros from codes, counts {dA['infra_duplicate_rows']:,} extra Alberta well rows, and splits licence statuses into {dA['licence_status_spellings']} spellings instead of {dA['licence_status_clean']}.",
    body, mini_bars(["dup", "blank", "lic dup", "no spud"], [("AB", vals(dA), PAL[0]), ("SK", vals(dS), PAL[1])], "share of file rows with each problem"))

# ---------------- register ----------------
pj = ROOT / "posts" / "posts.json"
posts = [p for p in json.loads(pj.read_text()) if p["slug"] not in {n["slug"] for n in posts_new}]
posts += posts_new
pj.write_text(json.dumps(posts, indent=2), encoding="utf-8")
print(len(posts), "posts total")
