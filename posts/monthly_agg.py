"""Province-level monthly totals from files you downloaded. Aggregates only; no well data is written.
Usage: python posts/monthly_agg.py {ab|sk|bc} FOLDER      (appends to posts/monthly_agg.csv)
Columns: province, product, month, volume (m3 oil, 10^3 m3 gas), wells (volume > 0), days_in_month
"""
import os
import sys

import pandas as pd

import tidywells as tw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monthly_agg.csv")


def agg(d, prov):
    d = d[d["volume"].notna()]
    g = d.groupby(["product", "month"]).agg(volume=("volume", "sum"), wells=("volume", lambda s: int((s > 0).sum()))).reset_index()
    g.insert(0, "province", prov.upper())
    return g


if __name__ == "__main__":
    prov, folder = sys.argv[1].lower(), sys.argv[2]
    parts = []
    if prov == "bc":
        for n in ("zone_prd_2016_to_2024", "zone_prd_2025_to_present"):
            d = tw.read_bc_production(os.path.join(folder, n + ".csv"), products=("OIL", "GAS"))
            parts.append(agg(d[d.month >= pd.Period("2022-01")], prov))
    else:
        for f in tw.loaders._expand(folder, prov.upper()):
            d = tw.read_volumetrics(f, products=("OIL", "GAS"))[["month", "well_id", "product", "volume"]]
            parts.append(agg(d, prov))
    out = pd.concat(parts, ignore_index=True).groupby(["province", "product", "month"], as_index=False).sum()
    out["days_in_month"] = [m.days_in_month for m in out["month"]]
    out["month"] = out["month"].astype(str)
    old = pd.read_csv(OUT) if os.path.exists(OUT) else pd.DataFrame()
    if len(old):
        old = old[old.province != prov.upper()]
    pd.concat([old, out], ignore_index=True).to_csv(OUT, index=False)
    print(prov, len(out))
