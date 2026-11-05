import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("scorecard", Path(__file__).resolve().parents[1] / "posts" / "scorecard.py")
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)


B = 2022 * 12


def series():
    return {B + i: 100 + (i % 12) * 2 + i * 0.1 for i in range(0, 40)}


def test_forecast_uses_no_future_data():
    s = series()
    origin, target = 30, 33
    base = {m: sc.forecast(m, s, origin, target) for m in sc.METHODS}
    s2 = dict(s)
    for k in range(origin + 1, 40):
        s2[k] = 1e6  # change everything after the origin
    assert {m: sc.forecast(m, s2, origin, target) for m in sc.METHODS} == base


def test_methods_on_a_known_series():
    s = {i: 10.0 for i in range(30)}
    assert sc.forecast("naive", s, 20, 22) == 10.0
    assert sc.forecast("seasonal_naive", s, 20, 22) == 10.0
    assert sc.forecast("seasonal_trend", s, 20, 22) == 10.0
    s = {i: 10.0 * (1.1 if i >= 18 else 1.0) for i in range(30)}  # 10% growth in the last year
    assert abs(sc.forecast("seasonal_trend", s, 28, 29) - 11.0) < 1e-9
    assert sc.forecast("seasonal_naive", {20: 5}, 20, 40) is None  # no data a year before the target


def test_live_log_is_append_only_and_grades_later(tmp_path, monkeypatch):
    monkeypatch.setattr(sc, "LOG", tmp_path / "f.json")
    data = {k: dict(series()) for k in sc.SERIES}
    log = sc.update_log(data, "abc")
    first = json.dumps(log["entries"][:5])
    n = len(log["entries"])
    assert n == len(sc.SERIES) * 3 * 3 and all(e["actual"] is None for e in log["entries"])
    log2 = sc.update_log(data, "other-hash")  # same month again: nothing added, nothing rewritten
    assert len(log2["entries"]) == n and json.dumps(log2["entries"][:5]) == first
    for k in data:  # a new month appears: forecasts for it get graded, old forecast values stay
        data[k][B + 40] = 130.0
    log3 = sc.update_log(data, "new")
    graded = [e for e in log3["entries"] if e["actual"] is not None]
    assert graded and all(e["ape_pct"] is not None for e in graded)
    old = {(e["data_through"], e["series"], e["method"], e["target"]): e["forecast"] for e in log["entries"]}
    key = lambda e: (e["data_through"], e["series"], e["method"], e["target"])
    assert all(old[key(e)] == e["forecast"] for e in log3["entries"] if key(e) in old)
