"""Second analysis: which wells 'recover' after the training window, and does a low month just before it explain the miss?
Usage: python posts/recovery.py {ab|sk|bc} FOLDER   (adds to posts/recovery.json; aggregates only)
Same wells and fits as posts/backtest.py (first 45 months to fit, months 46-57 to test)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as bt  # noqa: E402
import tidywells as tw  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recovery.json")
BINS = [-1.0, -0.75, -0.5, -0.25, -0.1, 0.1, 0.25, 0.5, 0.75, 1.0, 9]  # error bins (pred/actual - 1)


def rows(long, product, to_unit, use_days, train=bt.TEST_START):
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
    out = []
    for w in pick:
        d = np.where(days.loc[w].values > 0, days.loc[w].values, np.nan) if use_days else dim
        q = vol.loc[w].values / d * to_unit
        try:
            fit = tw.fit_arps(t[:train], q[:train])
        except ValueError:
            continue
        qt = q[:train]
        i0 = int(np.argmax(np.where(np.isfinite(qt) & (qt > 0), qt, -1)))
        pred = np.sum(tw.arps_rate(t[train:] - t[i0], fit["qi"], fit["di"], fit["b"]) * dim[train:])
        actual = np.nansum(q[train:] * dim[train:])
        recent = np.nanmean(q[train - 3:train])
        if not (actual > 0 and recent > 0):
            continue
        base = np.nanmedian(q[train - 12:train])
        dip = bool(np.nanmin(np.nan_to_num(q[train - 6:train], nan=0.0)) < 0.5 * base)      # a low/zero month in the last 6 training months
        testdip = bool(np.nanmin(np.nan_to_num(q[train:], nan=0.0)) < 0.5 * base)          # a low/zero month inside the test window
        out.append(dict(err=pred / actual - 1, up=bool(np.nanmean(q[train:]) > recent), dip=dip, testdip=testdip,
                        lift=float(np.nanmean(q[train:]) / recent)))
    return out


def summarise(r):
    e = np.array([x["err"] for x in r]); up = np.array([x["up"] for x in r]); dip = np.array([x["dip"] for x in r])
    tdip = np.array([x["testdip"] for x in r]); lift = np.array([x["lift"] for x in r])
    med = lambda m: float(np.median(e[m]) * 100) if m.sum() else None
    return dict(n=len(r), recovered_share=float(up.mean() * 100), recovered_lift_median=float(np.median(lift[up]) * 100 - 100),
                dip_share_all=float(dip.mean() * 100), dip_share_recovered=float(dip[up].mean() * 100), dip_share_declining=float(dip[~up].mean() * 100),
                recovered_with_dip=float((up & dip).sum() / up.sum() * 100), err_dip=med(dip), err_nodip=med(~dip),
                err_rec_dip=med(up & dip), err_rec_nodip=med(up & ~dip), n_rec_dip=int((up & dip).sum()), n_rec_nodip=int((up & ~dip).sum()),
                testdip_share=float(tdip.mean() * 100),
                hist_recovered=np.histogram(e[up], BINS)[0].tolist(), hist_declining=np.histogram(e[~up], BINS)[0].tolist())


if __name__ == "__main__":
    prov, folder = sys.argv[1].lower(), sys.argv[2]
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for label, v, product, unit, use_days in bt.load(prov, folder):
        res[label] = summarise(rows(v, product, unit, use_days))
        print(label, json.dumps({k: (round(x, 1) if isinstance(x, float) else x) for k, x in res[label].items() if not k.startswith("hist")}), flush=True)
    json.dump(res, open(OUT, "w"))
