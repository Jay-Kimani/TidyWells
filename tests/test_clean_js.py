"""The browser cleaner (docs/clean.js) must give the same rows as the Python loaders."""
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

import tidywells as tw

JS = Path(__file__).resolve().parents[1] / "docs" / "clean.js"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

VOL_HEADER = ("ProductionMonth,OperatorBAID,OperatorName,ReportingFacilityID,ReportingFacilityProvinceState,ReportingFacilityType,"
              "ReportingFacilityIdentifier,ReportingFacilityName,ReportingFacilitySubType,ReportingFacilitySubTypeDesc,ReportingFacilityLocation,"
              "FacilityLegalSubdivision,FacilitySection,FacilityTownship,FacilityRange,FacilityMeridian,SubmissionDate,ActivityID,ProductID,"
              "FromToID,FromToIDProvinceState,FromToIDType,FromToIDIdentifier,Volume,Energy,Hours,CCICode,ProrationProduct,ProrationFactor,Heat")


def vol_row(month, op, name, fac, act, prod, wid, vol, hours, pro=""):
    return (f"{month},{op},{name},{fac},AB,BT,1,F,1,X,1-1-1-1,1,1,1,1,4,2026-10-08,{act},{prod},{wid},AB,"
            f"{'WI' if wid != '' else ''},{wid[-6:]},{vol},,{hours},,{pro},,")


def make_vol(path):
    rows = [VOL_HEADER,
            vol_row("2026-01", "00012", '"ACME, ENERGY LTD."', "ABBT0001", "PROD", "OIL", "ABWI100010101001W500", "12.5", "744", "OIL"),
            vol_row("2026-01", "00012", '"ACME, ENERGY LTD."', "ABBT0001", "PROD", "GAS", "ABWI100010101001W500", "0", "744"),
            vol_row("2026-01", "00099", "PLAIN CO", "ABBT0002", "PROD", "OIL", "***", "5", "700"),
            vol_row("2026-01", "00099", "PLAIN CO", "ABBT0002", "DISP", "OIL", "ABWI100010101002W500", "5", "700"),
            vol_row("2026-01", "00099", "PLAIN CO", "ABBT0002", "PROD", "WATER", "ABWI100010101002W500", "5", "700"),
            vol_row("2026-02", "00099", "PLAIN CO", "ABBT0002", "PROD", "COND", "ABWI100010101002W500", "", "NA", "NA"),
            vol_row("2026-02", "00099", "PLAIN CO", "ABBT0002", "PROD", "OIL", "ABWI100010101002W500", "1234.56", "650", "GAS"),
            ]
    Path(path).write_text("\r\n".join(rows) + "\r\n", encoding="utf-8")


def make_bc(path):
    hdr = ('"Wa_num","Compltn_event_seq","Prod_period","UWI","Area_code","Formtn_code","Pool_seq","Gas_prod_vol (e3m3)",'
           '"Oil_prod_vol (m3)","Water_prod_vol (m3)","Cond_prod_vol (m3)","Prod_days ","Gas_prod_cum (e3m3)"')
    body = ['"ZONE_PRD_TEST FILE"', hdr,
            '"00101","00","202501","100060608613W600","2000","4535","A","5.9","36.4","1036.5","0","31","5.9"',
            '"00101","00","202501","100060608613W600","2000","4536","B","1.1","0.6","3.5","0","20","1.1"',
            '"00101","00","202502","100060608613W600","2000","4535","A","5.2","35.1","936.9","0","28","11.1"',
            '"00102","00","202501","100070608613W600","2000","4535","A","","","","","","0"']
    Path(path).write_text("\n".join(body) + "\n", encoding="utf-8")


def run_js(src, path):
    code = ("const c=require(%r);const t=require('fs').readFileSync(%r,'utf8');const cl=c.sniff(t.slice(0,4000),{});"
            "const r=new c.CsvReader(x=>cl.row(x));r.feed(t);r.end();const o=cl.finish();"
            "process.stdout.write(JSON.stringify({kind:cl.constructor.kind,csv:c.toCsv(o),stats:o.stats}))" % (str(src), str(path)))
    return json.loads(subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout)


def js_frame(out):
    from io import StringIO
    return pd.read_csv(StringIO(out["csv"]), dtype=str, keep_default_na=False)


def test_volumetrics_match(tmp_path):
    f = tmp_path / "Vol_2026-01-AB.csv"
    make_vol(f)
    py = tw.read_volumetrics(f)
    out = run_js(JS, f)
    js = js_frame(out)
    assert out["kind"] == "volumetrics"
    assert out["stats"]["masked"] == py.attrs["masked_rows"] == 1
    assert len(js) == len(py) == 4
    assert list(js["month"]) == [str(m) for m in py["month"]]
    for col in ["well_id", "province", "product", "facility_id", "operator_code", "operator_name"]:
        assert list(js[col]) == list(py[col].fillna("")), col
    for col in ["volume", "hours"]:
        a = pd.to_numeric(js[col].replace("", None))
        assert a.fillna(-1).round(9).tolist() == py[col].fillna(-1).round(9).tolist(), col
    assert list(js["prorated"] == "True") == list(py["prorated"])
    assert "ACME, ENERGY LTD." in js["operator_name"].tolist()  # comma inside quotes survives


def test_bc_match(tmp_path):
    f = tmp_path / "zone_prd_test.csv"
    make_bc(f)
    py = tw.read_bc_production(f)
    out = run_js(JS, f)
    js = js_frame(out)
    assert out["kind"] == "bc"
    assert len(js) == len(py)
    assert list(js["month"]) == [str(m) for m in py["month"]]
    assert list(js["well_id"]) == list(py["well_id"])
    assert list(js["product"]) == list(py["product"])
    assert pd.to_numeric(js["volume"]).round(9).tolist() == py["volume"].round(9).tolist()
    assert pd.to_numeric(js["days"].replace("", None)).fillna(-1).tolist() == py["days"].fillna(-1).tolist()


def test_unrecognised_file_is_rejected(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("a,b\n1,2\n")
    code = "const c=require(%r);console.log(c.sniff(require('fs').readFileSync(%r,'utf8'),{})===null)" % (str(JS), str(f))
    assert subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout.strip() == "true"
