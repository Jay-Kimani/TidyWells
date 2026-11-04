"""Decline curve backtest behind the Nov 2026 write-up.

Usage: python posts/backtest.py {ab|sk|bc} /path/to/your/downloaded/files [extra]

For up to 500 random wells with production in (almost) all 57 months of
2022-01..2026-09: fit Arps decline on the first N months (from the peak), predict
months 46-57's cumulative volume, compare to what was reported.
With 'extra', also runs: exponential-only vs hyperbolic, shorter training windows,
and a split by whether the rate recovered in the test window.
You supply the files from Petrinex (AB, SK) or BCER (BC). Nothing is downloaded here.
"""
import os
import sys

import numpy as np
import pandas as pd

import tidywells as tw

NMONTHS, TEST_START = 57, 45


def load(prov: str, folder: str):
    """Return [(label, long_df, product, to_unit, use_days)] for a province."""
    if prov == "bc":
        v = pd.concat([tw.read_bc_production(os.path.join(folder, f"{n}.csv"), products=("GAS",))
                       for n in ("zone_prd_2016_to_2024", "zone_prd_2025_to_present")], ignore_index=True)
        v = v[v.month >= pd.Period("2022-01")]
        return [("BC gas", v, "GAS", tw.loaders.E3M3_TO_MCF, True)]
    files = tw.loaders._expand(folder, prov.upper())
    parts = []
    for f in files:  # one file at a time, 4 columns, so Alberta fits in ~4 GB of RAM
        d = tw.read_volumetrics(f, products=("OIL", "GAS"))[["month", "well_id", "product", "volume"]]
        parts.append(d.assign(product=d["product"].astype("category")))
    v = pd.concat(parts, ignore_index=True)
    if prov == "ab":
        return [("AB oil", v, "OIL", tw.loaders.M3_TO_BBL, False)]
    return [("SK oil", v, "OIL", tw.loaders.M3_TO_BBL, False), ("SK gas", v, "GAS", tw.loaders.E3M3_TO_MCF, False)]


def evaluate(long, product, to_unit, use_days, train=TEST_START, b_max=2.0):
    """One row per tested well: error of the predicted months 46-57 cumulative volume."""
    g = long[long["product"] == product]
    g = g.assign(well_id=g["well_id"].astype(str)) if str(g["well_id"].dtype) == "category" else g
    n_any = g.groupby("well_id")["month"].nunique()
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
            fit = tw.fit_arps(t[:train], q[:train], b_max=b_max)
        except ValueError:
            continue
        qt = q[:train]
        i0 = int(np.argmax(np.where(np.isfinite(qt) & (qt > 0), qt, -1)))
        dd = np.where(np.isfinite(d[TEST_START:]), d[TEST_START:], dim[TEST_START:]) if use_days else dim[TEST_START:]
        pred = np.sum(tw.arps_rate(t[TEST_START:] - t[i0], fit["qi"], fit["di"], fit["b"]) * dd)
        actual = np.nansum(vol.loc[w].values[TEST_START:]) * to_unit if use_days else np.nansum(q[TEST_START:] * dim[TEST_START:])
        recent = np.nanmean(q[TEST_START - 3:TEST_START])
        if actual > 0 and recent > 0:
            rows.append(dict(err=pred / actual - 1, warn=len(fit["warnings"]) > 0, b=fit["b"],
                             up=np.nanmean(q[TEST_START:]) > recent))
    return pd.DataFrame(rows)


def summ(e):
    return (f"tested {len(e)}, median abs error {100*e.err.abs().median():.0f}%, "
            f"within 25% {100*(e.err.abs()<.25).mean():.0f}%, within 50% {100*(e.err.abs()<.5).mean():.0f}%, "
            f"median signed {100*e.err.median():.0f}%")


if __name__ == "__main__":
    prov, folder = sys.argv[1].lower(), sys.argv[2]
    extra = len(sys.argv) > 3 and sys.argv[3] == "extra"
    for label, v, product, unit, use_days in load(prov, folder):
        e = evaluate(v, product, unit, use_days)
        print(f"{label}: {summ(e)}, warnings {100*e.warn.mean():.0f}%, median b {e.b.median():.1f}")
        if extra:
            ex = evaluate(v, product, unit, use_days, b_max=0.0)
            print(f"  exponential only (b=0): {summ(ex)}")
            for tr in (24, 36):
                print(f"  train on {tr} months: {summ(evaluate(v, product, unit, use_days, train=tr))}")
            print(f"  rate recovered in test window: {100*e.up.mean():.0f}% of wells; "
                  f"median signed error {100*e[e.up].err.median():.0f}% (recovered) vs {100*e[~e.up].err.median():.0f}% (kept declining)")
