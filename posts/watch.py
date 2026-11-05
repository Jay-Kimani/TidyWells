"""Release watcher. Prints a JSON list of GitHub issues the scheduled workflow should open (title + body), de-duplicated by title.
  1. The BC Energy Regulator production file changed since the last build (Last-Modified is newer than our data build).
  2. Our dataset is behind: a newer month should be public by now (regulators publish about a month after month end).
Nothing is downloaded. Petrinex has no stable public file URL we can check, so Alberta and Saskatchewan rely on rule 2.
Usage: python posts/watch.py [--offline]"""
import csv
import json
import sys
import urllib.request
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "docs" / "data" / "tidywells-monthly-production.csv"
MANIFEST = ROOT / "docs" / "data" / "manifest.json"
BC_URL = "https://iris.bcogc.ca/download/prod_csv.zip"
LAG_DAYS = 12  # newest month is expected once this many days of the next month have passed


def mi(s):
    return int(s[:4]) * 12 + int(s[5:7]) - 1


def ms(i):
    return f"{i // 12}-{i % 12 + 1:02d}"


def latest_month(path=CSV):
    return max(r["month"] for r in csv.DictReader(open(path, newline="")))


def expected_latest(today):
    """Newest month that should be public: last month, once LAG_DAYS of this month have passed; otherwise the month before."""
    cur = today.year * 12 + today.month - 1
    return ms(cur - 1 if today.day >= LAG_DAYS else cur - 2)


def stale_issue(latest, today):
    exp = expected_latest(today)
    if mi(latest) >= mi(exp):
        return None
    return {"title": f"Data update due: {exp} production data",
            "body": (f"The dataset ends at {latest}, but {exp} should be public by now.\n\n"
                     "1. Download the new Petrinex (AB, SK) and BCER files.\n"
                     "2. `python posts/monthly_agg.py ab|sk|bc FOLDER` for each province.\n"
                     "3. `python posts/update.py` (regenerates posts, scorecard, revisions, feed) and `python posts/verify_site.py`.\n"
                     "4. Review the diff, commit and push.\n\n_Opened automatically by posts/watch.py._")}


def bcer_issue(last_modified, data_built):
    """last_modified: datetime of the BCER file; data_built: datetime our data was last built."""
    if last_modified is None or last_modified <= data_built:
        return None
    d = last_modified.date().isoformat()
    return {"title": f"BCER production file updated {d}",
            "body": (f"The BC Energy Regulator production file changed on {d}, after our data was last built. "
                     "Re-download it, re-aggregate BC, and check the Data revisions page for restated months.\n\n_Opened automatically by posts/watch.py._")}


def fetch_last_modified(url=BC_URL):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "tidywells-watch (+https://tidywells.com)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        v = r.headers.get("Last-Modified")
    return parsedate_to_datetime(v).replace(tzinfo=None) if v else None


def built_time():
    try:
        return datetime.fromisoformat(json.load(open(MANIFEST))["built_utc"].replace("Z", "")[:19])
    except Exception:
        return datetime.fromtimestamp(CSV.stat().st_mtime)


if __name__ == "__main__":
    out = []
    s = stale_issue(latest_month(), date.today())
    if s:
        out.append(s)
    if "--offline" not in sys.argv:
        try:
            b = bcer_issue(fetch_last_modified(), built_time())
            if b:
                out.append(b)
        except Exception as e:  # a failed check must not fail the workflow
            print(f"BCER check skipped: {e}", file=sys.stderr)
    print(json.dumps(out))
