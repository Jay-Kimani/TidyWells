import importlib.util
from datetime import date, datetime
from pathlib import Path

spec = importlib.util.spec_from_file_location("watch", Path(__file__).resolve().parents[1] / "posts" / "watch.py")
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def test_expected_latest_month():
    assert w.expected_latest(date(2026, 11, 4)) == "2026-09"   # early November: September is the newest to expect
    assert w.expected_latest(date(2026, 11, 12)) == "2026-10"  # after the lag: October
    assert w.expected_latest(date(2026, 1, 20)) == "2025-12"   # year boundary
    assert w.expected_latest(date(2026, 1, 3)) == "2025-11"


def test_stale_issue_only_when_behind():
    assert w.stale_issue("2026-09", date(2026, 11, 4)) is None
    i = w.stale_issue("2026-09", date(2026, 11, 20))
    assert i and "2026-10" in i["title"]


def test_bcer_issue_only_when_file_is_newer():
    built = datetime(2026, 11, 4)
    assert w.bcer_issue(datetime(2026, 11, 1), built) is None
    assert w.bcer_issue(None, built) is None
    assert "2026-11-10" in w.bcer_issue(datetime(2026, 11, 10, 9), built)["title"]
