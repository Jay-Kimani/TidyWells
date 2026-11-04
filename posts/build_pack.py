"""Rebuild the Tidywells Pro monthly data pack from the aggregate files (aggregates only, no well data).

Monthly routine (data stays on your computer):
  1. Download the latest Petrinex / BCER files.
  2. python posts/monthly_agg.py ab FOLDER ; ... sk ... ; ... bc ...   (refreshes posts/monthly_agg.csv)
  3. python posts/build_pack.py                                         (writes the zip, named by the latest month)

Output goes OUTSIDE the repo (default ~/Documents/Tidywells-Pro) so paid files never reach the public site.
"""
import csv
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Tidywells-Pro")


def prev_month(ym):
    y, m = map(int, ym.split("-"))
    return f"{y - (m == 1)}-{(m - 2) % 12 + 1:02d}"


def main():
    rows_in = {}
    for x in csv.DictReader(open(os.path.join(HERE, "monthly_agg.csv"))):
        rows_in[(x["province"], x["product"], x["month"])] = x  # later rows win (re-runs append)
    latest = max(k[2] for k in rows_in)
    edition = latest
    out = os.path.join(OUT_ROOT, edition)
    os.makedirs(out, exist_ok=True)
    rows = []
    for k in sorted(rows_in):
        x = rows_in[k]
        v, w, d = float(x["volume"]), int(float(x["wells"])), int(x["days_in_month"])
        py = rows_in.get((k[0], k[1], f"{int(k[2][:4]) - 1}-{k[2][5:]}"))
        pm = rows_in.get((k[0], k[1], prev_month(k[2])))
        yoy = round(100 * (v / float(py["volume"]) - 1), 1) if py and float(py["volume"]) else ""
        mom = round(100 * (v / float(pm["volume"]) - 1), 1) if pm and float(pm["volume"]) else ""
        rows.append([k[0], k[1], k[2], "m3" if k[1] == "OIL" else "1000 m3", round(v, 1), w, round(v / d, 1),
                     round(v / d / w, 3) if w else "", mom, yoy])
    with open(os.path.join(out, "monthly_production.csv"), "w", newline="") as f:
        c = csv.writer(f)
        c.writerow(["province", "product", "month", "unit", "volume", "wells_reporting", "avg_daily_volume",
                    "avg_daily_volume_per_well", "change_vs_prior_month_pct", "change_vs_year_ago_pct"])
        c.writerows(rows)
    study = json.load(open(os.path.join(HERE, "study.json")))
    with open(os.path.join(out, "well_status_inventory.csv"), "w", newline="") as f:
        c = csv.writer(f)
        c.writerow(["province", "well_status", "wells_in_infrastructure_file", "producing_in_last_12_months"])
        for p in ("AB", "SK"):
            for b in study[p]["inventory"]["by_status"]:
                c.writerow([p, b["status"], b["n"], b["producing"]])
    rec = json.load(open(os.path.join(HERE, "recovery.json")))
    with open(os.path.join(out, "backtest_summary.csv"), "w", newline="") as f:
        c = csv.writer(f)
        c.writerow(["group", "wells_tested", "share_recovered_pct"])
        for k, v in rec.items():
            c.writerow([k, v["n"], round(v["recovered_share"], 1)])
    readme = f"""Tidywells Pro - monthly data pack ({edition} edition, data through {latest})

WHAT THIS IS
The monthly volumes here come from the same public tables as the free monthly snapshots on tidywells.com. The pack
adds structure and convenience (tidy CSVs, per-well and growth columns, consistent units), not new data.

FILES
monthly_production.csv     Monthly totals by province (AB, SK, BC) and product (OIL, GAS): wells reporting, average
                           daily volume, per-well average, change vs prior month and year-ago.
well_status_inventory.csv  Wells in the AB and SK infrastructure files by licence status, and how many produced in the
                           last 12 months (as of the last time this table was rebuilt).
backtest_summary.csv       Share of wells whose output recovered after a low month, from the decline-curve backtest post.

UNITS: oil in cubic metres (m3); gas in thousands of cubic metres (1000 m3). Convert: bbl = m3 x 6.28981; mcf = 1000 m3 x 35.3147.

NOTES
- Alberta "OIL" includes wells licensed for crude bitumen (about three quarters of recent Alberta oil-product volume).
- Wells reporting counts wells with a volume row that month; it is not a count of all licensed wells.
- Built from public Petrinex (AB, SK) and BC Energy Regulator data using the open-source methods at https://tidywells.com/methods.html.

DISCLAIMER
Information and education only. Not legal, engineering, reserves-evaluation, financial or investment advice, and not a
recommendation to buy or sell any security or asset. Derived from public data and may contain errors or delays; check the
original sources. Independent; not affiliated with Petrinex, the AER, the Saskatchewan Ministry of Energy and Resources or
the BC Energy Regulator. For your own or your organization's internal use; please do not resell or republish.
Questions: hello@tidywells.com
"""
    open(os.path.join(out, "README.txt"), "w").write(readme)
    zpath = os.path.join(OUT_ROOT, f"Tidywells-Pro-{edition}.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(out)):
            z.write(os.path.join(out, fn), fn)
    print(f"wrote {zpath} ({len(rows)} monthly rows, latest {latest})")


if __name__ == "__main__":
    main()
