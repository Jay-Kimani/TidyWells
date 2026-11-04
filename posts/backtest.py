"""Decline curve backtest behind the Nov 2026 write-up.

Usage: python posts/backtest.py {ab|sk|bc} /path/to/your/downloaded/files

For up to 500 random wells with production in (almost) all 57 months of
2022-01..2026-09: fit Arps decline on the first 45 months (from the peak), predict
the last 12 months' cumulative volume, compare to what was reported.
You supply the files from Petrinex (AB, SK) or BCER (BC). Nothing is downloaded here.
"""
import os
import sys

import numpy as np
import pandas as pd

import tidywells as tw

NMONTHS, TRAIN = 57, 45


def run(long: pd.DataFrame, product: str, to_unit: float, use_days: bool, label: str):
    g = long[long["product"] == product]
    g = g.assign(well_id=g["well_id"].astype(str)) if str(g["well_id"].dtype) == "category" else g
    by = g.groupby("well_id")
    n_any = by["month"].nunique()
    n_pos = g[g["volume"] > 0].groupby("well_id")["month"].nunique().reindex(n_any.index).fillna(0)
    full = n_any.index[(n_any >= NMONTHS) & (n_pos >= 50)]
    pick = np.random.default_rng(0).choice(full, min(500, len(full)), replace=False)
    g = g[g["well_id"].isin(pick)]
    vol = g.pivot_table(index="well_id", columns="month", values="volume", aggfunc="sum")
    days = g.pivot_table(index="well_id", columns="month", values="days", aggfunc="max") if use_days else None
    dim = np.array([m.days_in_month for m in vol.columns])
    t = np.arange(NMONTHS) / 12
    rows = []
    for w in pick:
        d = np.where(days.loc[w].values > 0, days.loc[w].values, np.nan) if use_days else dim
        q = vol.loc[w].values / d * to_unit
        try:
            fit = tw.fit_arps(t[:TRAIN], q[:TRAIN])
        except ValueError:
            continue
        qt = q[:TRAIN]
        i0 = int(np.argmax(np.where(np.isfinite(qt) & (qt > 0), qt, -1)))
        dd = np.where(np.isfinite(d[TRAIN:]), d[TRAIN:], dim[TRAIN:]) if use_days else dim[TRAIN:]
        pred = np.sum(tw.arps_rate(t[TRAIN:] - t[i0], fit["qi"], fit["di"], fit["b"]) * dd)
        actual = np.nansum(vol.loc[w].values[TRAIN:]) * to_unit if use_days else np.nansum(q[TRAIN:] * dim[TRAIN:])
        if actual > 0:
            rows.append((pred / actual - 1, len(fit["warnings"]) > 0, fit["b"]))
    e = pd.DataFrame(rows, columns=["err", "warn", "b"])
    print(f"{label}: full-history wells {len(full)}, tested {len(e)}, "
          f"median abs error {100*e.err.abs().median():.0f}%, "
          f"within 25% {100*(e.err.abs()<.25).mean():.0f}%, within 50% {100*(e.err.abs()<.5).mean():.0f}%, "
          f"median signed {100*e.err.median():.0f}%, warnings {100*e.warn.mean():.0f}%, median b {e.b.median():.1f}")


if __name__ == "__main__":
    prov, folder = sys.argv[1].lower(), sys.argv[2]
    if prov == "bc":
        v = pd.concat([tw.read_bc_production(os.path.join(folder, f"{n}.csv"), products=("GAS",))
                       for n in ("zone_prd_2016_to_2024", "zone_prd_2025_to_present")], ignore_index=True)
        v = v[v.month >= pd.Period("2022-01")]
        run(v, "GAS", tw.loaders.E3M3_TO_MCF, True, "BC gas (mcf/d, producing days)")
    else:
        # read one file at a time and keep only 4 columns so Alberta fits in ~4 GB of RAM
        files = tw.loaders._expand(folder, prov.upper())
        parts = []
        for f in files:
            d = tw.read_volumetrics(f, products=("OIL", "GAS"))[["month", "well_id", "product", "volume"]]
            parts.append(d.assign(product=d["product"].astype("category")))
        v = pd.concat(parts, ignore_index=True)
        del parts
        if prov == "ab":
            run(v, "OIL", tw.loaders.M3_TO_BBL, False, "AB oil (bbl/d)")
        else:
            run(v, "OIL", tw.loaders.M3_TO_BBL, False, "SK oil (bbl/d)")
            run(v, "GAS", tw.loaders.E3M3_TO_MCF, False, "SK gas (mcf/d)")
