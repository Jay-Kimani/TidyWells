"""Writes docs/shop.html, docs/shop.css block in style.css and the home-page shop strip, and docs/img/shop previews.
Idempotent. Run after shop/art.py, art_goods.py, cheats.py + render.js have produced web previews in OUT/web
(only when previews change); CI just re-runs this script against the committed images.
Honesty rules: no prices, no 'on sale', no Buy buttons until window.TIDYWELLS_SHOP_URL / LINKS are set in config.js."""
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "posts"))
from pagetpl import page  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMG = "img/shop/"

POSTERS = [  # slug, title, blurb
    ("ab-oil", "Alberta Oil", "Monthly oil production, January 2022 to September 2026, with the peak month marked."),
    ("ab-gas", "Alberta Gas", "Alberta gas production through the winter peaks, drawn from the open dataset."),
    ("sk-oil", "Saskatchewan Oil", "Five years of Saskatchewan oil, the peak and the latest month labelled."),
    ("sk-gas", "Saskatchewan Gas", "Saskatchewan gas production, daily-rate basis."),
    ("bc-oil", "British Columbia Oil", "BC oil from the BC Energy Regulator files: the 2023 dip and the recovery."),
    ("bc-gas", "British Columbia Gas", "BC gas production, the sharpest growth of the three provinces."),
    ("five-years", "Five Years, Six Lines", "Oil and gas in three provinces as six small multiples on one sheet."),
    ("gas-season", "Gas Has a Season", "A radar of the calendar-month pattern in Alberta and BC gas."),
    ("decline-shape", "Shape of a Decline", "The Arps family b = 0 to 1.5, the curve every well-file reader should know."),
]
APPAREL = [  # slug, name, garment, blurb
    ("hyperbolic-decline", "Hyperbolic Decline: My Motivation", "hoodie", "For anyone whose enthusiasm follows an Arps curve."),
    ("arps-was-right", "Arps Was Right", "hoodie", "The 1945 equation, still undefeated."),
    ("shut-in-not-shut-down", "Shut-In, Not Shut Down", "hoodie", "A valve wheel and a distinction that matters."),
    ("wells-dont-retire", "Wells Don't Retire. They Decline.", "hoodie", "Respect the curve."),
    ("b-equals-1", "b = 1.0", "tee", "Harmonic decline, in monospace."),
    ("arps-equation", "The Arps Equation", "tee", "q(t) = qᵢ / (1 + b·Dᵢ·t)^(1/b), set in type."),
    ("leading-zeros-matter", "Leading Zeros Matter", "tee", "For everyone who has watched a spreadsheet eat a well ID."),
    ("check-the-units", "Check the Units", "tee", "m³, Mcf, MMcf, boe. Always."),
    ("gas-has-a-season", "Gas Has a Season", "tee", "Winter demand, drawn as a wave."),
    ("bounded-optimism", "Bounded Fit. Bounded Optimism.", "tee", "0 ≤ b ≤ 2."),
    ("p50-energy", "P50 Energy", "tee", "Not optimistic. Not pessimistic. Just the median."),
    ("licensed-not-producing", "Licensed ≠ Producing", "tee", "A licence is not a production report."),
]
STICKERS = [("hyperbolic-decline", "Hyperbolic Decline"), ("b-equals-1", "b = 1.0"), ("shut-in-not-shut-down", "Shut-In, Not Shut Down"),
            ("arps-was-right", "Arps Was Right"), ("leading-zeros-matter", "Leading Zeros Matter"), ("check-the-units", "Check the Units")]
NOTEBOOKS = [("decline-log", "Decline Log", "A field notebook for the numbers you keep meaning to track."), ("well-file", "Well File", "Notes, numbers, nonsense.")]
SHEETS = [("units-and-conversions", "Units & Conversions", "Oil, gas, energy and pressure factors, plus the rate-from-volume rule."),
          ("decline-curves-one-page", "Decline Curves, One Page", "Exponential, hyperbolic and harmonic, with the habits that keep a fit honest."),
          ("regulator-data-gotchas", "Regulator Data Gotchas", "Seven ways public well data quietly breaks an analysis.")]
FEATURED = ["hyperbolic-decline", "arps-was-right", "shut-in-not-shut-down", "wells-dont-retire"]



LINKJS = ('<script src="shop.js"></script>')


def esc(s):
    return escape(s, quote=True)


def card_img(src, alt, w, h):
    return f'<img src="{IMG}{src}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy">'


def prod(slug, kind, title, blurb, img, w, h, extra=""):
    return (f'<div class="prod" data-slug="{esc(kind + "-" + slug)}">{img}<div class="pi"><span class="tag">{esc(kind_label(kind))}</span>'
            f'<h3>{esc(title)}</h3><p>{esc(blurb)}</p>{extra}<span class="go soon">Opening soon</span></div></div>')


def kind_label(k):
    return {"poster": "Data-art poster", "hoodie": "Hoodie", "tee": "T-shirt", "sticker": "Sticker", "notebook": "Notebook", "sheet": "Digital download"}[k]


def body():
    o = []
    o.append('<div class="shop-hero"><span class="badge">Launch collection · opening soon</span>'
             '<h1>The Tidywells <span class="grad">shop</span></h1>'
             '<p>Oil and gas, in the places it belongs: on your wall, your chest and your hard hat. Posters drawn from the open dataset, '
             'apparel only people who have fought a regulator file will get, stickers, notebooks and printable reference sheets.</p>'
             '<p class="shop-note">Made on demand, so nothing sits in a warehouse. The store opens soon; join the newsletter at the bottom of the page and we will tell you first. '
             'Prices and checkout links appear here when the store is live.</p></div>')
    # featured hoodies
    feat = [a for a in APPAREL if a[0] in FEATURED]
    o.append('<h2 id="hoodies">Featured hoodies</h2><div class="pgrid four">' + "".join(
        prod(s, k, n, b, card_img(f"mockup-{s}.jpg", f"{n} {k} mockup", 720, 720), 720, 720) for s, n, k, b in feat) + '</div>'
        '<p class="shop-note">Garment images are illustrative mockups of the print placement. Final garment colours and fit follow the store listing.</p>')
    # posters
    ps = []
    for s, t, b in POSTERS:
        sw = ('<div class="sw" role="group" aria-label="Colourway"><button type="button" data-cw="night" aria-pressed="true">Night</button>'
              '<button type="button" data-cw="paper" aria-pressed="false">Paper</button></div>')
        ps.append(prod(s, "poster", t, b, f'<img src="{IMG}poster-{s}-night.jpg" data-base="{IMG}poster-{s}-" alt="{esc(t)} poster, 18 by 24 inch" width="720" height="960" loading="lazy">', 720, 960, sw))
    o.append('<h2 id="posters">Data-art posters</h2><p>Every poster is generated from the open Tidywells dataset: the numbers printed on it match '
             '<a href="data.html">the CSV you can download</a>, and the footer says what they are. 18 × 24 inch, in a dark Night or a cream Paper colourway.</p>'
             '<div class="pgrid">' + "".join(ps) + '</div>')
    # apparel (all)
    rest = [a for a in APPAREL if a[0] not in FEATURED]
    o.append('<h2 id="apparel">Apparel</h2><p>Insider humour, no company logos. Each design is made in a light ink for dark garments and a dark ink for light ones.</p><div class="pgrid">' + "".join(
        prod(s, k, n, b, card_img(f"mockup-{s}.jpg", f"{n} {k} mockup", 720, 720), 720, 720) for s, n, k, b in rest) + '</div>')
    # stickers and notebooks
    o.append('<h2 id="stickers">Hard-hat stickers and field notebooks</h2><div class="pgrid">' + "".join(
        prod(s, "sticker", n, "Die-cut style, 3 inch. Sticks to hard hats, laptops and truck dashboards.", card_img(f"sticker-{s}.png", f"{n} sticker", 600, 600), 600, 600) for s, n in STICKERS) + "".join(
        prod(s, "notebook", n, b, card_img(f"cover-{s}.jpg", f"{n} notebook cover", 600, 928), 600, 928) for s, n, b in NOTEBOOKS) + '</div>')
    # custom
    o.append('<h2 id="your-well">Your Well poster</h2><div class="strip"><p>Bring your own monthly production for a well you own or have the right to use and make a poster of it, right in your browser. '
             'The file is read locally and never uploaded. <a class="btn primary" href="your-well.html">Make a Your Well poster</a></p>'
             '<p class="shop-note">We do not sell prints of other people\'s wells from public files: that needs written confirmation from the regulator, which we do not have yet.</p></div>')
    # digital
    o.append('<h2 id="downloads">Printable reference sheets</h2><p>Three 11 × 17 inch sheets to pin up beside your screen. Digital download, print them as often as you like for your own use.</p><div class="pgrid">' + "".join(
        prod(s, "sheet", t, b, card_img(f"sheet-{s}.jpg", f"{t} reference sheet", 720, 1118), 720, 1118) for s, t, b in SHEETS) + '</div>')
    o.append('<h2>Good to know</h2><div class="faq"><p><b>Is this affiliated with a regulator or an operator?</b><br>No. The art uses public regulator data and original wording. No company names or logos appear on any product.</p>'
             '<p><b>Are the numbers on the posters right?</b><br>They are computed from the open dataset and checked against it in our tests. Oil and gas are the Petrinex conventional volumetrics products, so totals can differ from other published provincial figures. The posters are not investment advice.</p>'
             '<p><b>Who makes and ships the products?</b><br>A print-on-demand partner, confirmed when the store opens. Sizes, delivery times and prices will be on each listing.</p>'
             '<p><b>Where does the money go?</b><br>It helps keep the open data, tools and analysis free. Tidywells is built by one person; see <a href="about.html">About</a>.</p></div>')
    o.append(LINKJS)
    return "\n".join(o)


def home_strip():
    feat = [a for a in APPAREL if a[0] in FEATURED]
    cards = "".join(f'<a class="prod" href="shop.html#hoodies" style="text-decoration:none;color:inherit"><img src="{IMG}mockup-{s}.jpg" alt="{esc(n)} hoodie mockup" width="720" height="720" loading="lazy"><div class="pi"><span class="tag">Hoodie</span><h3>{esc(n)}</h3></div></a>'
                    for s, n, k, b in feat)
    pcards = "".join(f'<a class="prod" href="shop.html#posters" style="text-decoration:none;color:inherit"><img src="{IMG}poster-{s}-night.jpg" alt="{esc(t)} poster" width="720" height="960" loading="lazy"><div class="pi"><span class="tag">Poster</span><h3>{esc(t)}</h3></div></a>'
                     for s, t in (("ab-oil", "Alberta Oil"), ("gas-season", "Gas Has a Season")))
    return ('<!--SHOP--><section class="strip"><span class="badge">Launch collection · opening soon</span>'
            '<h2>The Tidywells shop</h2><p>Hoodies, posters drawn from real data, stickers and notebooks for people who work with Canadian oil and gas.</p>'
            f'<div class="pgrid">{cards}{pcards}</div>'
            '<p><a class="btn primary" href="shop.html">See the collection</a> <a class="btn" href="shop.html#posters">Data-art posters</a></p></section><!--/SHOP-->')


def your_well():
    return """<h1>Your Well poster</h1>
<p><span class="chip">Runs in your browser; nothing is uploaded</span><span class="chip">For wells you own or may use</span></p>
<p>Turn one well's monthly production into a poster: a clean line, the peak, the latest month and the change since the start. Paste two columns (month and volume), load a file, or load the output of the <a href="clean.html">File cleaner</a> and choose a well.</p>
<div class="panel">
<label for="paste">Monthly production</label>
<textarea id="paste" style="min-height:140px;font:13px/1.4 ui-monospace,monospace" placeholder="month,volume&#10;2023-01,310&#10;2023-02,295&#10;..."></textarea>
<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:8px"><input id="file" type="file" accept=".csv,.txt,.tsv" style="width:auto"><button id="ex" type="button">Try an example (synthetic)</button></div>
<div id="msg" class="shop-note" role="status"></div>
<div id="wellrow" hidden><label for="well">Well</label><select id="well" style="width:100%;padding:7px"></select></div>
<div id="prodrow" hidden><label for="prod">Product</label><select id="prod" style="width:100%;padding:7px"></select></div>
<label for="title">Poster title</label><input id="title" placeholder="My Well" maxlength="60">
<label for="unit">Unit label</label><input id="unit" placeholder="bbl per day" maxlength="40">
<label for="kind">The numbers are</label><select id="kind" style="width:100%;padding:7px"><option value="vol">monthly volumes (shown as a daily rate)</option><option value="rate">already a daily rate</option></select>
<label for="theme2">Colourway</label><select id="theme2" style="width:100%;padding:7px"><option value="night">Night</option><option value="paper">Paper</option></select>
</div>
<div id="out" hidden style="margin-top:14px"><div id="prev" style="max-width:520px;margin:0 auto"></div>
<p style="text-align:center"><button id="dl" type="button" class="btn primary">Download PNG (3600 × 4800)</button> <button id="dls" type="button">Download SVG</button></p></div>
<p class="shop-note">Use only data you own or have the right to print. Tidywells does not sell prints of other people's wells made from public files: the regulators' terms need confirming in writing first. The poster uses the fonts on your device, so it can look slightly different from the shop posters.</p>
<script src="wellposter.js"></script><script src="your-well.js"></script>"""


TAGS_BASE = ["oil and gas", "petroleum engineer", "oilfield gift", "data nerd", "geek gift", "engineer gift", "canadian oil", "alberta"]


def listings():
    """Store-ready copy (Etsy limits: title 140 chars, 13 tags of at most 20 chars). Writes shop/listings.csv."""
    import csv
    rows = []
    for s, t, b in POSTERS:
        for cw in ("Night", "Paper"):
            rows.append((f"poster-{s}-{cw.lower()}", "Poster 18x24in", f"{t} Poster, Canadian Oil and Gas Data Art, {cw} Edition, 18x24 Print",
                         f"{b} Generated from the open Tidywells dataset (Petrinex and BC Energy Regulator public data); the figures match the CSV at tidywells.com/data.html. "
                         "Not investment advice. Printed on demand.", TAGS_BASE + ["data art", "wall art", "office decor", "poster", "chart print"]))
    for s, n, k, b in APPAREL:
        rows.append((f"{k}-{s}", "Hoodie" if k == "hoodie" else "T-shirt", f"{n} {'Hoodie' if k == 'hoodie' else 'T-Shirt'}, Oil and Gas Humor, Decline Curve Gift",
                     f"{b} Design by Tidywells. No company logos. Printed on demand.", TAGS_BASE + ["funny shirt", "decline curve", "roughneck", "oilfield humor", "gift for him"]))
    for s, n in STICKERS:
        rows.append((f"sticker-{s}", "Sticker 3in", f"{n} Sticker, Hard Hat Sticker, Oil and Gas Humor, Laptop Decal",
                     "Hard-hat and laptop sticker with an oil-and-gas data joke. Design by Tidywells.", TAGS_BASE + ["hard hat sticker", "laptop sticker", "vinyl sticker", "decal", "oilfield"]))
    for s, n, b in NOTEBOOKS:
        rows.append((f"notebook-{s}", "Notebook", f"{n} Notebook, Oilfield Field Notebook, Gift for Petroleum Engineer",
                     f"{b} Design by Tidywells.", TAGS_BASE + ["field notebook", "journal", "notebook", "log book", "work gift"]))
    for s, t, b in SHEETS:
        rows.append((f"sheet-{s}", "Digital download PDF 11x17", f"{t} Cheat Sheet PDF, Oil and Gas Reference, Printable 11x17",
                     f"{b} Instant PDF download, print for your own use. By Tidywells.", TAGS_BASE + ["cheat sheet", "printable", "pdf download", "reference", "digital download"]))
    with open(ROOT / "shop" / "listings.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "title", "description", "tags"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], "|".join(list(dict.fromkeys(r[4]))[:13])])
    return rows


def main():
    listings()
    html = page("shop.html", "Shop", "Oil and gas posters drawn from real data, hoodies, tees, stickers and notebooks from Tidywells.", body(),
                css="article{max-width:none}")
    (DOCS / "shop.html").write_text(html, encoding="utf-8")
    (DOCS / "your-well.html").write_text(page("your-well.html", "Your Well poster", "Make a poster of your own well's production in your browser. Nothing is uploaded.", your_well(), css="article{max-width:760px}"), encoding="utf-8")
    idx = DOCS / "index.html"
    h = idx.read_text(encoding="utf-8")
    strip = home_strip()
    if "<!--SHOP-->" in h:
        h = re.sub(r"<!--SHOP-->.*?<!--/SHOP-->", lambda m: strip, h, flags=re.S)
    else:
        h = h.replace("<!--/LATEST-->", "<!--/LATEST-->\n" + strip, 1)
    idx.write_text(h, encoding="utf-8")
    print("shop built")


if __name__ == "__main__":
    main()
