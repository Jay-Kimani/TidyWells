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


PRICE = {"hoodie": 69, "tee": 36, "poster": 42, "sticker": 5, "notebook": 19, "sheet": 8}  # CAD launch prices; confirmed in the store
BUNDLES = [  # id, title, blurb, price, would-be separate total, image
    ("sheets-all-three", "Reference sheet set", "All three 11 x 17 reference sheets: units and conversions, decline curves, and regulator data gotchas.", 19, 24, "bundle-sheets.jpg"),
    ("stickers-three-pack", "Sticker 3-pack", "Pick any three hard-hat stickers from the collection.", 12, 15, "bundle-stickers.jpg"),
]
SPECS = {
    "poster": ["18 x 24 inch print, Night (dark) or Paper (cream) colourway", "Drawn from the open Tidywells dataset, data through September 2026", "Source, method and data window printed on the poster", "Produced and shipped by our fulfilment partner; timing shown at checkout"],
    "hoodie": ["Light-ink design for dark garments", "No company names or logos", "Garment colours, sizes and fabric are set in the store listing", "The image above is an illustrative mockup of the print placement"],
    "tee": ["Light-ink design for dark garments", "No company names or logos", "Garment colours, sizes and fabric are set in the store listing", "The image above is an illustrative mockup of the print placement"],
    "sticker": ["3 inch, die-cut style vinyl sticker", "Made for hard hats, laptops and truck dashboards", "Final material and finish are set in the store listing"],
    "notebook": ["Printed cover design; paper type and page count are set in the store listing", "Made for field notes and well logs"],
    "sheet": ["11 x 17 inch PDF, instant digital download", "For your own use: print as often as you like", "Standard published conversion factors and public regulator file layouts"],
}

POSTER_TAIL = " Four headline figures sit under the chart, and the source, method and data window are printed at the foot, so it reads like a figure from a report rather than decoration. Choose the dark Night edition or the cream Paper edition."
DESC = {
    "poster-ab-oil": "Alberta's monthly oil production from January 2022 to September 2026 as one clean line, with the peak month and the latest month marked." + POSTER_TAIL,
    "poster-ab-gas": "Alberta gas production over the same window, showing the winter peaks that come back every year and where the latest month sits against them." + POSTER_TAIL,
    "poster-sk-oil": "Five years of Saskatchewan oil production, with the peak and the latest month labelled so the shape of the recovery is easy to read from across a room." + POSTER_TAIL,
    "poster-sk-gas": "Saskatchewan gas production on a daily-rate basis, drawn from public regulator files and labelled with its peak and latest month." + POSTER_TAIL,
    "poster-bc-oil": "British Columbia oil production from the BC Energy Regulator files, including the dip and the recovery that follows." + POSTER_TAIL,
    "poster-bc-gas": "British Columbia gas production over five years, with the peak month and the latest month marked on the line." + POSTER_TAIL,
    "poster-five-years": "Oil and gas in Alberta, Saskatchewan and British Columbia as six small charts on one sheet, so the three provinces can be compared at a glance. Source, method and data window are printed at the foot. Choose the dark Night edition or the cream Paper edition.",
    "poster-gas-season": "A radar chart of the calendar-month pattern in Alberta and British Columbia gas: the seasonal wave that every analyst learns to expect. Source, method and data window are printed at the foot. Choose the dark Night edition or the cream Paper edition.",
    "poster-decline-shape": "The Arps family of decline curves from b = 0 to b = 1.5 on one sheet: exponential, hyperbolic and harmonic, the shapes every well-file reader should be able to recognise. Equations and a short reading guide are printed on the poster. Choose the dark Night edition or the cream Paper edition.",
    "hoodie-hyperbolic-decline": "A hoodie for anyone whose enthusiasm follows an Arps curve: a steep start, a long flattening tail, and a small curve drawn under the headline. Printed in light ink for dark garments. Original design, no company names or logos.",
    "hoodie-arps-was-right": "The 1945 decline equation, set large and left to speak for itself. For engineers, analysts and anyone who has fit a curve to a well and been quietly proven right. Printed in light ink for dark garments. Original design, no company names or logos.",
    "hoodie-shut-in-not-shut-down": "A valve wheel and a distinction that matters: a shut-in well is paused, not finished. A hoodie for people who know the difference. Printed in light ink for dark garments. Original design, no company names or logos.",
    "hoodie-wells-dont-retire": "Wells do not retire, they decline, and this hoodie says so with a small decline curve under the line. Respect the curve. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-b-equals-1": "Harmonic decline, in monospace: b = 1.0, nothing more. A quiet t-shirt for people who will get the joke and people who will ask. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-arps-equation": "The Arps equation, q(t) = qi / (1 + b·Di·t)^(1/b), set in type like a line from a textbook. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-leading-zeros-matter": "For everyone who has watched a spreadsheet quietly eat the leading zeros off a well ID and then spent an afternoon finding out why. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-check-the-units": "m³, Mcf, MMcf, boe: always check the units. A t-shirt for the person in the meeting who asks the question that saves the slide. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-gas-has-a-season": "Winter demand, drawn as a wave across the chest. Gas has a season and so does this shirt. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-bounded-optimism": "A decline fit with the exponent held between 0 and 2, because a fit should be bounded and so should optimism. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-p50-energy": "Not optimistic, not pessimistic, just the median. A t-shirt for people who report the P50 and mean it. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-licensed-not-producing": "A licence is not a production report. A t-shirt for anyone who has had to explain that a well on the list is not a well on the pad. Printed in light ink for dark garments. Original design, no company names or logos.",
    "sticker-hyperbolic-decline": "A 3 inch die-cut-style sticker with the steep start and long tail of a hyperbolic decline. Made for hard hats, laptop lids and truck dashboards.",
    "sticker-b-equals-1": "A 3 inch die-cut-style sticker that says b = 1.0, the harmonic decline, in monospace. Made for hard hats, laptops and truck dashboards.",
    "sticker-shut-in-not-shut-down": "A 3 inch die-cut-style sticker of a valve wheel with the line shut-in, not shut down. Made for hard hats, laptops and truck dashboards.",
    "sticker-arps-was-right": "A 3 inch die-cut-style sticker with the Arps equation and the verdict. Made for hard hats, laptops and truck dashboards.",
    "sticker-leading-zeros-matter": "A 3 inch die-cut-style sticker for anyone who has lost a well ID's leading zeros to a spreadsheet. Made for hard hats, laptops and truck dashboards.",
    "sticker-check-the-units": "A 3 inch die-cut-style sticker with the one habit that prevents most reporting errors: check the units. Made for hard hats, laptops and truck dashboards.",
    "notebook-decline-log": "A field notebook with a decline-curve cover, for the numbers you keep meaning to track: rates, pressures, dates and the odd well-site thought. Original cover design, no company names or logos.",
    "notebook-well-file": "A notebook with a well-file cover: notes, numbers and nonsense, all in one place. Original cover design, no company names or logos.",
    "sheet-units-and-conversions": "A one-page, 11 x 17 inch PDF of oil, gas, energy and pressure conversion factors, plus the rule for turning a volume into a daily rate. Print it for your desk or your truck; for your own use. Instant download.",
    "sheet-decline-curves-one-page": "Exponential, hyperbolic and harmonic decline on one 11 x 17 inch PDF page, with the habits that keep a fit honest: what b means, where the fit breaks and what to check first. Print it for your own use. Instant download.",
    "sheet-regulator-data-gotchas": "Seven ways public well data quietly breaks an analysis, on one 11 x 17 inch PDF page: units, identifiers, reporting lags, and the other traps that catch careful people. Print it for your own use. Instant download.",
}
SIZES = {
    "tee": ("Unisex t-shirt", ["S", "M", "L", "XL", "2XL", "3XL"], [(18, 28), (20, 29), (22, 30), (24, 31), (26, 32), (28, 33)]),
    "hoodie": ("Unisex hoodie", ["S", "M", "L", "XL", "2XL", "3XL"], [(20, 27), (22, 28), (24, 29), (26, 30), (28, 31), (30, 32)]),
}


def size_chart(kind):
    """Generic unisex size table (flat garment measurements). The final chart comes from the supplier listing."""
    name, labels, dims = SIZES[kind]
    rows = "".join(f"<tr><th scope='row'>{l}</th><td>{w}</td><td>{round(w * 2.54)}</td><td>{h}</td><td>{round(h * 2.54)}</td></tr>" for l, (w, h) in zip(labels, dims))
    return (f'<h2>Size guide</h2><div class="sizes"><table><caption>{name}, flat garment measurements</caption>'
            '<thead><tr><th scope="col">Size</th><th scope="col">Chest width (in)</th><th scope="col">Chest width (cm)</th><th scope="col">Length (in)</th><th scope="col">Length (cm)</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            '<p class="shop-note">Typical unisex fit. Measurements are approximate and vary slightly by garment maker; the final size guide appears in the store listing. Between sizes, size up for a relaxed fit.</p>')



def price_html(kind=None, amount=None):
    a = PRICE[kind] if amount is None else amount
    return f'<span class="price">CAD ${a} <small>launch price</small></span>'


def pid(kind, slug):
    return f"{kind}-{slug}"


def page_name(kind, slug):
    return f"product-{pid(kind, slug)}.html"


def catalogue():
    """Every product as a dict: id, kind, slug, title, blurb, images [(file, alt, w, h)], page."""
    out = []
    for s, t, b in POSTERS:
        out.append(dict(kind="poster", slug=s, title=t + " poster", short=t, blurb=b, images=[(f"poster-{s}-night.jpg", f"{t} poster, Night colourway", 720, 960), (f"poster-{s}-paper.jpg", f"{t} poster, Paper colourway", 720, 960)]))
    for s, n, k, b in APPAREL:
        out.append(dict(kind=k, slug=s, title=f"{n} {'hoodie' if k == 'hoodie' else 't-shirt'}", short=n, blurb=b, images=[(f"mockup-{s}.jpg", f"{n} {k} mockup", 720, 720)]))
    for s, n in STICKERS:
        out.append(dict(kind="sticker", slug=s, title=f"{n} sticker", short=n, blurb="A hard-hat sticker for people who work with oil and gas data.", images=[(f"sticker-{s}.png", f"{n} sticker", 600, 600)]))
    for s, n, b in NOTEBOOKS:
        out.append(dict(kind="notebook", slug=s, title=f"{n} notebook", short=n, blurb=b, images=[(f"cover-{s}.jpg", f"{n} notebook cover", 600, 928)]))
    for s, t, b in SHEETS:
        out.append(dict(kind="sheet", slug=s, title=f"{t} reference sheet", short=t, blurb=b, images=[(f"sheet-{s}.jpg", f"{t} reference sheet", 720, 1118)]))
    for it in out:
        it["id"] = pid(it["kind"], it["slug"])
        it["page"] = page_name(it["kind"], it["slug"])
    return out


def esc(s):
    return escape(s, quote=True)


def card_img(src, alt, w, h):
    return f'<img src="{IMG}{src}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy">'


def prod(slug, kind, title, blurb, img, w, h, extra=""):
    href = page_name(kind, slug)
    return (f'<div class="prod" data-slug="{esc(pid(kind, slug))}"><a class="pimg" href="{href}">{img}</a><div class="pi"><span class="tag">{esc(kind_label(kind))}</span>'
            f'<h3><a href="{href}">{esc(title)}</a></h3><p>{esc(blurb)}</p>{extra}{price_html(kind)}<span class="go soon">Opening soon</span></div></div>')


def kind_label(k):
    return {"poster": "Data-art poster", "hoodie": "Hoodie", "tee": "T-shirt", "sticker": "Sticker", "notebook": "Notebook", "sheet": "Digital download"}[k]


def body():
    o = []
    o.append('<div class="shop-hero"><span class="badge">Launch collection · opening soon</span>'
             '<h1>The Tidywells <span class="grad">shop</span></h1>'
             '<p>Oil and gas, in the places it belongs: on your wall, your chest and your hard hat. Posters drawn from the open dataset, '
             'apparel only people who have fought a regulator file will get, stickers, notebooks and printable reference sheets.</p>'
             '<p class="shop-note">Prices are launch prices in Canadian dollars; shipping and tax are added at checkout, and the store confirms the final price.</p>'
             '<div id="waitlist" class="waitlist"></div></div>')
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
    o.append('<div class="well-card" id="your-well"><div class="wc-text"><span class="tag">Make your own</span><h2>Your Well poster</h2>'
             '<p>Turn one well\'s monthly production into a poster, for a well you own or may use. It runs in your browser and the file never leaves your device.</p>'
             '<p><a class="btn primary" href="your-well.html">Make a poster</a></p>'
             '<p class="shop-note">We do not sell prints of other people\'s wells from public files; that needs the regulator\'s written confirmation.</p></div>'
             f'<figure><img src="{IMG}your-well-example.jpg" alt="Example Your Well poster built from synthetic data" width="720" height="960" loading="lazy"><figcaption>Example, made from synthetic data</figcaption></figure></div>')
    o.append('<h2 id="bundles">Bundles</h2><div class="pgrid">' + "".join(
        f'<div class="prod" data-slug="bundle-{i}"><div class="pimg">{card_img(img, t, 720, 720)}</div><div class="pi"><span class="tag">Bundle</span><h3>{esc(t)}</h3><p>{esc(b)}</p>'
        f'{price_html(amount=p)}<span class="shop-note">Separately CAD ${full}: you save ${full - p}.</span><span class="go soon">Opening soon</span></div></div>'
        for i, t, b, p, full, img in BUNDLES) + '</div>')
    # digital
    o.append('<h2 id="downloads">Printable reference sheets</h2><p>Three 11 × 17 inch sheets to pin up beside your screen. Digital download, print them as often as you like for your own use.</p><div class="pgrid">' + "".join(
        prod(s, "sheet", t, b, card_img(f"sheet-{s}.jpg", f"{t} reference sheet", 720, 1118), 720, 1118) for s, t, b in SHEETS) + '</div>')
    o.append('<h2>Good to know</h2><div class="faq"><p><b>Is this affiliated with a regulator or an operator?</b><br>No. The art uses public regulator data and original wording. No company names or logos appear on any product.</p>'
             '<p><b>Are the numbers on the posters right?</b><br>They are computed from the open dataset and checked against it in our tests. Oil and gas are the Petrinex conventional volumetrics products, so totals can differ from other published provincial figures. The posters are not investment advice.</p>'
             '<p><b>Who makes and ships the products?</b><br>Products are produced and shipped by our fulfilment partner. Production and delivery times follow the partner schedule and are shown at checkout.</p>'
             '<p><b>Where does the money go?</b><br>It helps keep the open data, tools and analysis free. Tidywells is built by one person; see <a href="about.html">About</a>.</p></div>')
    o.append(LINKJS)
    return "\n".join(o)


def home_strip():
    feat = [a for a in APPAREL if a[0] in FEATURED]
    cards = "".join(f'<a class="prod" href="{page_name("hoodie", s)}" style="text-decoration:none;color:inherit"><img src="{IMG}mockup-{s}.jpg" alt="{esc(n)} hoodie mockup" width="720" height="720" loading="lazy"><div class="pi"><span class="tag">Hoodie</span><h3>{esc(n)}</h3></div></a>'
                    for s, n, k, b in feat)
    pcards = "".join(f'<a class="prod" href="{page_name("poster", s)}" style="text-decoration:none;color:inherit"><img src="{IMG}poster-{s}-night.jpg" alt="{esc(t)} poster" width="720" height="960" loading="lazy"><div class="pi"><span class="tag">Poster</span><h3>{esc(t)}</h3></div></a>'
                     for s, t in (("ab-oil", "Alberta Oil"), ("gas-season", "Gas Has a Season")))
    return ('<!--SHOP--><section class="strip"><span class="badge">Launch collection · opening soon</span>'
            '<h2>The Tidywells shop</h2><p>Hoodies, posters drawn from real data, stickers and notebooks for people who work with Canadian oil and gas.</p>'
            f'<div class="pgrid">{cards}{pcards}</div>'
            f'<p class="shop-note">Hoodies from CAD ${PRICE["hoodie"]} · posters from CAD ${PRICE["poster"]} · stickers from CAD ${PRICE["sticker"]} (launch prices)</p>'
            '<p><a class="btn primary" href="shop.html">See the collection</a> <a class="btn" href="shop.html#posters">Data-art posters</a></p></section><!--/SHOP-->')


def product_page(it, items):
    """One search-landing page per product, with structured data (no offer data until a store URL exists)."""
    import json
    t, kind = it["title"], it["kind"]
    imgs = it["images"]
    pics = "".join(f'<img src="{IMG}{f}" alt="{esc(a)}" width="{w}" height="{h}" data-pi="{i}"{"" if i == 0 else " hidden"}>' for i, (f, a, w, h) in enumerate(imgs))
    sw = ""
    if len(imgs) > 1:
        sw = '<div class="sw" role="group" aria-label="Colourway"><button type="button" data-pi="0" aria-pressed="true">Night</button><button type="button" data-pi="1" aria-pressed="false">Paper</button></div>'
    specs = "".join(f"<li>{esc(x)}</li>" for x in SPECS[kind])
    related = [x for x in items if x["kind"] == kind and x["id"] != it["id"]][:4]
    rel = "".join(f'<a class="prod" href="{r["page"]}" style="text-decoration:none;color:inherit"><img src="{IMG}{r["images"][0][0]}" alt="{esc(r["images"][0][1])}" width="{r["images"][0][2]}" height="{r["images"][0][3]}" loading="lazy"><div class="pi"><h3>{esc(r["short"])}</h3>{price_html(kind)}</div></a>' for r in related)
    ld = {"@context": "https://schema.org", "@type": "Product", "name": t, "description": DESC[it["id"]], "sku": it["id"], "brand": {"@type": "Brand", "name": "Tidywells"},
          "image": [f"https://tidywells.com/{IMG}{f}" for f, *_ in imgs], "url": f"https://tidywells.com/{it['page']}"}
    body_ = (f'<p class="crumb"><a href="shop.html">Shop</a> &rsaquo; {esc(kind_label(kind))}</p>'
             f'<div class="ppage"><div class="pview">{pics}{sw}</div><div class="pdet" data-slug="{esc(it["id"])}"><span class="tag">{esc(kind_label(kind))}</span><h1>{esc(t)}</h1>'
             f'<p class="plead">{esc(it["blurb"])}</p><p>{price_html(kind)}</p><p class="go soon">Opening soon. <a href="shop.html#waitlist">Get an email when the shop opens</a>.</p>'
             f'<h2>About this design</h2><p>{esc(DESC[it["id"]])}</p>'
             f'<h2>Details</h2><ul class="specs">{specs}</ul>{size_chart(kind) if kind in SIZES else ""}'
             '<p class="shop-note">Launch price in Canadian dollars; shipping and tax are added at checkout and the store confirms the final price. Tidywells is not affiliated with any regulator or operator.</p></div></div>'
             f'<h2>More from this range</h2><div class="pgrid">{rel}</div>')
    body_ += f'<script type="application/ld+json">{json.dumps(ld)}</script><script src="shop.js"></script>'
    return page(it["page"], t, f"{t} from the Tidywells shop. {it['blurb']}", body_, css="article{max-width:none}")


def posterbox(prefix, topic):
    """'Hang this chart' strip for articles: three matched posters with prices, linking to their product pages."""
    sets = {"snapshot": ["ab-oil", "ab-gas", "bc-gas"], "gas": ["gas-season", "ab-gas", "sk-gas"], "decline": ["decline-shape", "ab-oil", "five-years"], "default": ["five-years", "ab-oil", "decline-shape"]}
    names = {s: t for s, t, _ in POSTERS}
    cards = "".join(f'<a class="prod" href="{prefix}{page_name("poster", s)}" style="text-decoration:none;color:inherit"><img src="{prefix}{IMG}poster-{s}-night.jpg" alt="{esc(names[s])} poster" width="720" height="960" loading="lazy"><div class="pi"><h3>{esc(names[s])}</h3>{price_html("poster")}</div></a>' for s in sets.get(topic, sets["default"]))
    return ('<!--POSTERBOX--><section class="posterbox"><div class="pb-t"><span class="tag">From the Tidywells shop</span><h2>Hang the data on your wall</h2>'
            f'<p>Every poster is drawn from the same open dataset as these articles, 18 x 24 inch, opening soon. <a href="{prefix}shop.html#posters">See all posters</a>.</p></div>'
            f'<div class="pgrid">{cards}</div></section><!--/POSTERBOX-->')


def your_well():
    return """<h1>Your Well poster</h1>
<p class="yw-lead">Turn one well's monthly production into a clean poster. Your data is read in your browser and never uploaded. Use it for wells you own or have the right to use.</p>
<div class="yw">
<div class="panel yw-in">
<h2>1. Add your data</h2>
<label for="paste">Paste two columns, month and volume, or load a file</label>
<textarea id="paste" placeholder="month,volume&#10;2023-01,310&#10;2023-02,295"></textarea>
<div class="yw-row"><input id="file" type="file" accept=".csv,.txt,.tsv"><button id="ex" type="button">Use example data</button></div>
<p class="shop-note">Also accepts the output of the <a href="clean.html">File cleaner</a>; then pick the well below.</p>
<div id="msg" class="shop-note" role="status"></div>
<h2>2. Make it yours</h2>
<div class="fgrid">
<div id="wellrow" hidden><label for="well">Well</label><select id="well"></select></div>
<div id="prodrow" hidden><label for="prod">Product</label><select id="prod"></select></div>
<div class="wide"><label for="title">Title</label><input id="title" placeholder="My Well" maxlength="60"></div>
<div><label for="unit">Unit label</label><input id="unit" placeholder="bbl per day" maxlength="40"></div>
<div><label for="theme2">Colourway</label><select id="theme2"><option value="night">Night</option><option value="paper">Paper</option></select></div>
<div class="wide"><label for="kind">The numbers are</label><select id="kind"><option value="vol">monthly volumes (shown as a daily rate)</option><option value="rate">already a daily rate</option></select></div>
</div>
</div>
<div class="yw-out"><div id="ph" class="yw-ph">Your poster appears here</div>
<div id="out" hidden><div id="prev"></div>
<p class="yw-btns"><button id="dl" type="button" class="btn primary">Download PNG</button><button id="dls" type="button" class="btn">Download SVG</button></p></div></div>
</div>
<p class="shop-note">Tidywells does not sell prints of other people's wells made from public files; the regulators' terms need confirming in writing first. The PNG is 3600 x 4800 pixels. It uses fonts on your device, so it can look slightly different from the shop posters.</p>
<script src="wellposter.js"></script><script src="your-well.js"></script>"""


TAGS_BASE = ["oil and gas", "petroleum engineer", "oilfield gift", "data nerd", "geek gift", "engineer gift", "canadian oil", "alberta"]


def listings():
    """Store-ready copy (Etsy limits: title 140 chars, 13 tags of at most 20 chars). Writes shop/listings.csv."""
    import csv
    rows = []
    for s, t, b in POSTERS:
        for cw in ("Night", "Paper"):
            rows.append((f"poster-{s}-{cw.lower()}", "Poster 18x24in", f"{t} Poster, Canadian Oil and Gas Data Art, {cw} Edition, 18x24 Print",
                         f"{DESC[pid('poster', s)]} Generated from the open Tidywells dataset (Petrinex and BC Energy Regulator public data); the figures match the CSV at tidywells.com/data.html. "
                         "Not investment advice.", TAGS_BASE + ["data art", "wall art", "office decor", "poster", "chart print"]))
    for s, n, k, b in APPAREL:
        rows.append((f"{k}-{s}", "Hoodie" if k == "hoodie" else "T-shirt", f"{n} {'Hoodie' if k == 'hoodie' else 'T-Shirt'}, Oil and Gas Humor, Decline Curve Gift",
                     f"{DESC[pid(k, s)]}", TAGS_BASE + ["funny shirt", "decline curve", "roughneck", "oilfield humor", "gift for him"]))
    for s, n in STICKERS:
        rows.append((f"sticker-{s}", "Sticker 3in", f"{n} Sticker, Hard Hat Sticker, Oil and Gas Humor, Laptop Decal",
                     DESC[pid("sticker", s)], TAGS_BASE + ["hard hat sticker", "laptop sticker", "vinyl sticker", "decal", "oilfield"]))
    for s, n, b in NOTEBOOKS:
        rows.append((f"notebook-{s}", "Notebook", f"{n} Notebook, Oilfield Field Notebook, Gift for Petroleum Engineer",
                     DESC[pid("notebook", s)], TAGS_BASE + ["field notebook", "journal", "notebook", "log book", "work gift"]))
    for s, t, b in SHEETS:
        rows.append((f"sheet-{s}", "Digital download PDF 11x17", f"{t} Cheat Sheet PDF, Oil and Gas Reference, Printable 11x17",
                     DESC[pid("sheet", s)], TAGS_BASE + ["cheat sheet", "printable", "pdf download", "reference", "digital download"]))
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
    (DOCS / "your-well.html").write_text(page("your-well.html", "Your Well poster", "Make a poster of your own well's production in your browser. Nothing is uploaded.", your_well(), css="article{max-width:none}"), encoding="utf-8")
    items = catalogue()
    for it in items:
        (DOCS / it["page"]).write_text(product_page(it, items), encoding="utf-8")
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
