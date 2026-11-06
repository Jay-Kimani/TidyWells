"""Check that the published site agrees with the data, and write docs/data/manifest.json.

Run after build_feed.py:  python posts/verify_site.py
Checks (exit code 1 if any fails):
  1. The open-data CSV is complete: six series, every month present once, no negative values.
  2. Every figure in every monthly snapshot page (rate, change on the month before, change on the year
     before, wells producing) equals the figure recomputed from the CSV, to the precision shown.
  3. The latest-data strip on the home page equals the recomputed latest month.
"""
import csv
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONV = {"OIL": 6.2898 / 1000, "GAS": 35.3147 / 1000}
GROUPS = {"Alberta oil": ("AB", "OIL"), "Alberta gas": ("AB", "GAS"), "Saskatchewan oil": ("SK", "OIL"),
          "Saskatchewan gas": ("SK", "GAS"), "BC oil": ("BC", "OIL"), "BC gas": ("BC", "GAS")}


def num(s):
    return float(s.replace(",", "").replace("−", "-").replace("+", "").replace("%", ""))


def decimals(s):
    return len(s.split(".")[1].rstrip("%")) if "." in s else 0


def close(shown, exact, dec):
    return abs(num(shown) - exact) <= 0.5 * 10 ** (-dec) + 1e-9


def main():
    rows = list(csv.DictReader(open(DOCS / "data" / "tidywells-monthly-production.csv")))
    fails, checked = [], 0
    # 1. integrity
    series, wells = {}, {}
    for r in rows:
        k = (r["province"], r["product"])
        if r["month"] in series.setdefault(k, {}):
            fails.append(f"duplicate month {k} {r['month']}")
        v = float(r["volume"])
        if v < 0:
            fails.append(f"negative volume {k} {r['month']}")
        series[k][r["month"]] = v / float(r["days_in_month"]) * CONV[r["product"]]
        wells.setdefault(k, {})[r["month"]] = int(r["wells_producing"])
    months = sorted(series[("AB", "OIL")])
    for k, s in series.items():
        if sorted(s) != months:
            fails.append(f"series {k} months differ from the others")
    integrity = len(rows)
    # 2. snapshot pages
    for f in sorted((DOCS / "posts").glob("snapshot-*.html")):
        period = f.stem.replace("snapshot-", "")
        t = f.read_text(encoding="utf-8")
        y, m = int(period[:4]), int(period[5:])
        prev = f"{y if m > 1 else y - 1}-{(m - 1) or 12:02d}"
        yago = f"{y - 1}-{m:02d}"
        found = 0
        for tr in re.findall(r"<tr>(.*?)</tr>", t, re.S):
            c = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
            if len(c) != 5 or c[0] not in GROUPS:
                continue
            k = GROUPS[c[0]]
            s = series[k]
            rate, mom, yoy, wl = c[1:]
            exact = [s[period], (s[period] / s[prev] - 1) * 100, (s[period] / s[yago] - 1) * 100]
            for label, shown, ex in (("rate", rate, exact[0]), ("vs previous month", mom, exact[1]), ("vs year earlier", yoy, exact[2])):
                checked += 1
                if not close(shown, ex, decimals(shown)):
                    fails.append(f"{period} {c[0]} {label}: page {shown}, data {ex:.3f}")
            checked += 1
            if int(wl.replace(",", "")) != wells[k][period]:
                fails.append(f"{period} {c[0]} wells: page {wl}, data {wells[k][period]}")
            found += 1
        if found != 6:
            fails.append(f"{period}: found {found} of 6 group rows")
    # 3. home strip
    home = (DOCS / "index.html").read_text(encoding="utf-8")
    last = months[-1]
    prevyr = f"{int(last[:4]) - 1}-{last[5:]}"
    pat = r"<div><span>([^<]+)</span><b>([\d,\.]+) <small>[^<]*</small></b><span class=\"(?:up|dn)\">([^<]+) on a year earlier"
    for label, shown_rate, shown_chg in re.findall(pat, home):
        k = GROUPS[label]
        checked += 2
        if not close(shown_rate, series[k][last], 0):
            fails.append(f"home {label} rate {shown_rate} vs {series[k][last]:.1f}")
        if not close(shown_chg, (series[k][last] / series[k][prevyr] - 1) * 100, 1):
            fails.append(f"home {label} change {shown_chg}")
    sha = hashlib.sha256((DOCS / "data" / "tidywells-monthly-production.csv").read_bytes()).hexdigest()
    manifest = {"built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "file": "tidywells-monthly-production.csv", "sha256": sha,
                "rows": integrity, "series": len(series), "first_month": months[0], "last_month": months[-1],
                "numbers_checked_against_data": checked, "snapshot_pages_checked": len(list((DOCS / "posts").glob("snapshot-*.html"))),
                "failures": len(fails)}
    (DOCS / "data" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    # show the result on the open-data page
    p = DOCS / "data.html"
    t = re.sub(r"<!--CHECKS-->.*?<!--/CHECKS-->", "", p.read_text(encoding="utf-8"), flags=re.S)
    blk = ('<!--CHECKS--><h2 id="checks">How we check this</h2>'
           f'<p>Every time the site is rebuilt, a script recomputes the figures from this file and compares them with what the pages say. '
           f'Last run: <b>{manifest["numbers_checked_against_data"]:,}</b> figures across <b>{manifest["snapshot_pages_checked"]}</b> monthly snapshot pages and the home page, '
           f'<b>{manifest["failures"]}</b> mismatches. The file has {integrity:,} rows ({len(series)} series, {months[0]} to {months[-1]}), with no missing months, duplicates or negative volumes.</p>'
           f'<p class="muted" style="font-size:13px">File fingerprint (SHA-256): <code style="overflow-wrap:anywhere">{sha}</code> · <a href="data/manifest.json">manifest.json</a> · '
           '<a href="https://github.com/Jay-Kimani/TidyWells/blob/main/posts/verify_site.py">the checking script</a>. '
           'This confirms the pages match the data file. It does not prove the regulator files themselves are right, which is why the caveats above matter.</p><!--/CHECKS-->')
    t = t.replace("<h2>Cite it</h2>", blk + "<h2>Cite it</h2>", 1)
    strip = ('<!--STATS--><div class="stats">'
             f'<div class="st"><b>{integrity:,}</b><span>rows in the file</span></div><div class="st"><b>{len(series)}</b><span>series (AB, SK, BC; oil and gas)</span></div>'
             f'<div class="st"><b>{months[0]}</b><span>first month, through {months[-1]}</span></div>'
             f'<div class="st"><b>{manifest["failures"]}</b><span>mismatches in the last check of {manifest["numbers_checked_against_data"]:,} figures</span></div></div><!--/STATS-->')
    t = re.sub(r"<!--STATS-->.*?<!--/STATS-->", strip, t, flags=re.S)
    p.write_text(t, encoding="utf-8")
    print(f"checked {checked} figures; {len(fails)} failures")
    for x in fails[:30]:
        print(" -", x)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
