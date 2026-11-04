import zipfile
import pandas as pd
import tidywells as tw

LIC = """LicenceType,LicenceNumber,LicenceIssueDate,LicenceStatus,LicenceStatusDate,Licensee,LicenseeName,LicenceLocation,WellPurpose,WellSubstance,OrphanWellFlg
WELL,0000001,1949-05-23,ABANDONED,2016-03-14,A001,FAKE ENERGY LTD,08-09-051-25W4,X,Y,N
WELL,0000002,1950-01-01,RecCertified,2016-03-14,A002,TEST CO,05-25-049-26W4,X,Y,Y
WELL,0000003,1951-01-01,RECCERTIFIED,2016-03-14,A002,TEST CO,05-25-049-26W4,X,Y,N
"""
INF = """WellID,LicenceNumber,WellName,ConfidentialType,WellStatusFluid,WellStatusMode,WellStatusType,WellStatusStructure,WellStatusDate,SpudDate,HorizontalDrill,FinalTotalDepth,Field,FieldName,PoolDeposit,PoolDepositName,LinkedFacilityOperatorBAID,LinkedFacilityOperatorLegalName
ABWI100010100115W400,0000001,FAKE 1-1-1-15,NON-CONFIDENTIAL,OIL,PROD,PUMP,SINGLE,2020-01-01,2019-01-01,,1000,1,F,1,P,A001,FAKE ENERGY LTD
ABWI100020200215W400,2,FAKE 2,CONFIDENTIAL,GAS,PROD,FLOW,SINGLE,2020-01-01,2019-01-01,,1000,1,F,1,P,A002,TEST CO
"""
def vol(month, rows):
    h = "ProductionMonth,OperatorBAID,OperatorName,ReportingFacilityID,ActivityID,ProductID,FromToID,FromToIDType,Volume,Hours,ProrationProduct,ProrationFactor\n"
    return h + "".join(f"{month},A001,FAKE,ABBT1,{a},{p},{w},{t},{v},,,\n" for a, p, w, t, v in rows)


def test_licence_pads_and_normalizes(tmp_path):
    f = tmp_path / "l.csv"; f.write_text(LIC)
    d = tw.read_well_licence(f)
    assert d.licence_number.tolist() == ["0000001", "0000002", "0000003"]
    assert d.licence_status.tolist() == ["Abandoned", "RecCertified", "RecCertified"]
    assert d.orphan.tolist() == [False, True, False]


def test_infra_links_well_to_licence(tmp_path):
    f = tmp_path / "i.csv"; f.write_text(INF)
    d = tw.read_well_infrastructure(f)
    assert d.loc[1, "licence_number"] == "0000002"
    assert d.confidential.tolist() == [False, True]


def test_volumetrics_filters_masks_and_zip(tmp_path):
    w = "ABWI100010100115W400"
    for m, v in [("2024-01", 31.0), ("2024-02", 29.0), ("2024-04", 30.0)]:
        csv = vol(m, [("PROD", "OIL", w, "WI", v), ("PROD", "OIL", "***", "WI", 5),
                      ("PROD", "WATER", w, "WI", 9), ("DISP", "OIL", w, "WI", 9),
                      ("PROD", "OIL", "ABBT1", "BT", 9)])
        with zipfile.ZipFile(tmp_path / f"Vol_{m}-AB.csv.zip", "w") as z:
            z.writestr(f"Vol_{m}-AB.CSV", csv)
    d = tw.read_volumetrics(tmp_path)
    assert len(d) == 3 and set(d["product"]) == {"OIL"}
    assert d.attrs["masked_rows"] == 3
    s = tw.monthly_series(d, w, "OIL")
    assert len(s) == 4 and s.isna().sum() == 1          # March missing stays NaN
    assert s.iloc[0] == 1.0                             # 31 m3 over 31 days


def test_join_wells(tmp_path):
    (tmp_path / "l.csv").write_text(LIC); (tmp_path / "i.csv").write_text(INF)
    v = pd.DataFrame({"well_id": ["ABWI100010100115W400"], "month": [pd.Period("2024-01")]})
    j = tw.join_wells(v, tw.read_well_infrastructure(tmp_path / "i.csv"), tw.read_well_licence(tmp_path / "l.csv"))
    assert j.loc[0, "licensee_name"] == "FAKE ENERGY LTD"


def test_join_keeps_one_row_per_well(tmp_path):
    inf = INF + "ABWI100010100115W400,0000001,FAKE OLD,NON-CONFIDENTIAL,OIL,PROD,PUMP,SINGLE,2010-01-01,2009-01-01,,1000,1,F,1,P,A001,FAKE ENERGY LTD\n"
    (tmp_path / "l.csv").write_text(LIC); (tmp_path / "i.csv").write_text(inf)
    v = pd.DataFrame({"well_id": ["ABWI100010100115W400", "ABWI100010100115W400"], "month": [pd.Period("2024-01")] * 2})
    j = tw.join_wells(v, tw.read_well_infrastructure(tmp_path / "i.csv"), tw.read_well_licence(tmp_path / "l.csv"))
    assert len(j) == 1 and j.loc[0, "well_name"] == "FAKE 1-1-1-15"


def test_province_filter_on_folder(tmp_path):
    for prov in ("AB", "SK"):
        w = f"{prov}WI100010100115W400"
        (tmp_path / f"Vol_2024-01-{prov}.csv").write_text(vol("2024-01", [("PROD", "OIL", w, "WI", 10)]))
    assert len(tw.read_volumetrics(tmp_path)) == 2
    d = tw.read_volumetrics(tmp_path, province="SK")
    assert len(d) == 1 and d["province"].iloc[0] == "SK"


def test_bc_production_sums_zones_and_uses_days(tmp_path):
    f = tmp_path / "zone_prd.csv"
    f.write_text('"ZONE_PRD FILE"\n'
        '"Wa_num","Prod_period","UWI","Gas_prod_vol (e3m3)","Oil_prod_vol (m3)","Water_prod_vol (m3)","Cond_prod_vol (m3)","Prod_days "\n'
        '"00101","202401","100060608613W600","10","3","1","0","20"\n'
        '"00101","202401","100060608613W600","5","2","1","0","15"\n'
        '"00101","202403","100060608613W600","8","0","1","0","31"\n')
    d = tw.read_bc_production(f)
    g = d[(d.well_id == "100060608613W600") & (d["product"] == "GAS")].set_index("month")
    assert g.loc[pd.Period("2024-01"), "volume"] == 15 and g.loc[pd.Period("2024-01"), "days"] == 20
    s = tw.monthly_series(d, "100060608613W600", "GAS", use_producing_days=True)
    assert s.iloc[0] == 15 / 20 and s.isna().iloc[1]
    assert (d.province == "BC").all()
