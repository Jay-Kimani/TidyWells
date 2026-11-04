"""Data-quality counts for the 'what a naive load gets wrong' post.
Usage: python posts/dq_study.py {ab|sk|bc} FOLDER   (adds to posts/dq.json; counts only)"""
import csv
import io
import json
import os
import sys
import zipfile

import numpy as np
import pandas as pd

import tidywells as tw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dq.json")


def lost_zero_cols(raw):
    """Columns pandas would turn into numbers by default, and how many values lose leading zeros."""
    out = {}
    for c in raw.columns:
        s = raw[c].dropna().astype(str).str.strip()
        s = s[s != ""]
        if len(s) == 0:
            continue
        num = pd.to_numeric(s, errors="coerce")
        if num.notna().all() and s.str.match(r"^\d+$").all():
            lost = int((s.str.len() > s.str.lstrip("0").str.len()).sum())
            if lost:
                out[c] = dict(values_with_leading_zeros=lost, of=int(len(s)))
    return out


def main(prov, folder):
    res = {}
    if prov in ("ab", "sk"):
        P = prov.upper()
        rawi = tw.loaders._read_csv(os.path.join(folder, f"Well Infrastructure-{P}.csv.zip"))
        rawl = tw.loaders._read_csv(os.path.join(folder, f"Well Licence-{P}.csv.zip"))
        wid = rawi["WellID"].str.strip()
        ln_i, ln_l = rawi["LicenceNumber"].astype(str).str.strip(), rawl["LicenceNumber"].astype(str).str.strip()
        set_l_raw, set_l_clean = set(ln_l), set(ln_l.str.zfill(7))
        res.update(
            infra_rows=int(len(rawi)), infra_unique_wells=int(wid.nunique()), infra_duplicate_rows=int(len(rawi) - wid.nunique()),
            licence_rows=int(len(rawl)), licence_unique=int(ln_l.str.zfill(7).nunique()), licence_duplicate_rows=int(len(rawl) - ln_l.str.zfill(7).nunique()),
            infra_licence_match_raw=float(ln_i.isin(set_l_raw).mean() * 100), infra_licence_match_clean=float(ln_i.str.zfill(7).isin(set_l_clean).mean() * 100),
            blank_status_mode=int(rawi["WellStatusMode"].isna().sum()),
            bad_status_dates=int((pd.to_datetime(rawi["WellStatusDate"], errors="coerce").isna() & rawi["WellStatusDate"].notna()).sum()),
            missing_spud=int(rawi["SpudDate"].isna().sum()),
            lost_zero_infra=lost_zero_cols(rawi), lost_zero_licence=lost_zero_cols(rawl),
            licence_status_spellings=int(rawl["LicenceStatus"].dropna().nunique()), licence_status_clean=int(tw.loaders.normalize_status(rawl["LicenceStatus"].dropna()).nunique()))
        tot = masked = nfiles = 0
        for f in tw.loaders._expand(folder, P):
            d = tw.read_volumetrics(f, products=("OIL", "GAS", "COND"))
            tot += len(d); masked += int(d.attrs.get("masked_rows", 0)); nfiles += 1
        res.update(vol_files=nfiles, vol_rows_kept=tot, vol_rows_masked=masked)
    else:
        with open(os.path.join(folder, "well_index.csv"), encoding="utf-8", errors="replace") as f:
            hdr = next(csv.reader(f))
        dup = {h: hdr.count(h) for h in set(hdr) if hdr.count(h) > 1}
        res.update(index_columns=len(hdr), duplicate_header_names=dup)
        raw = tw.loaders._read_csv(os.path.join(folder, "zone_prd_2025_to_present.csv"), skiprows=1)
        res.update(zone_rows_2025_on=int(len(raw)), lost_zero_zone=lost_zero_cols(raw))
    return res


if __name__ == "__main__":
    prov, folder = sys.argv[1].lower(), sys.argv[2]
    d = json.load(open(OUT)) if os.path.exists(OUT) else {}
    d[prov.upper()] = main(prov, folder)
    json.dump(d, open(OUT, "w"), indent=1)
    print(json.dumps(d[prov.upper()], indent=1)[:1800])
