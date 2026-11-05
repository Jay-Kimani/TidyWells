"""Data revision tracker. Regulators restate past months after first publishing them. Each time the open dataset changes,
this script keeps a copy of the previous version (docs/data/vintages/), compares the two, and logs every restated or new month
in docs/data/revisions.json. It only detects revisions in months that were re-downloaded and re-aggregated.
Stdlib only. Run: python3 posts/revisions.py   (build_feed.py runs after it)."""
import csv
import hashlib
import json
import os
import sys
from datetime import date
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagetpl import page  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "docs" / "data" / "tidywells-monthly-production.csv"
VDIR = ROOT / "docs" / "data" / "vintages"
LOG = ROOT / "docs" / "data" / "revisions.json"
PROV = {"AB": "Alberta", "SK": "Saskatchewan", "BC": "British Columbia"}


def read(path):
    return {(r["province"], r["product"], r["month"]): (float(r["volume"]), int(r["wells_producing"])) for r in csv.DictReader(open(path, newline=""))}


def diff(old, new):
    changed, added = [], []
    for k, (v, w) in new.items():
        if k not in old:
            added.append(k)
        elif old[k] != (v, w):
            ov, ow = old[k]
            changed.append({"series": f"{k[0]}-{k[1]}", "month": k[2], "old_volume": ov, "new_volume": v,
                            "change_pct": round((v - ov) / ov * 100, 3) if ov else None, "old_wells": ow, "new_wells": w})
    removed = [k for k in old if k not in new]
    return changed, added, removed


def update(csv_path=CSV, vdir=VDIR, log_path=LOG, today=None):
    today = today or os.environ.get("TW_TODAY") or date.today().isoformat()
    vdir.mkdir(parents=True, exist_ok=True)
    data = Path(csv_path).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    log = json.load(open(log_path)) if Path(log_path).exists() else {
        "about": "Each entry is a time the open dataset changed. 'changed' lists months that were already published and now have a different value.",
        "vintages": [], "events": []}
    if log["vintages"] and log["vintages"][-1]["sha256"] == sha:
        return log
    new = read(csv_path)
    last_month = max(k[2] for k in new)
    fname = f"{today}-{sha[:8]}.csv"
    (vdir / fname).write_bytes(data)
    if log["vintages"]:
        old = read(vdir / log["vintages"][-1]["file"])
        changed, added, removed = diff(old, new)
        log["events"].append({"detected": today, "from": log["vintages"][-1]["sha256"][:8], "to": sha[:8],
                              "new_months": sorted({k[2] for k in added}), "removed_rows": len(removed), "changed": changed})
    log["vintages"].append({"detected": today, "file": fname, "sha256": sha, "rows": len(new), "last_month": last_month})
    json.dump(log, open(log_path, "w"), indent=1)
    open(log_path, "a").write("\n")
    return log


def build_page(log):
    v = log["vintages"]
    ev = log["events"]
    allch = [c for e in ev for c in e["changed"]]
    h = ["<h1>Data revisions</h1>",
         "<p>Regulators sometimes restate production for months they already published. If you build on a number without knowing that, you can be quietly wrong. "
         "Every time our open dataset changes we keep the earlier version, compare the two and log what moved. Nobody else publishes this for Canadian production data.</p>",
         "<h2>How it works</h2><ul>"
         "<li>Each version of the <a href=\"data.html\">open dataset</a> is saved under <code>docs/data/vintages/</code> with its SHA-256 fingerprint.</li>"
         "<li>A script compares the new version with the previous one and writes every restated or new month to <a href=\"data/revisions.json\">revisions.json</a>.</li>"
         "<li><b>Limit:</b> we can only see a revision in a month we re-downloaded. Each release we re-pull the most recent months, not the whole history, so a late restatement of an old month can go unseen.</li></ul>"]
    h.append(f"<h2>Where things stand</h2><p>{len(v)} version{'s' if len(v) != 1 else ''} recorded, {len(ev)} update{'s' if len(ev) != 1 else ''} compared, "
             f"{len(allch)} restated value{'s' if len(allch) != 1 else ''} found so far.</p>")
    if not ev:
        h.append(f"<p>Tracking began on {v[0]['detected']} with data through {v[0]['last_month']}. No later version exists yet, so there is nothing to compare. This page fills in on the next data update.</p>")
    else:
        h.append('<div class="tw"><table><tr><th>Detected</th><th>New months</th><th>Restated values</th><th>Largest change</th></tr>' + "".join(
            f'<tr><td>{e["detected"]}</td><td>{escape(", ".join(e["new_months"]) or "none")}</td><td>{len(e["changed"])}</td><td>' +
            (max(e["changed"], key=lambda c: abs(c["change_pct"] or 0))["month"] + " " + max(e["changed"], key=lambda c: abs(c["change_pct"] or 0))["series"] +
             f' ({max((c["change_pct"] or 0 for c in e["changed"]), key=abs):+.2f}%)' if e["changed"] else "none") + "</td></tr>" for e in reversed(ev)) + "</table></div>")
        if allch:
            h.append("<h3>Most recent restated values</h3><div class=\"tw\"><table><tr><th>Series</th><th>Month</th><th>Before</th><th>After</th><th>Change</th></tr>" + "".join(
                f'<tr><td>{PROV[c["series"][:2]]} {c["series"][3:].lower()}</td><td>{c["month"]}</td><td>{c["old_volume"]:,.1f}</td><td>{c["new_volume"]:,.1f}</td>'
                f'<td>{(str(c["change_pct"]) + "%") if c["change_pct"] is not None else "–"}</td></tr>' for c in list(reversed(allch))[:25]) + "</table></div>")
    h.append("<h2>Versions</h2><div class=\"tw\"><table><tr><th>Detected</th><th>Data through</th><th>Rows</th><th>SHA-256 (start)</th><th>File</th></tr>" + "".join(
        f'<tr><td>{x["detected"]}</td><td>{x["last_month"]}</td><td>{x["rows"]}</td><td><code>{x["sha256"][:12]}</code></td><td><a href="data/vintages/{x["file"]}">{x["file"]}</a></td></tr>' for x in reversed(v)) + "</table></div>")
    h.append('<p class="muted" style="margin-top:22px;font-size:14px">Volumes are the regulators’ units (oil m³, gas 10³ m³). Informational only, not investment, legal or engineering advice. Code: <code>posts/revisions.py</code>.</p>')
    return "\n".join(h)


if __name__ == "__main__":
    log = update()
    (ROOT / "docs" / "revisions.html").write_text(
        page("revisions.html", "Data revisions", "A running log of what the Alberta, Saskatchewan and BC regulators restated after first publishing production numbers.",
             build_page(log), css=".tw{overflow-x:auto}"), encoding="utf-8")
    print("vintages", len(log["vintages"]), "events", len(log["events"]))
