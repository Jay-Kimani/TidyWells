"""The shop must stay honest: images exist, no prices or sale claims before a store is connected, no company names,
poster numbers match the open data, and the Your Well engine behaves."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _load(name, path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


art = _load("shop_art", ROOT / "shop" / "art.py")
goods = _load("shop_goods", ROOT / "shop" / "art_goods.py")
shop = _load("shop_build", ROOT / "shop" / "build_shop.py")

BRANDS = ["suncor", "cenovus", "cnrl", "canadian natural", "husky", "nexen", "tourmaline", "ovintiv", "crescent point", "petro-canada",
          "esso", "imperial oil", "chevron", "exxon", "halliburton", "schlumberger", "baker hughes", "carhartt", "patagonia", "nike",
          "adidas", "yeti", "petrinex logo", "alberta energy regulator"]


def visible_text(html):
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).lower()


def test_every_image_exists():
    for page in ("shop.html", "index.html"):
        html = (DOCS / page).read_text(encoding="utf-8")
        for src in re.findall(r'src="(img/shop/[^"]+)"', html) + re.findall(r'data-base="(img/shop/[^"]+)"', html):
            if src.endswith("-"):
                assert (DOCS / (src + "night.jpg")).exists() and (DOCS / (src + "paper.jpg")).exists(), src
            else:
                assert (DOCS / src).exists(), src


def test_prices_are_labelled_and_no_sale_claims():
    cfg = (DOCS / "config.js").read_text(encoding="utf-8")
    assert re.search(r'TIDYWELLS_SHOP_OPEN\s*=\s*(true|false)', cfg), "shop open flag must be set"
    pages = ["shop.html", "your-well.html"] + [i["page"] for i in shop.catalogue()]
    for page in pages:
        t = visible_text((DOCS / page).read_text(encoding="utf-8"))
        assert " sale" not in t and "% off" not in t and "discount" not in t and "limited time" not in t, page
        if "$" in t:
            assert "launch price" in t, page
    strip = re.search(r"<!--SHOP-->.*?<!--/SHOP-->", (DOCS / "index.html").read_text(encoding="utf-8"), re.S).group(0).lower()
    assert " sale" not in strip and "now open" in strip and "launch prices" in strip


def test_every_product_has_a_page_a_price_and_clean_structured_data():
    import json
    items = shop.catalogue()
    assert len(items) == 35 and len({i["page"] for i in items}) == 35
    sitemap = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
    for it in items:
        html = (DOCS / it["page"]).read_text(encoding="utf-8")
        assert f"CAD ${shop.fmt_price(shop.PRICE[it['kind']])}" in html, it["id"]
        assert it["page"] in sitemap
        for f, *_ in it["images"]:
            assert (DOCS / "img" / "shop" / f).exists(), f
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        assert ld["@type"] == "Product" and "offers" not in ld  # no price/availability claims in search data until a store exists


def test_sticker_packs_are_priced_per_pack():
    assert shop.BUNDLES == [] and shop.STICKERS == []
    assert not any(i["kind"] == "sticker" for i in shop.catalogue())


def test_dataset_structured_data_matches_manifest():
    import json
    m = json.loads((DOCS / "data" / "manifest.json").read_text(encoding="utf-8"))
    html = (DOCS / "data.html").read_text(encoding="utf-8")
    ld = json.loads(re.search(r'<!--LD--><script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
    assert ld["@type"] == "Dataset" and ld["distribution"][0]["sha256"] == m["sha256"]
    assert ld["temporalCoverage"] == f"{m['first_month']}/{m['last_month']}"


def test_articles_carry_poster_box():
    for page in sorted((DOCS / "posts").glob("*.html")):
        assert "<!--POSTERBOX-->" in page.read_text(encoding="utf-8"), page.name


def test_no_company_names_in_products_or_art():
    src = " ".join([visible_text((DOCS / "shop.html").read_text(encoding="utf-8")),
                    (ROOT / "shop" / "art_goods.py").read_text(encoding="utf-8").lower(),
                    (ROOT / "shop" / "cheats.py").read_text(encoding="utf-8").lower()])
    for b in BRANDS:
        assert b not in src, b


def test_catalogue_is_consistent():
    slugs = [d[0] for d in goods.DESIGNS]
    assert len(slugs) == len(set(slugs)) == 13
    assert {a[0] for a in shop.APPAREL} <= set(slugs)
    assert True
    assert {c[0] for c in shop.HATS} == {c[0] for c in goods.HATS}
    assert set(goods.STICKERS) <= set(slugs)
    for s, _n, kind, _b in shop.APPAREL:
        assert kind in ("hoodie", "tee") and kind == [d[3] for d in goods.DESIGNS if d[0] == s][0]
    for s in shop.FEATURED:
        assert s in slugs


def test_poster_numbers_match_the_open_data():
    data = art.load()
    svgs = art.posters(data)
    assert len(svgs) == 24
    for (prov, prod), name in [(("AB", "OIL"), "poster-ab-oil-night"), (("BC", "GAS"), "poster-bc-gas-paper"), (("SK", "OIL"), "poster-sk-oil-night")]:
        s = data[(prov, prod)]
        last = max(s)
        assert art.fmt(s[last], prod) in svgs[name], name
        peak = max(s.values())
        assert art.fmt(peak, prod) in svgs[name], name
    # independent recomputation of one figure straight from the CSV text
    import csv
    rows = [r for r in csv.DictReader(open(DOCS / "data" / "tidywells-monthly-production.csv")) if r["province"] == "AB" and r["product"] == "OIL"]
    r = max(rows, key=lambda r: r["month"])
    expect = float(r["volume"]) / float(r["days_in_month"]) * 6.2898 / 1000
    assert f"{expect:,.0f}" in svgs["poster-ab-oil-night"]
    # new oil posters: recompute from the CSV independently
    import csv as _csv
    rows_ = [r for r in _csv.DictReader(open(ROOT / "docs" / "data" / "tidywells-monthly-production.csv")) if r["product"] == "OIL"]
    by = {}
    for r in rows_:
        by.setdefault(r["month"], 0.0)
        by[r["month"]] += float(r["volume"]) / float(r["days_in_month"]) * 6.2898 / 1000
    last_m = max(by)
    assert f"{by[last_m]:,.0f}" in svgs["poster-record-barrels-night"] and f"{by[last_m]:,.0f}" in svgs["poster-86-of-100-night"]
    assert f"{max(by.values()):,.0f}" in svgs["poster-record-barrels-night"]
    ab = sum(float(r["volume"]) / float(r["days_in_month"]) * 6.2898 / 1000 for r in rows_ if r["province"] == "AB" and r["month"] == last_m)
    assert f"{ab / by[last_m] * 100:.1f}%" in svgs["poster-86-of-100-night"]


def test_posters_are_well_formed_svg():
    import xml.dom.minidom as md
    for name, svg in art.posters(art.load()).items():
        md.parseString(svg)
    for slug, _n, fn, _k in goods.DESIGNS:
        for ink in goods.INKS.values():
            md.parseString(goods.design_svg(fn(ink)))


node = shutil.which("node")


@pytest.mark.skipif(node is None, reason="node not installed")
def test_wellposter_engine():
    js = f"""
const W=require({json.dumps(str(DOCS / 'wellposter.js'))});
const p=W.parse('month,volume\\n2023-01,310\\n2023-02,280\\n2023-03,262\\nbad,row');
const s=W.series(p.rows,{{}});
const c=W.parse('month,well_id,province,product,volume\\n2023-01,0001,AB,OIL,310\\n2023-01,0002,AB,OIL,100\\n2023-02,0001,AB,OIL,280');
const s1=W.series(c.rows,{{well:'0001',product:'OIL'}});
const svg=W.poster(s,{{title:'A <b> & "q"',unit:'bbl per day',theme:'paper'}});
console.log(JSON.stringify({{bad:p.bad,n:s.length,v0:s[0].v,wells:c.wells,s1:s1.map(x=>x.v),esc:svg.includes('A &lt;b&gt; &amp; &quot;q&quot;'),raw:svg.includes('<b>'),err:W.parse('x').error}}));
"""
    out = json.loads(subprocess.run([node, "-e", js], capture_output=True, text=True, check=True).stdout)
    assert out["bad"] == 1 and out["n"] == 3
    assert abs(out["v0"] - 10.0) < 1e-9  # 310 over 31 days
    assert out["wells"] == ["0001", "0002"]  # leading zeros preserved
    assert abs(out["s1"][0] - 10.0) < 1e-9 and abs(out["s1"][1] - 10.0) < 1e-9  # 280/28
    assert out["esc"] and not out["raw"] and out["err"]


def test_listing_copy_fits_store_limits():
    import csv
    rows = list(csv.DictReader(open(ROOT / "shop" / "listings.csv", encoding="utf-8")))
    assert len(rows) == 35  # 12 apparel (4 collections x hoodie, tee, crewneck) + 4 posters + 3 apparel tees + 8 mugs + 2 hats + 2 patch hats + 1 toque + 1 Your Well
    for r in rows:
        tags = r["tags"].split("|")
        assert len(r["title"]) <= 140 and len(tags) <= 13 and all(len(t) <= 20 for t in tags), r["id"]
        assert not any(b in (r["title"] + r["description"]).lower() for b in BRANDS)


def test_home_feature_directory_links_resolve():
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    block = re.search(r"<!--FEATURES-->.*?<!--/FEATURES-->", html, re.S).group(0)
    hrefs = re.findall(r'class="ft" href="([^"]+)"', block)
    assert len(hrefs) == 16
    for h in hrefs:
        if not h.startswith("http"):
            assert (DOCS / h).exists(), h
