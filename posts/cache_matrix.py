"""Build a well x month matrix cache (oil and gas volumes) from files you downloaded, outside the repo.
Usage: python posts/cache_matrix.py {ab|sk|bc} FOLDER [CACHE_DIR]     (default CACHE_DIR: /tmp/tw_cache)
Months: 2022-01 .. 2026-09 (57). Volumes are as reported (m3 oil, 10^3 m3 gas); NaN = not reported that month.
"""
import os
import sys

import numpy as np
import pandas as pd

import tidywells as tw

START, N = pd.Period("2022-01"), 57


def run(prov, folder, cache):
    ids, rows = {}, {"OIL": [], "GAS": []}
    def add(d, prod):
        d = d[d["volume"].notna()]
        idx = np.fromiter((ids.setdefault(w, len(ids)) for w in d["well_id"].astype(str)), dtype=np.int64, count=len(d))
        mi = np.array([(m - START).n for m in d["month"]], dtype=np.int64)
        ok = (mi >= 0) & (mi < N)
        rows[prod].append((idx[ok], mi[ok], d["volume"].values[ok].astype(np.float32)))
    if prov == "bc":
        for n in ("zone_prd_2016_to_2024", "zone_prd_2025_to_present"):
            d = tw.read_bc_production(os.path.join(folder, n + ".csv"), products=("OIL", "GAS"))
            d = d[d.month >= START]
            for prod in ("OIL", "GAS"):
                add(d[d["product"] == prod], prod)
    else:
        for f in tw.loaders._expand(folder, prov.upper()):
            d = tw.read_volumetrics(f, products=("OIL", "GAS"))[["month", "well_id", "product", "volume"]]
            for prod in ("OIL", "GAS"):
                add(d[d["product"] == prod], prod)
    out = {"ids": np.array(sorted(ids, key=ids.get))}
    for prod, parts in rows.items():
        m = np.full((len(ids), N), np.nan, dtype=np.float32)
        for idx, mi, v in parts:
            m[idx, mi] = v
        out[prod.lower()] = m
    os.makedirs(cache, exist_ok=True)
    np.savez_compressed(os.path.join(cache, f"mat_{prov}.npz"), **out)
    print(prov, len(ids), "wells")


if __name__ == "__main__":
    run(sys.argv[1].lower(), sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "/tmp/tw_cache")
