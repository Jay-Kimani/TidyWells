"""Aggregate curves for the post thumbnail: median reported vs median forecast rate,
each well scaled to its own peak in the training window. Usage:
    python posts/thumb_data.py {ab|sk|bc} /path/to/your/files   ->  posts/thumb_backtest.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as bt  # noqa: E402
import tidywells as tw  # noqa: E402


def curves(long, product, to_unit, use_days, train=bt.TEST_START):
    N = bt.NMONTHS
    g = long[long["product"] == product]
    g = g.assign(well_id=g["well_id"].astype(str)) if str(g["well_id"].dtype) == "category" else g
    n_any = g.groupby("well_id")["month"].nunique()
    n_pos = g[g["volume"] > 0].groupby("well_id")["month"].nunique().reindex(n_any.index).fillna(0)
    full = n_any.index[(n_any >= N) & (n_pos >= 50)]
    pick = np.random.default_rng(0).choice(full, min(500, len(full)), replace=False)
    g = g[g["well_id"].isin(pick)]
    vol = g.pivot_table(index="well_id", columns="month", values="volume", aggfunc="sum")
    days = g.pivot_table(index="well_id", columns="month", values="days", aggfunc="max") if use_days else None
    dim = np.array([m.days_in_month for m in vol.columns])
    t = np.arange(N) / 12
    act, fc = [], []
    for w in pick:
        d = np.where(days.loc[w].values > 0, days.loc[w].values, np.nan) if use_days else dim
        q = vol.loc[w].values / d * to_unit
        try:
            fit = tw.fit_arps(t[:train], q[:train])
        except ValueError:
            continue
        qt = q[:train]
        i0 = int(np.argmax(np.where(np.isfinite(qt) & (qt > 0), qt, -1)))
        peak = qt[i0]
        if not peak > 0:
            continue
        model = np.full(N, np.nan)
        model[i0:] = tw.arps_rate(t[i0:] - t[i0], fit["qi"], fit["di"], fit["b"])
        act.append(q / peak)
        fc.append(model / peak)
    act, fc = np.array(act), np.array(fc)
    return dict(n=len(act), actual=np.nanmedian(act, axis=0).round(4).tolist(), model=np.nanmedian(fc, axis=0).round(4).tolist())


if __name__ == "__main__":
    prov, folder = sys.argv[1].lower(), sys.argv[2]
    label, v, product, unit, use_days = bt.load(prov, folder)[0]
    out = curves(v, product, unit, use_days)
    out.update(label=label, train_months=bt.TEST_START, months=bt.NMONTHS)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "thumb_backtest.json"), "w"))
    print(label, out["n"])
