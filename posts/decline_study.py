"""First-year decline of new wells: rate in months 10-12 after first production vs the initial peak (first 3 months).
Usage: python posts/decline_study.py {ab|sk} FOLDER [CACHE_DIR]   (needs cache_matrix.py output; writes posts/decline_study.json)
Aggregates only. New wells = spud date 2021 or later whose first production month is in the data window."""
import json
import os
import sys

import numpy as np
import pandas as pd

import tidywells as tw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "decline_study.json")
N, START = 57, pd.Period("2022-01")
DIM = np.array([(START + i).days_in_month for i in range(N)], dtype=float)
M3_BBL, E3M3_MCF = tw.loaders.M3_TO_BBL, tw.loaders.E3M3_TO_MCF


def study(prov, folder, cache):
    z = np.load(os.path.join(cache, f"mat_{prov}.npz"), allow_pickle=True)
    ids, oil, gas = z["ids"], np.nan_to_num(z["oil"]), np.nan_to_num(z["gas"])
    pos = (oil > 0) | (gas > 0)
    inf = tw.loaders._latest(tw.read_well_infrastructure(os.path.join(folder, f"Well Infrastructure-{prov.upper()}.csv.zip")), "well_id", "status_date")
    lic = tw.loaders._latest(tw.read_well_licence(os.path.join(folder, f"Well Licence-{prov.upper()}.csv.zip")), "licence_number", "licence_status_date")
    df = inf.merge(lic, on="licence_number", how="left", suffixes=("", "_lic")).set_index("well_id").reindex(ids)
    first = np.where(pos.any(axis=1), pos.argmax(axis=1), -1)
    spud = pd.to_datetime(df.spud_date).values
    sub = df.substance.fillna("").astype(str).values
    horiz = df.horizontal.fillna("").astype(str).str.upper().str.contains("HORIZ").values
    ok = (spud >= np.datetime64("2021-01-01")) & (first >= 1) & (first <= 44)
    rows = []
    for i in np.where(ok)[0]:
        a = first[i]
        o6, g6 = oil[i, a:a + 6].sum(), gas[i, a:a + 6].sum()
        if o6 > 0 and o6 * M3_BBL * 6000 > g6 * E3M3_MCF * 1000:
            k = "bitumen" if "BITUMEN" in sub[i].upper() else "oil"; r = oil[i] / DIM * M3_BBL
        elif g6 > 0:
            k = "gas"; r = gas[i] / DIM * E3M3_MCF
        else:
            continue
        peak = r[a:a + 3].max()
        late = r[a + 9:a + 12]
        if peak <= 0:
            continue
        rows.append((k, int((START + int(a)).year), bool(horiz[i]), float(late.mean() / peak), bool((late > 0).all())))
    d = pd.DataFrame(rows, columns=["cls", "year", "horiz", "ratio", "all_on"])
    res = {"new_wells": int(len(d))}
    def summ(x):
        live = x[x.all_on]
        return dict(n=int(len(x)), still_on=float(len(live) / max(len(x), 1) * 100), median=float(live.ratio.median()),
                    p25=float(live.ratio.quantile(.25)), p75=float(live.ratio.quantile(.75)))
    res["by_class"] = {k: summ(g) for k, g in d.groupby("cls") if len(g) >= 30}
    res["by_vintage"] = [dict(cls=k, year=int(y), **summ(g)) for (k, y), g in d.groupby(["cls", "year"]) if len(g) >= 30]
    res["by_drill"] = {f"{k}_{'horizontal' if h else 'other'}": summ(g) for (k, h), g in d.groupby(["cls", "horiz"]) if len(g) >= 30}
    return res


if __name__ == "__main__":
    prov, folder = sys.argv[1].lower(), sys.argv[2]
    cache = sys.argv[3] if len(sys.argv) > 3 else "/tmp/tw_cache"
    allr = json.load(open(OUT)) if os.path.exists(OUT) else {}
    allr[prov.upper()] = study(prov, folder, cache)
    json.dump(allr, open(OUT, "w"), indent=1)
    print(prov, json.dumps({k: v for k, v in allr[prov.upper()].items() if k != "by_vintage"})[:900])
