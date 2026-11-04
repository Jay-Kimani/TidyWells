"""Loaders for Petrinex Alberta public data files (you download them yourself).

All identifiers are read as text so leading zeros survive. Nothing is uploaded.
Volumes: liquids in m3, gas in 10^3 m3 per month.
"""
from __future__ import annotations

import glob
import os
import zipfile
from typing import Iterable, Sequence

import pandas as pd

M3_TO_BBL = 6.28981
E3M3_TO_MCF = 35.3147

_STATUS = {
    "issued": "Issued", "amended": "Amended", "abandoned": "Abandoned",
    "reccertified": "RecCertified", "recexempt": "RecExempt",
    "suspension": "Suspension", "cancelled": "Cancelled",
    "re-entered": "Re-Entered", "reentered": "Re-Entered",
}


def _read_csv(path, **kw) -> pd.DataFrame:
    """Read a CSV, or the single CSV inside a zip, as text."""
    path = os.fspath(path)
    kw.setdefault("dtype", str)
    kw.setdefault("encoding_errors", "replace")
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise ValueError(f"{path}: expected one CSV inside, found {len(names)}")
            with z.open(names[0]) as f:
                return pd.read_csv(f, **kw)
    return pd.read_csv(path, **kw)


def normalize_status(s: pd.Series) -> pd.Series:
    key = s.str.strip().str.lower()
    return key.map(_STATUS).fillna(s.str.strip())


def read_well_licence(path) -> pd.DataFrame:
    """Petrinex 'Well Licence' download -> one row per licence."""
    d = _read_csv(path)
    out = pd.DataFrame({
        "licence_number": d["LicenceNumber"].str.strip().str.zfill(7),
        "licence_status": normalize_status(d["LicenceStatus"]),
        "licence_status_date": pd.to_datetime(d["LicenceStatusDate"], errors="coerce"),
        "issue_date": pd.to_datetime(d["LicenceIssueDate"], errors="coerce"),
        "licensee_code": d["Licensee"].str.strip(),
        "licensee_name": d["LicenseeName"].str.strip(),
        "surface_location": d["LicenceLocation"].str.strip(),
        "well_purpose": d.get("WellPurpose"),
        "substance": d.get("WellSubstance"),
        "orphan": d.get("OrphanWellFlg", pd.Series("N", index=d.index)).str.upper().eq("Y"),
    })
    return out


def read_well_infrastructure(path) -> pd.DataFrame:
    """Petrinex 'Well Infrastructure' download -> one row per well ID.

    Keeps the link from well_id (the ID used in production files) to licence_number.
    """
    cols = ["WellID", "LicenceNumber", "WellName", "ConfidentialType", "WellStatusFluid",
            "WellStatusMode", "WellStatusType", "WellStatusStructure", "WellStatusDate",
            "SpudDate", "HorizontalDrill", "FinalTotalDepth", "Field", "FieldName",
            "PoolDeposit", "PoolDepositName", "LinkedFacilityOperatorBAID",
            "LinkedFacilityOperatorLegalName"]
    d = _read_csv(path, usecols=lambda c: c in cols)
    out = pd.DataFrame({
        "well_id": d["WellID"].str.strip(),
        "licence_number": d["LicenceNumber"].str.strip().str.zfill(7),
        "well_name": d["WellName"].str.strip(),
        "confidential": d["ConfidentialType"].str.strip().str.upper().ne("NON-CONFIDENTIAL"),
        "status_fluid": d["WellStatusFluid"], "status_mode": d["WellStatusMode"],
        "status_type": d["WellStatusType"], "status_structure": d["WellStatusStructure"],
        "status_date": pd.to_datetime(d["WellStatusDate"], errors="coerce"),
        "spud_date": pd.to_datetime(d["SpudDate"], errors="coerce"),
        "horizontal": d["HorizontalDrill"],
        "total_depth_m": pd.to_numeric(d["FinalTotalDepth"], errors="coerce"),
        "field_name": d["FieldName"], "pool_name": d["PoolDepositName"],
        "operator_code": d["LinkedFacilityOperatorBAID"],
        "operator_name": d["LinkedFacilityOperatorLegalName"],
    })
    return out


def _expand(paths, province: str | None = None) -> list[str]:
    if isinstance(paths, (str, os.PathLike)):
        p = os.fspath(paths)
        if os.path.isdir(p):
            found = sorted(set(glob.glob(os.path.join(p, "Vol_*.csv*")) + glob.glob(os.path.join(p, "Vol_*.CSV*"))))
            if province:  # files are named like Vol_2026-01-AB.csv.zip
                found = [f for f in found if f"-{province.upper()}." in os.path.basename(f).upper()]
            return found
        return [p]
    return [os.fspath(x) for x in paths]


def read_volumetrics(paths, products: Sequence[str] = ("OIL", "GAS", "COND"),
                     activity: str = "PROD", province: str | None = None) -> pd.DataFrame:
    """Petrinex Conventional Volumetrics -> per-well monthly production, long format.

    paths: one file, a list of files, or a folder of Vol_*.csv(.zip) files.
    province: 'AB' or 'SK' to pick only that province's files when given a folder.
    Only well-level rows for the chosen activity and products are kept, which keeps
    memory small. Masked wells (***) are dropped and counted in df.attrs['masked_rows'].
    """
    keep = ["ProductionMonth", "OperatorBAID", "OperatorName", "ReportingFacilityID",
            "ActivityID", "ProductID", "FromToID", "FromToIDType", "Volume", "Hours",
            "ProrationProduct", "ProrationFactor"]
    parts, masked = [], 0
    for p in _expand(paths, province):
        d = _read_csv(p, usecols=lambda c: c in keep)
        d = d[(d["ActivityID"] == activity) & (d["FromToIDType"] == "WI") & d["ProductID"].isin(products)]
        masked += int((d["FromToID"] == "***").sum())
        parts.append(d[d["FromToID"] != "***"])
    if not parts:
        raise FileNotFoundError("no volumetric files found")
    d = pd.concat(parts, ignore_index=True)
    out = pd.DataFrame({
        "month": pd.PeriodIndex(d["ProductionMonth"], freq="M"),
        "well_id": d["FromToID"], "province": d["FromToID"].str[:2], "product": d["ProductID"],
        "volume": pd.to_numeric(d["Volume"], errors="coerce"),
        "hours": pd.to_numeric(d["Hours"], errors="coerce"),
        "prorated": d["ProrationProduct"].notna(),
        "facility_id": d["ReportingFacilityID"],
        "operator_code": d["OperatorBAID"], "operator_name": d["OperatorName"],
    })
    out.attrs["masked_rows"] = masked
    return out


def monthly_series(vol: pd.DataFrame, well_id: str, product: str, daily: bool = True) -> pd.Series:
    """Dense monthly series for one well and product (missing months = NaN).

    daily=True returns average rate per day (volume / days in month), which is what
    the decline curve works with. Liquids m3/d; gas 10^3 m3/d.
    """
    d = vol[(vol["well_id"] == well_id) & (vol["product"] == product)]
    s = d.groupby("month")["volume"].sum(min_count=1).sort_index()
    if s.empty:
        return s
    s = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"))
    if daily:
        s = s / s.index.days_in_month
    return s


def _latest(df: pd.DataFrame, key: str, date_col: str) -> pd.DataFrame:
    """One row per key: the one with the latest date (ties: last in file)."""
    return df.sort_values(date_col, kind="stable", na_position="first").drop_duplicates(key, keep="last")


def join_wells(vol: pd.DataFrame, infra: pd.DataFrame, lic: pd.DataFrame) -> pd.DataFrame:
    """One row per well with names, status and licensee, for wells that appear in vol.

    The source files repeat some well IDs and licence numbers; we keep the row with
    the latest status date for each.
    """
    wells = pd.DataFrame({"well_id": vol["well_id"].drop_duplicates()})
    w = wells.merge(_latest(infra, "well_id", "status_date"), on="well_id", how="left")
    lic2 = _latest(lic, "licence_number", "licence_status_date")
    return w.merge(lic2, on="licence_number", how="left", suffixes=("", "_lic"))
