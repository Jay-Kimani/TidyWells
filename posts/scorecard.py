"""Forecast scorecard: grades simple forecasts of provincial production against what the regulators later reported.

Two parts, kept separate on the page because they mean different things:
  * Backtest: every past forecast the methods could have made from the data available at the time, scored after the fact.
  * Live log (docs/data/forecasts.json): forecasts written down BEFORE the data exists. Entries are append-only; this script never
    edits a forecast, it only fills in the actual once the month appears in the data. Git history timestamps each entry.
Stdlib only. Run: python3 posts/scorecard.py   (build_feed.py runs after it).
"""
import csv
import hashlib
import json
import os
import sys
from datetime import date
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagetpl import page, hero, stats as stats_strip, bubble, fold, layout  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "docs" / "data" / "tidywells-monthly-production.csv"
LOG = ROOT / "docs" / "data" / "forecasts.json"
CONV = {"OIL": 6.2898 / 1000, "GAS": 35.3147 / 1000}
UNIT = {"OIL": "thousand bbl/d", "GAS": "MMcf/d"}
PROV = {"AB": "Alberta", "SK": "Saskatchewan", "BC": "British Columbia"}
SERIES = [(p, k) for p in ("AB", "SK", "BC") for k in ("OIL", "GAS")]
METHODS = {
    "seasonal_trend": ("Seasonal trend", "Same month last year, scaled by how the last 3 months compared with a year earlier."),
    "seasonal_naive": ("Same month last year", "The value from the same month a year earlier, unchanged."),
    "naive": ("Last month repeated", "The most recent month, carried forward."),
}
HORIZONS = (1, 2, 3)


def mi(s):  # "2026-09" -> month index
    return int(s[:4]) * 12 + int(s[5:7]) - 1


def ms(i):
    return f"{i // 12}-{i % 12 + 1:02d}"


def load():
    out = {}
    for r in csv.DictReader(open(CSV, newline="")):
        key = (r["province"], r["product"])
        out.setdefault(key, {})[mi(r["month"])] = float(r["volume"]) / float(r["days_in_month"]) * CONV[r["product"]]
    return out


def forecast(method, s, origin, target):
    """Forecast for `target` using only months <= origin."""
    if method == "naive":
        return s.get(origin)
    ly = s.get(target - 12)
    if ly is None:
        return None
    if method == "seasonal_naive":
        return ly
    ratios = []
    for k in range(3):
        a, b = s.get(origin - k), s.get(origin - k - 12)
        if a is None or b is None or b == 0:
            return None
        ratios.append(a / b)
    return ly * sum(ratios) / 3


def backtest(data):
    """{(series, method, h): [(origin, forecast, actual)]}"""
    res = {}
    for key in SERIES:
        s = data[key]
        last = max(s)
        for h in HORIZONS:
            for origin in range(min(s) + 14, last - h + 1):
                for m in METHODS:
                    f = forecast(m, s, origin, origin + h)
                    if f is None or (origin + h) not in s:
                        continue
                    res.setdefault((key, m, h), []).append((origin, f, s[origin + h]))
    return res


def stats(rows):
    n = len(rows)
    if not n:
        return None
    ape = [abs(f - a) / a * 100 for _, f, a in rows]
    bias = [(f - a) / a * 100 for _, f, a in rows]
    return {"n": n, "mape": sum(ape) / n, "bias": sum(bias) / n}


def update_log(data, sha):
    log = json.load(open(LOG)) if LOG.exists() else {
        "about": "Append-only log of forecasts written before the data existed. Made dates come from the git history of this file. "
                 "Only the 'actual' and 'ape_pct' fields are ever filled in later, by posts/scorecard.py.",
        "entries": []}
    entries = log["entries"]
    have = {(e["data_through"], e["series"], e["method"], e["target"]) for e in entries}
    latest = max(data[SERIES[0]])
    made = os.environ.get("TW_TODAY") or date.today().isoformat()
    for key in SERIES:
        s = data[key]
        for h in HORIZONS:
            for m in METHODS:
                sid = f"{key[0]}-{key[1]}"
                k = (ms(latest), sid, m, ms(latest + h))
                if k in have:
                    continue
                f = forecast(m, s, latest, latest + h)
                if f is None:
                    continue
                entries.append({"made": made, "data_through": ms(latest), "data_sha256": sha, "series": sid, "method": m,
                                "target": ms(latest + h), "unit": UNIT[key[1]], "forecast": round(f, 4), "actual": None, "ape_pct": None})
    for e in entries:  # fill actuals only
        if e["actual"] is None:
            key = tuple(e["series"].split("-"))
            a = data[key].get(mi(e["target"]))
            if a is not None:
                e["actual"] = round(a, 4)
                e["ape_pct"] = round(abs(e["forecast"] - a) / a * 100, 2)
    json.dump(log, open(LOG, "w"), indent=1)
    open(LOG, "a").write("\n")
    return log


def chart(data, bt, key, method):
    s = data[key]
    rows = bt.get((key, method, 1), [])
    months = sorted(s)
    lo, hi = min(s.values()) * 0.97, max(s.values()) * 1.03
    W, H, P = 620, 150, 8
    x = lambda i: P + (i - months[0]) / (months[-1] - months[0]) * (W - 2 * P)
    y = lambda v: H - P - (v - lo) / (hi - lo) * (H - 2 * P)
    act = " ".join(f"{x(i):.1f},{y(s[i]):.1f}" for i in months)
    fc = " ".join(f"{x(o + 1):.1f},{y(f):.1f}" for o, f, _ in rows)
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Actual and one-month-ahead forecast, {PROV[key[0]]} {key[1].lower()}" style="width:100%;height:auto">'
            f'<polyline points="{act}" fill="none" stroke="var(--muted)" stroke-width="2"/>'
            f'<polyline points="{fc}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-dasharray="4 3"/></svg>')


def fmt(v, d=1):
    return f"{v:,.{d}f}"


def build_page(data, bt, log):
    latest = ms(max(data[SERIES[0]]))
    ent = log["entries"]
    graded = [e for e in ent if e["actual"] is not None]
    pend = [e for e in ent if e["actual"] is None]
    # ---- backtest numbers
    tot = {}
    body = ['<table><tr><th>Series</th><th>Method</th><th class="num">Months ahead</th><th class="num">Mean error</th><th class="num">Bias</th><th class="num">Forecasts</th></tr>']
    for key in SERIES:
        for hz in (1, 3):
            best = min(METHODS, key=lambda m: stats(bt[(key, m, hz)])["mape"])
            tot[(key, hz)] = best
            for m in METHODS:
                st = stats(bt[(key, m, hz)])
                b = "<b>" if m == best else ""
                e = "</b>" if m == best else ""
                body.append(f'<tr><td>{PROV[key[0]]} {key[1].lower()}</td><td>{b}{METHODS[m][0]}{e}</td><td class="num">{hz}</td><td class="num">{b}{st["mape"]:.1f}%{e}</td><td class="num">{st["bias"]:+.1f}%</td><td class="num">{st["n"]}</td></tr>')
    body.append('</table><p class="muted" style="font-size:13px">Bold marks the lowest mean error for each series and horizon. Bias is the average signed error; above zero means the method ran high.</p>')
    wins = {m: sum(1 for v in tot.values() if v == m) for m in METHODS}
    n = len(tot)
    verdict = ", ".join(f"{METHODS[m][0].lower()} {w}" for m, w in sorted(wins.items(), key=lambda x: -x[1]))
    allm = {m: [r for key in SERIES for hz in (1, 3) for r in bt[(key, m, hz)]] for m in METHODS}
    allm = {m: stats(v)["mape"] for m, v in allm.items()}
    bestm = min(allm, key=allm.get)
    others = ", ".join(f"{METHODS[m][0].lower()} {v:.1f}%" for m, v in allm.items() if m != bestm)
    # ---- live batch, one row per series, one column per target month
    first = sorted({e["data_through"] for e in ent})
    rows = [e for e in ent if e["method"] == "seasonal_trend" and e["data_through"] == first[-1]] if first else []
    live = ""
    if rows:
        months = sorted({e["target"] for e in rows})
        order = []
        for e in rows:
            if e["series"] not in order:
                order.append(e["series"])
        by = {(e["series"], e["target"]): e for e in rows}
        def cell(e):
            d = 1 if e["series"].endswith("OIL") else 0
            if e["actual"] is None:
                return f'{fmt(e["forecast"], d)} <span class="pill pend">pending</span>'
            return f'{fmt(e["forecast"], d)} &rarr; {fmt(e["actual"], d)} <span class="pill {"ok" if e["ape_pct"] < 5 else "bad"}">{e["ape_pct"]}% off</span>'
        live = ('<div class="tw"><table><tr><th>Series</th>' + "".join(f'<th class="num">{m}</th>' for m in months) + '</tr>' + "".join(
            f'<tr><td>{PROV[k[:2]]} {k[3:].lower()} <span class="muted">({UNIT[k[3:]]})</span></td>' + "".join(f'<td class="num">{cell(by[(k, m)]) if (k, m) in by else "–"}</td>' for m in months) + '</tr>' for k in order) + '</table></div>'
                f'<p class="muted" style="font-size:13px">Seasonal trend method, written down from data through {first[-1]}. Pending means the regulator has not yet published that month.</p>')
    if graded:
        by2 = {}
        for e in graded:
            by2.setdefault(e["method"], []).append(e["ape_pct"])
        live += ('<div class="tw"><table><tr><th>Method</th><th class="num">Graded forecasts</th><th class="num">Mean error</th></tr>' + "".join(
            f'<tr><td>{METHODS[m][0]}</td><td class="num">{len(v)}</td><td class="num">{sum(v) / len(v):.1f}%</td></tr>' for m, v in by2.items()) + '</table></div>')
    main = (f'<h2>Live forecasts<span class="sub">Written before the data exists. {len(ent)} logged, {len(graded)} graded, {len(pend)} waiting. Latest data used: {latest}.</span></h2>' + live +
            f'<h2>What the backtest shows</h2><div class="callout">Across {n} series and horizons the lowest error went to: {verdict}. Averaged over everything, the best method was <b>{METHODS[bestm][0].lower()}</b> at {allm[bestm]:.1f}% mean error ({others}). If a fancier method cannot beat these, it has not earned your trust.</div>'
            f'<h2>Full backtest<span class="sub">{len(SERIES) * 2 * len(METHODS)} rows: every series, method and horizon.</span></h2>'
            '<p>Calculated after the fact, not a live record: for every past month, each method forecasts 1 and 3 months ahead using only the data up to then, and we score it against what was reported. The history is short (monthly data from 2022), so treat the numbers as indicative.</p><div class="tw">' + "".join(body) + '</div>')
    side = (bubble("The rules",
                   '<ul><li>Forecasts are written to an append-only <a href="data/forecasts.json">log</a>. Each commit is dated by GitHub, so none can be quietly rewritten.</li>'
                   '<li>A script, not a person, fills in the actual number when the month appears in the <a href="data.html">open data</a>.</li>'
                   '<li>Error is absolute percentage error on the daily rate. Data can be revised; see <a href="revisions.html">Data revisions</a>.</li></ul>') +
            bubble("The three methods", "<ul>" + "".join(f'<li><b>{nm}.</b> {d}</li>' for nm, d in METHODS.values()) + "</ul>"))
    h = [hero("Research · Accountability", "Forecast scorecard",
              "Most sites show forecasts and never check them. We write simple forecasts of provincial oil and gas production <b>before</b> the data exists, then grade them against what the regulators report. The methods are deliberately plain, so you can see how hard the problem is."),
         stats_strip([(str(len(ent)), "forecasts logged"), (str(len(graded)), "graded so far"), (str(len(pend)), "waiting for data"), (f"{allm[bestm]:.1f}%", f"mean error, best method ({METHODS[bestm][0].lower()})")]),
         layout(main, side),
         '<p class="muted" style="margin-top:28px;font-size:14px">Informational only, not investment, legal or engineering advice. '
         f'Held to account by the <a href="https://github.com/Jay-Kimani/TidyWells/commits/main/docs/data/forecasts.json">commit history</a> of the forecast log. Code: <code>posts/scorecard.py</code>.</p>']
    return "\n".join(h)


if __name__ == "__main__":
    data = load()
    sha = hashlib.sha256(CSV.read_bytes()).hexdigest()
    log = update_log(data, sha)
    bt = backtest(data)
    (ROOT / "docs" / "scorecard.html").write_text(
        page("scorecard.html", "Forecast scorecard",
             "Simple forecasts of Alberta, Saskatchewan and BC oil and gas production, written down before the data exists and graded against what the regulators later reported.",
             build_page(data, bt, log), css=".tw{overflow-x:auto}", cls="rp"), encoding="utf-8")
    print("entries", len(log["entries"]), "backtest cells", len(bt))
