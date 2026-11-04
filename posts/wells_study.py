"""Aggregate studies behind several posts: inventory vs producing wells, shut-ins and restarts,
new-well productivity by vintage, licensee concentration, gas-oil ratio.
Usage: python posts/wells_study.py {ab|sk|bc} FOLDER [CACHE_DIR]   (needs posts/cache_matrix.py output; adds to posts/study.json)
Writes aggregates only: no well IDs, no company names."""
import json
import os
import sys

import numpy as np
import pandas as pd

import tidywells as tw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "study.json")
N, START = 57, pd.Period("2022-01")
DIM = np.array([(START + i).days_in_month for i in range(N)], dtype=float)
M3_BBL, E3M3_MCF = tw.loaders.M3_TO_BBL, tw.loaders.E3M3_TO_MCF
LAST12 = slice(45, 57)


def topn_shares(counts: pd.Series, ns=(1, 5, 10, 20, 50)):
    c = counts.sort_values(ascending=False)
    tot = c.sum()
    return {str(n): float(c.iloc[:n].sum() / tot * 100) for n in ns}, (c.iloc[:100].cumsum() / tot * 100).round(2).tolist()


def study(prov, folder, cache):
    z = np.load(os.path.join(cache, f"mat_{prov}.npz"), allow_pickle=True)
    ids, oil, gas = z["ids"], z["oil"], z["gas"]
    opos, gpos = np.nan_to_num(oil) > 0, np.nan_to_num(gas) > 0
    pos = opos | gpos
    res = {"wells_in_files": int(len(ids)), "wells_ever_positive": int(pos.any(axis=1).sum())}
    p12 = pos[:, LAST12].any(axis=1)
    res["producing_last12"] = int(p12.sum())

    # ---------- attributes ----------
    df = None
    if prov in ("ab", "sk"):
        inf = tw.loaders._latest(tw.read_well_infrastructure(os.path.join(folder, f"Well Infrastructure-{prov.upper()}.csv.zip")), "well_id", "status_date")
        lic = tw.loaders._latest(tw.read_well_licence(os.path.join(folder, f"Well Licence-{prov.upper()}.csv.zip")), "licence_number", "licence_status_date")
        allw = inf.merge(lic, on="licence_number", how="left", suffixes=("", "_lic"))
        allw["p12"] = allw.well_id.isin(set(ids[p12]))
        allw["ever"] = allw.well_id.isin(set(ids[pos.any(axis=1)]))
        mode = allw.status_mode.fillna("(blank)")
        g = allw.groupby(mode).agg(n=("well_id", "size"), producing=("p12", "sum")).sort_values("n", ascending=False)
        res["inventory"] = dict(
            total=int(len(allw)), producing_last12=int(allw.p12.sum()), ever=int(allw.ever.sum()),
            by_status=[dict(status=k, n=int(r.n), producing=int(r.producing)) for k, r in g.head(8).iterrows()],
            other_n=int(g.iloc[8:].n.sum()), other_producing=int(g.iloc[8:].producing.sum()),
            blank_producing=int(allw[(mode == "(blank)") & allw.p12].shape[0]))
        df = allw.set_index("well_id").reindex(ids)

    # ---------- shut-ins and restarts ----------
    first = np.where(pos.any(axis=1), pos.argmax(axis=1), -1)
    last = np.where(pos.any(axis=1), N - 1 - pos[:, ::-1].argmax(axis=1), -1)
    ever = first >= 0
    # cohort: producing in Jan 2022
    coh = pos[:, 0]
    surv = (pos[coh].mean(axis=0) * 100).round(2).tolist()
    # gaps of >=3 months between first and last positive month
    def gaps(row, a, b):
        out, run = [], 0
        for v in row[a:b + 1]:
            if v: 
                if run >= 3: out.append(run)
                run = 0
            else: run += 1
        return out
    gl = []
    inter = 0
    for i in np.where(ever)[0]:
        g_ = gaps(pos[i], first[i], last[i])
        if g_:
            inter += 1; gl += g_
    stopped = int((ever & (last <= 50)).sum())
    prod_prev = pos[:, 2:-2]
    restarts, stops = [], []
    for t in range(3, N - 2):
        pt = pos[:, t]
        rs = pt & ~pos[:, t - 1] & ~pos[:, t - 2] & ~pos[:, t - 3] & (first <= t - 4) & (first >= 0)
        st = pos[:, t - 1] & ~pos[:, t] & ~pos[:, t + 1] & ~pos[:, t + 2]
        base = max(int(pos[:, t - 1].sum()), 1)
        restarts.append(round(100 * rs.sum() / base, 3)); stops.append(round(100 * st.sum() / base, 3))
    bk = lambda lo, hi: int(sum(lo <= x <= hi for x in gl))
    res["shutins"] = dict(
        ever=int(ever.sum()), producing_last_month=int(pos[:, -1].sum()), stopped_6m=stopped,
        interrupted_wells=int(inter), interrupted_share=float(inter / max(ever.sum(), 1) * 100),
        gap_buckets=dict(m3_5=bk(3, 5), m6_11=bk(6, 11), m12_23=bk(12, 23), m24plus=bk(24, 999)),
        cohort_n=int(coh.sum()), cohort_survival=surv,
        restart_pct=restarts, stop_pct=stops, months=list(range(3, N - 2)))

    # ---------- GOR ----------
    ov = np.nansum(oil[:, LAST12], axis=1) * M3_BBL                   # bbl, last 12 months
    gv = np.nansum(gas[:, LAST12], axis=1) * E3M3_MCF * 1000          # scf
    om = ov > 0
    gor = np.where(om, gv / np.where(om, ov, 1), np.nan)
    cls = np.full(len(ids), "oil", dtype=object)
    if df is not None:
        sub = df.substance.fillna("").values
        cls = np.where(np.char.find(sub.astype(str), "BITUMEN") >= 0, "bitumen", "oil")
        res["bitumen"] = dict(producing_wells_bitumen=int(((cls == "bitumen") & p12).sum()),
                              oil_volume_share_bitumen=float(ov[cls == "bitumen"].sum() / max(ov.sum(), 1) * 100))
    bins = [0, 1, 100, 300, 1000, 3000, 10000, 1e12]
    def gorsum(mask):
        x = gor[mask & om]
        return dict(n=int(len(x)), no_gas=int((x <= 0).sum()), median_with_gas=float(np.median(x[x > 0])) if (x > 0).any() else None,
                    hist=np.histogram(x, bins)[0].tolist())
    res["gor"] = {c: gorsum(cls == c) for c in sorted(set(cls.tolist())) if gorsum(cls == c)["n"] >= 30}

    # ---------- new-well productivity by first production year ----------
    if df is not None:
        spud = pd.to_datetime(df.spud_date).values
        newish = (spud >= np.datetime64("2021-01-01")) & (first >= 1) & (first <= 51)
        horiz = df.horizontal.fillna("").astype(str).str.upper().str.contains("HORIZ").values
        rows = []
        for i in np.where(newish)[0]:
            a = first[i]; sl = slice(a, a + 6)
            o6 = np.nansum(oil[i, sl]); g6 = np.nansum(gas[i, sl])
            if o6 > 0 and o6 * M3_BBL > g6 * E3M3_MCF * 1000 / 100:      # oil well if oil is a real part of the output
                rate = o6 / DIM[sl].sum() * M3_BBL; k = "oil"
            elif g6 > 0:
                rate = g6 / DIM[sl].sum() * E3M3_MCF; k = "gas"
            else:
                continue
            yr = (START + int(a)).year
            rows.append((k, yr, rate, bool(horiz[i])))
        d = pd.DataFrame(rows, columns=["cls", "year", "rate", "horiz"])
        out = []
        for (k, y), g_ in d.groupby(["cls", "year"]):
            if len(g_) >= 30:
                out.append(dict(cls=k, year=int(y), n=int(len(g_)), median=float(g_.rate.median()), p25=float(g_.rate.quantile(.25)), p75=float(g_.rate.quantile(.75)),
                                horizontal_share=float(g_.horiz.mean() * 100)))
        hz = {}
        for k in ("oil", "gas"):
            for h in (True, False):
                x = d[(d.cls == k) & (d.horiz == h)].rate
                if len(x) >= 30:
                    hz[f"{k}_{'horizontal' if h else 'other'}"] = dict(n=int(len(x)), median=float(x.median()))
        res["vintage"] = dict(groups=out, by_drill=hz, new_wells=int(len(d)))

        # ---------- licensee concentration (wells producing in the last 12 months) ----------
        nm = df.licensee_name.fillna("(none)").where(p12)
        w = nm[p12].value_counts()
        ow = pd.Series(ov[p12], index=nm[p12].values).groupby(level=0).sum()
        gw = pd.Series(gv[p12], index=nm[p12].values).groupby(level=0).sum()
        sw, cw = topn_shares(w); so, co = topn_shares(ow[ow > 0]); sg, cg = topn_shares(gw[gw > 0])
        res["operators"] = dict(licensees=int(len(w)), wells=int(w.sum()), top_wells=sw, top_oil=so, top_gas=sg,
                                curve_wells=cw, curve_oil=co, curve_gas=cg,
                                small_licensees=int((w < 10).sum()), small_share=float(w[w < 10].sum() / w.sum() * 100),
                                none_share=float(w.get("(none)", 0) / w.sum() * 100))
    return res


if __name__ == "__main__":
    prov, folder = sys.argv[1].lower(), sys.argv[2]
    cache = sys.argv[3] if len(sys.argv) > 3 else "/tmp/tw_cache"
    allr = json.load(open(OUT)) if os.path.exists(OUT) else {}
    allr[prov.upper()] = study(prov, folder, cache)
    json.dump(allr, open(OUT, "w"))
    print(prov, "ok", {k: (v if not isinstance(v, (dict, list)) else "...") for k, v in allr[prov.upper()].items()})
