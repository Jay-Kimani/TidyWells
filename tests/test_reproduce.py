"""The 'Reproduce these numbers' script on a snapshot page must print the figures that the page shows."""
import html
import io
import re
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def run_block(page):
    t = (ROOT / "docs" / "posts" / page).read_text(encoding="utf-8")
    code = html.unescape(re.search(r'<!--REPRO-->.*?<pre><code>(.*?)</code></pre>', t, re.S).group(1))
    data = (ROOT / "docs" / "data" / "tidywells-monthly-production.csv").read_bytes()
    out = io.StringIO()
    with mock.patch("urllib.request.urlopen", return_value=io.BytesIO(data)), redirect_stdout(out):
        exec(compile(code, "repro", "exec"), {})
    return t, out.getvalue().strip().splitlines()


def test_snapshot_script_matches_page_figures():
    for page in ("snapshot-2026-09.html", "snapshot-2024-01.html"):
        t, lines = run_block(page)
        assert len(lines) == 6
        text = re.sub(r"<[^>]+>", " ", t.split("<!--REPRO-->")[0])
        for ln in lines:
            prov, prod, val = ln.split()
            assert val in text, (page, ln)
