"""Does the Alberta oil result change if bitumen-licensed wells are split out?
Usage: python posts/backtest_split.py FOLDER     -> posts/split.json (aggregates only)
Same method and sample rules as posts/backtest.py, run separately on wells whose licence substance is crude bitumen vs all other Alberta oil wells."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as bt  # noqa: E402
import tidywells as tw  # noqa: E402

folder = sys.argv[1]
label, v, product, unit, use_days = bt.load("ab", folder)[0]
inf = tw.loaders._latest(tw.read_well_infrastructure(os.path.join(folder, "Well Infrastructure-AB.csv.zip")), "well_id", "status_date")
lic = tw.loaders._latest(tw.read_well_licence(os.path.join(folder, "Well Licence-AB.csv.zip")), "licence_number", "licence_status_date")
m = inf.merge(lic, on="licence_number", how="left")
bit = set(m.loc[m.substance.fillna("").str.contains("BITUMEN"), "well_id"])
other = set(m.loc[~m.substance.fillna("").str.contains("BITUMEN"), "well_id"])
wid = v["well_id"].astype(str)
out = {}
for name, ids in (("Alberta crude oil (no bitumen wells)", other), ("Alberta bitumen wells", bit)):
    sub = v[wid.isin(ids)]
    res = {}
    for tr in (45, 36, 24):
        e = bt.evaluate(sub, product, unit, use_days, train=tr)
        res[str(tr)] = dict(n=int(len(e)), median_abs=float(e.err.abs().median() * 100), within25=float((e.err.abs() < .25).mean() * 100),
                            within50=float((e.err.abs() < .5).mean() * 100), bias=float(e.err.median() * 100), recovered=float(e.up.mean() * 100))
    ex = bt.evaluate(sub, product, unit, use_days, b_max=0.0)
    res["exp_median_abs"] = float(ex.err.abs().median() * 100)
    out[name] = res
    print(name, json.dumps(res["45"]), flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "split.json"), "w"), indent=1)
