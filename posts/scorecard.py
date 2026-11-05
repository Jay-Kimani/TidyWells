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
from pagetpl import page  # noqa: E402

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
    h = ['<h1>Forecast scorecard</h1>',
         '<p>Most sites show forecasts and never check them. Here we write simple forecasts of provincial oil and gas production down <b>before</b> the data exists, then grade them against what the regulators later report. '
         'The methods are deliberately plain, so you can see how hard the problem really is.</p>',
         '<h2>The rules</h2><ul>'
         '<li>Forecasts are made from the latest published month and written to an append-only <a href="data/forecasts.json">log</a>. Each commit is dated by GitHub, so we cannot quietly rewrite one.</li>'
         '<li>A script, not a person, fills in the actual number when the month appears in the <a href="data.html">open data</a>, and calculates the error.</li>'
         '<li>Errors are absolute percentage errors on the daily rate. The data can be revised after first publication; see <a href="revisions.html">Data revisions</a>.</li></ul>',
         '<h2>The three methods</h2><ul>' + "".join(f'<li><b>{n}.</b> {d}</li>' for n, d in METHODS.values()) + '</ul>']
    # live
    ent = log["entries"]
    graded = [e for e in ent if e["actual"] is not None]
    pend = [e for e in ent if e["actual"] is None]
    h.append(f'<h2>Live forecasts</h2><p>{len(ent)} forecasts logged, {len(graded)} graded, {len(pend)} waiting for data. Latest data used: {latest}.</p>')
    if graded:
        by = {}
        for e in graded:
            by.setdefault(e["method"], []).append(e["ape_pct"])
        h.append('<div class="tw"><table><tr><th>Method</th><th>Graded forecasts</th><th>Mean error</th></tr>' + "".join(
            f'<tr><td>{METHODS[m][0]}</td><td>{len(v)}</td><td>{sum(v) / len(v):.1f}%</td></tr>' for m, v in by.items()) + '</table></div>')
    first = sorted({e["data_through"] for e in ent})
    rows = [e for e in ent if e["method"] == "seasonal_trend" and e["data_through"] == first[-1]] if first else []
    if rows:
        h.append(f'<p class="muted">Latest batch (data through {first[-1]}), seasonal trend method. “Pending” means the regulator has not yet published that month.</p>'
                 '<div class="tw"><table><tr><th>Series</th><th>Month</th><th>Forecast</th><th>Actual</th><th>Error</th></tr>' + "".join(
                     f'<tr><td>{PROV[e["series"][:2]]} {e["series"][3:].lower()} ({e["unit"]})</td><td>{e["target"]}</td><td>{fmt(e["forecast"], 1 if e["series"].endswith("OIL") else 0)}</td>'
                     f'<td>{fmt(e["actual"], 1 if e["series"].endswith("OIL") else 0) if e["actual"] is not None else "Pending"}</td>'
                     f'<td>{(str(e["ape_pct"]) + "%") if e["ape_pct"] is not None else "–"}</td></tr>' for e in rows) + '</table></div>')
    # backtest
    h.append('<h2>Backtest</h2><p>This part is calculated after the fact, not a live record: for every past month, each method forecasts 1 and 3 months ahead using only the data up to then, and we score it against what was reported. '
             'The history is short (monthly data from 2022), so treat the numbers as indicative.</p>')
    tot = {}
    body = ['<div class="tw"><table><tr><th>Series</th><th>Method</th><th>Months ahead</th><th>Mean error</th><th>Bias</th><th>Forecasts</th></tr>']
    for key in SERIES:
        for hz in (1, 3):
            best = min(METHODS, key=lambda m: stats(bt[(key, m, hz)])["mape"])
            tot[(key, hz)] = best
            for m in METHODS:
                st = stats(bt[(key, m, hz)])
                b = "<b>" if m == best else ""
                e = "</b>" if m == best else ""
                body.append(f'<tr><td>{PROV[key[0]]} {key[1].lower()}</td><td>{b}{METHODS[m][0]}{e}</td><td>{hz}</td><td>{b}{st["mape"]:.1f}%{e}</td><td>{st["bias"]:+.1f}%</td><td>{st["n"]}</td></tr>')
    body.append('</table></div><p class="muted" style="font-size:13px">Bold marks the lowest mean error for each series and horizon. Bias is the average signed error; above zero means the method ran high.</p>')
    h.append("".join(body))
    wins = {m: sum(1 for v in tot.values() if v == m) for m in METHODS}
    n = len(tot)
    verdict = ", ".join(f"{METHODS[m][0].lower()} {w}" for m, w in sorted(wins.items(), key=lambda x: -x[1]))
    allm = {m: [r for key in SERIES for hz in (1, 3) for r in bt[(key, m, hz)]] for m in METHODS}
    allm = {m: stats(v)["mape"] for m, v in allm.items()}
    bestm = min(allm, key=allm.get)
    h.append(f'<h2>What this shows</h2><p>Across {n} series and horizon combinations the lowest error went to: {verdict}. '
             f'Averaged over everything, the best method was <b>{METHODS[bestm][0].lower()}</b> at {allm[bestm]:.1f}% mean error '
             f'(' + ", ".join(f"{METHODS[m][0].lower()} {v:.1f}%" for m, v in allm.items() if m != bestm) + '). '
             'If a fancier method cannot beat these, it has not earned your trust.</p>')
    h.append(f'<h2>One month ahead, {METHODS[bestm][0].lower()}</h2><p class="muted" style="font-size:13px">The method with the lowest average error. Grey is the reported rate, dashed blue is the forecast made one month earlier.</p><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px">'
             + "".join(f'<div><b style="font-size:14px">{PROV[k[0]]} {k[1].lower()} ({UNIT[k[1]]})</b>{chart(data, bt, k, bestm)}</div>' for k in SERIES) + '</div>')
    h.append('<p class="muted" style="margin-top:22px;font-size:14px">Informational only, not investment, legal or engineering advice. '
             f'Held to account by the <a href="https://github.com/Jay-Kimani/TidyWells/commits/main/docs/data/forecasts.json">commit history</a> of the forecast log. Code: <code>posts/scorecard.py</code>.</p>')
    return "\n".join(h)


if __name__ == "__main__":
    data = load()
    sha = hashlib.sha256(CSV.read_bytes()).hexdigest()
    log = update_log(data, sha)
    bt = backtest(data)
    (ROOT / "docs" / "scorecard.html").write_text(
        page("scorecard.html", "Forecast scorecard",
             "Simple forecasts of Alberta, Saskatchewan and BC oil and gas production, written down before the data exists and graded against what the regulators later reported.",
             build_page(data, bt, log), css=".tw{overflow-x:auto}"), encoding="utf-8")
    print("entries", len(log["entries"]), "backtest cells", len(bt))
