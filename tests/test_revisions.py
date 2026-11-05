import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("revisions", Path(__file__).resolve().parents[1] / "posts" / "revisions.py")
rv = importlib.util.module_from_spec(spec); spec.loader.exec_module(rv)

HDR = "province,product,month,volume,unit,wells_producing,days_in_month\n"


def write(p, rows):
    p.write_text(HDR + "".join(f"{a},{b},{c},{d},u,{e},30\n" for a, b, c, d, e in rows))


def test_detects_restated_and_new_months(tmp_path):
    csvp, vd, lg = tmp_path / "d.csv", tmp_path / "v", tmp_path / "r.json"
    write(csvp, [("AB", "OIL", "2026-08", 100.0, 10), ("AB", "OIL", "2026-09", 110.0, 11)])
    log = rv.update(csvp, vd, lg, today="2026-10-01")
    assert len(log["vintages"]) == 1 and not log["events"]
    assert len(rv.update(csvp, vd, lg, today="2026-10-02")["vintages"]) == 1  # unchanged data: nothing new
    write(csvp, [("AB", "OIL", "2026-08", 100.0, 10), ("AB", "OIL", "2026-09", 112.2, 11), ("AB", "OIL", "2026-10", 120.0, 12)])
    log = rv.update(csvp, vd, lg, today="2026-11-01")
    ev = log["events"][0]
    assert ev["new_months"] == ["2026-10"] and len(ev["changed"]) == 1
    c = ev["changed"][0]
    assert c["month"] == "2026-09" and c["old_volume"] == 110.0 and c["new_volume"] == 112.2 and abs(c["change_pct"] - 2.0) < 1e-9
    assert len(list(vd.glob("*.csv"))) == 2
