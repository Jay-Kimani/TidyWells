"""Snapshot hand-edited product galleries (images, alt text, view labels, description) from docs/product-*.html
into shop/galleries.json, which build_shop.py applies on top of its pick lists. Run this after editing a
product page by hand, so a later rebuild keeps the edit.  Usage: python3 shop/snapshot_galleries.py"""
import json, re
from html import unescape
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
out = {}
for f in sorted(DOCS.glob("product-*.html")):
    pid = f.stem[len("product-"):]
    if pid.split("-")[0] not in ("hoodie", "tee", "crewneck", "hat", "toque"):
        continue
    h = f.read_text(encoding="utf-8")
    m = re.search(r'<div class="pview">(.*?)<div class="sw"', h, re.S)
    if not m:
        continue
    imgs = [(a, unescape(b), int(w), int(hh)) for a, b, w, hh in re.findall(r'<img src="img/shop/([^"]+)" alt="([^"]*)" width="(\d+)" height="(\d+)"', m.group(1))]
    labs = [unescape(x) for x in re.findall(r'<button type="button" data-pi="\d+" aria-pressed="[a-z]+">(.*?)</button>', h)]
    d = re.search(r"<h2>About this design</h2><p>(.*?)</p>", h, re.S)
    pl = re.search(r'<p class="plead">(.*?)</p>', h, re.S)
    sp = re.search(r'<ul class="specs">(.*?)</ul>', h, re.S)
    if imgs and len(imgs) == len(labs) and d and pl and sp:
        out[pid] = {"images": imgs, "labels": labs, "desc": unescape(d.group(1)), "blurb": unescape(pl.group(1)),
                    "specs": [unescape(x) for x in re.findall(r"<li>(.*?)</li>", sp.group(1), re.S)]}
(Path(__file__).parent / "galleries.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(out), "galleries snapshotted")
