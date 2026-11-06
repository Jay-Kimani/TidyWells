"""Writes docs/shop.html, docs/shop.css block in style.css and the home-page shop strip, and docs/img/shop previews.
Idempotent. Run after shop/art.py, art_goods.py, cheats.py + render.js have produced web previews in OUT/web
(only when previews change); CI just re-runs this script against the committed images.
Honesty rules: no prices, no 'on sale', no Buy buttons until window.TIDYWELLS_SHOP_URL / LINKS are set in config.js."""
import json, re
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
    ("record-barrels", "Record Barrels", "Alberta, Saskatchewan and BC oil stacked on one chart, with the highest month since January 2022 marked."),
    ("peak-vs-now", "Peak vs Now", "Six oil and gas streams ranked by how close they are to their own best month."),
    ("86-of-100", "86 of Every 100", "A hundred dots, one for every 100 barrels: who produces what in the three provinces."),
    ("decline-shape", "Shape of a Decline", "The Arps family b = 0 to 1.5, the curve every well-file reader should know."),
]
APPAREL = [  # slug, name, garment, blurb
    ("build-the-pipeline", "Build the Pipeline", "hoodie", "Three words and a request."),
    ("ottawa-doesnt-pump-oil", "Ottawa Doesn't Pump Oil", "hoodie", "A reminder of who does."),
    ("shut-in-not-shut-down", "Shut-In, Not Shut Down", "hoodie", "A valve wheel and a distinction that matters."),
    ("oil-and-gas", "Oil & Gas", "hoodie", "The industry's name, big and plain."),
    ("hyperbolic-decline", "Hyperbolic Decline: My Motivation", "hoodie", "For anyone whose enthusiasm follows an Arps curve."),
    ("arps-was-right", "Arps Was Right", "hoodie", "The 1945 equation, still undefeated."),
    ("powered-by-oil", "Powered by Oil", "tee", "Short, clean, and true."),
    ("scrap-the-tanker-ban", "Scrap the Tanker Ban", "tee", "For the west coast export argument."),
    ("camp-life", "Camp Life", "tee", "Two words for the rotation."),
    ("oil-and-gas-crew", "Oil & Gas Crew", "tee", "Plain type, plain pride."),
    ("darcys-law", "Darcy's Law", "tee", "How fluid moves through rock."),
    ("pv-znrt", "pV = znRT", "tee", "The real gas law, with the z-factor."),
]
STICKERS = [("build-the-pipeline", "Build the Pipeline"), ("scrap-the-tanker-ban", "Scrap the Tanker Ban"), ("ottawa-doesnt-pump-oil", "Ottawa Doesn't Pump Oil"),
            ("powered-by-oil", "Powered by Oil"), ("shut-in-not-shut-down", "Shut-In, Not Shut Down"),
            ("camp-life", "Camp Life"), ("darcys-law", "Darcy's Law"), ("pv-znrt", "pV = znRT"), ("hyperbolic-decline", "Hyperbolic Decline")]
MUGS = [("build-the-pipeline", "Build the Pipeline", "Three words and a request, for the first coffee of the shift."),
        ("ottawa-doesnt-pump-oil", "Ottawa Doesn't Pump Oil", "A reminder of who does."),
        ("powered-by-oil", "Powered by Oil", "Short, clean, and true."),
        ("hyperbolic-decline", "Hyperbolic Decline: My Motivation", "For anyone whose enthusiasm follows an Arps curve."),
        ("check-the-units", "Check the Units", "m³, Mcf, MMcf, boe. Always.")]
HATS = [("build-the-pipeline", "Build the Pipeline", "Embroidered text, three words and a request."),
        ("powered-by-oil", "Powered by Oil", "Embroidered text, three words and a fact.")]
TOQUES = [("camp-life", "Camp Life", "For the winter rotation: a toque that says it for you."),
          ("powered-by-oil", "Powered by Oil", "Embroidered on the cuff, for the long walk to the truck."),
          ("build-the-pipeline", "Build the Pipeline", "Embroidered on the cuff, for the walk to the truck.")]
SHEETS = [("units-and-conversions", "Units & Conversions", "Oil, gas, energy and pressure factors, plus the rate-from-volume rule.")]
FEATURED = ["build-the-pipeline", "ottawa-doesnt-pump-oil", "shut-in-not-shut-down", "hyperbolic-decline"]
BEST = ["hoodie-build-the-pipeline", "hoodie-ottawa-doesnt-pump-oil", "toque-camp-life", "mug-build-the-pipeline"]



LINKJS = ('<script src="shop-links.js"></script><script src="shop-links.js"></script><script src="shop.js"></script>')


PRICE = {"hoodie": 74.99, "tee": 36.99, "mug": 24.99, "hat": 49.99, "toque": 39.99, "poster": 44.99, "sheet": 8.99}  # CAD launch prices; confirmed in the store
BUNDLES = [  # id, title, blurb, price, stickers in pack, image. Stickers are sold only in packs: one sticker alone costs about as much to ship as it earns.
    ("stickers-3-pack", "Sticker sheet of 3", "A5 kiss-cut sheet: Build the Pipeline, Scrap the Tanker Ban and Powered by Oil. About 2.5 inch each.", 12.99, 3, "sp-sticker-sheet-3-1.jpg"),
    ("stickers-6-pack", "Sticker sheet of 6", "A5 kiss-cut sheet of six: the three above plus Camp Life, Ottawa Doesn't Pump Oil and Darcy's Law. About 2.3 inch each.", 14.99, 6, "sp-sticker-sheet-6-1.jpg"),
    ("stickers-complete-set", "Complete sheet of 9", "A5 kiss-cut sheet with every design in the collection, one of each. About 1.7 inch each.", 16.99, 9, "sp-sticker-sheet-9-1.jpg"),
]
SPECS = {
    "poster": ["18 x 24 inch print, Dark Night or cream Paper edition (separate listings)", "Drawn from the open Tidywells dataset, data through September 2026", "Source, method and data window printed on the poster", "Produced and shipped by our fulfilment partner; timing shown at checkout"],
    "hoodie": ["Large design printed on the back, small Tidywells mark on the left chest", "Light-ink design for dark garments", "No oil company names or logos", "Garment colours, sizes and fabric are set in the store listing", "The images above are illustrative mockups of the print placement"],
    "tee": ["Large design printed on the back, small Tidywells mark on the left chest", "Light-ink design for dark garments", "No oil company names or logos", "Garment colours, sizes and fabric are set in the store listing", "The images above are illustrative mockups of the print placement"],
    "sticker": ["3 inch, die-cut style vinyl sticker", "Made for hard hats, laptops and truck dashboards", "Final material and finish are set in the store listing"],
    "mug": ["11 oz ceramic mug, design wraps around", "Dishwasher and microwave safe (confirm in the store listing)", "No oil company names or logos"],
    "hat": ["Embroidered text on the front panel", "Adjustable fit; colour set in the store listing", "No oil company names or logos"],
    "toque": ["Cuffed knit toque (beanie) with embroidered cuff", "One size; fabric and lining are set in the store listing", "No oil company names or logos"],
    "sheet": ["11 x 17 inch PDF, instant digital download", "For your own use: print as often as you like", "Standard published conversion factors and public regulator file layouts"],
}

POSTER_TAIL = " Four headline figures sit under the chart, and the source, method and data window are printed at the foot, so it reads like a figure from a report rather than decoration. Available as a dark Night edition and a cream Paper edition."
DESC = {
    "poster-ab-oil": "Alberta's monthly oil production from January 2022 to September 2026 as one clean line, with the peak month and the latest month marked." + POSTER_TAIL,
    "hoodie-build-the-pipeline": "Three words and a request, set large on the back. For everyone who has been waiting on a pipeline long enough to have an opinion about it. Printed in light ink for dark garments. Original design, no company names or logos.",
    "hoodie-ottawa-doesnt-pump-oil": "A short reminder of who actually pumps it. Bold type on the back for the crew, the office and the family barbecue. Printed in light ink for dark garments. Original design, no company names or logos.",
    "hoodie-shut-in-not-shut-down": "A valve wheel and a distinction that matters: a shut-in well is paused, not finished. A hoodie for people who know the difference. Printed in light ink for dark garments. Original design, no company names or logos.",
    "hoodie-hyperbolic-decline": "A hoodie for anyone whose enthusiasm follows an Arps curve: a steep start, a long flattening tail, and a small curve drawn under the headline. Printed in light ink for dark garments. Original design, no company names or logos.",
    "hoodie-arps-was-right": "The 1945 decline equation, set large and left to speak for itself. For engineers and analysts who have fit a curve to a well and been quietly proven right. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-scrap-the-tanker-ban": "A blunt opinion on the west coast export argument, in heavy type. Wear it where the conversation is happening. Printed in light ink for dark garments. Original design, no company names or logos.",
    "sticker-build-the-pipeline": "A 3 inch die-cut-style sticker with a three-word request. Made for hard hats, lunch kits, tool boxes and truck dashboards.",
    "sticker-scrap-the-tanker-ban": "A 3 inch die-cut-style sticker with a blunt opinion in heavy type. Made for hard hats, toolboxes and truck dashboards.",
    "sticker-ottawa-doesnt-pump-oil": "A 3 inch die-cut-style sticker that says who actually pumps it. Made for hard hats, lunch kits and truck dashboards.",
    "sticker-shut-in-not-shut-down": "A 3 inch die-cut-style sticker of a valve wheel with the line shut-in, not shut down. Made for hard hats, laptops and truck dashboards.",
    "sticker-hyperbolic-decline": "A 3 inch die-cut-style sticker with the steep start and long tail of a hyperbolic decline. For the engineers' laptop lid.",
    "sticker-check-the-units": "A 3 inch die-cut-style sticker with the one habit that prevents most reporting errors: check the units. For the engineers' laptop lid.",
    "mug-build-the-pipeline": "Three words and a request, wrapped around an 11 oz mug. For the first coffee of the shift and the desk it ends up on. Original design, no company names or logos.",
    "mug-ottawa-doesnt-pump-oil": "A short reminder of who actually pumps it, in heavy type on an 11 oz mug. Good for the crew room and the office kitchen. Original design, no company names or logos.",
    "mug-hyperbolic-decline": "A small decline curve under the line, on an 11 oz mug: for anyone whose enthusiasm follows an Arps curve. Original design, no company names or logos.",
    "mug-check-the-units": "m³, Mcf, MMcf, boe: always check the units. An 11 oz mug for the engineer who asks the question that saves the slide. Original design, no company names or logos.",
    "hat-build-the-pipeline": "Embroidered text on the front of an adjustable hat: three words and a request. Plain, clean, easy to wear to the site, the rink or the pub. Original design, no company names or logos.",
    "hat-powered-by-oil": "Embroidered text on the front of an adjustable hat: powered by oil, three words and a fact. Original design, no company names or logos.",
    "toque-build-the-pipeline": "A cuffed toque with Build the Pipeline embroidered on the cuff. Keeps the cold off and the opinion on. Original design, no company names or logos.",
    "tee-powered-by-oil": "Three words and a fact, in heavy type on the back. For the lunchroom, the truck and everyone who has noticed what the lights run on. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-camp-life": "Two words for anyone who has done the rotation: the bunkhouse, the cafeteria, the long drive in and the longer one home. Heavy type on the back. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-darcys-law": "Darcy's law, set large on the back: flow rate equals permeability times area times pressure difference, over viscosity times length. How fluid moves through rock, first written down in 1856. For engineers, geologists and anyone who has argued about permeability. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-pv-znrt": "The real gas law on the back: pV = znRT. The z-factor is the part the textbook ideal gas law leaves out, and the reason gas is never quite as simple as it looks. For engineers who have fought a compressibility chart. Printed in light ink for dark garments. Original design, no company names or logos.",
    "sticker-powered-by-oil": "A 3 inch die-cut-style sticker in heavy type. Made for hard hats, lunch kits and truck dashboards.",
    "sticker-camp-life": "A 3 inch die-cut-style sticker for the rotation: camp life. Made for hard hats, lunch kits and truck dashboards.",
    "sticker-darcys-law": "A 3 inch die-cut-style sticker with Darcy's law. For the engineers' laptop lid.",
    "sticker-pv-znrt": "A 3 inch die-cut-style sticker with the real gas law, pV = znRT. For the engineers' laptop lid.",
    "mug-powered-by-oil": "Three words in heavy type on an 11 oz mug. A coffee cup with a point of view. Original design, no company names or logos.",
    "toque-camp-life": "A cuffed toque with Camp Life embroidered on the cuff. For the winter rotation and the long walk to the truck. Original design, no company names or logos.",
    "toque-powered-by-oil": "A cuffed toque with Powered by Oil embroidered on the cuff. Keeps the cold off and the point made. Original design, no company names or logos.",
    "hoodie-oil-and-gas": "Just the industry's name, big and plain on the back: Oil & Gas. A heavyweight hoodie for the crew, the office and the drive home. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-oil-and-gas-crew": "Oil & Gas Crew in heavy type on the back. Simple, clean and easy to wear to the site, the shop or the pub. Printed in light ink for dark garments. Original design, no company names or logos.",
    "poster-record-barrels": "Western Canada's oil, stacked on a zero baseline: Alberta, Saskatchewan and BC from January 2022 to September 2026, with the record month marked. The one to hang where the people who pump it will see it. Four headline figures and the source and method are printed on the sheet. Available as a dark Night edition and a cream Paper edition.",
    "poster-peak-vs-now": "Six streams of oil and gas ranked by how close each one is to its own best month. Alberta oil sits closest to its peak. Gas is seasonal and BC oil is very small, and the poster says so. Bars start at zero, and the source and method are printed on the sheet. Available as a dark Night edition and a cream Paper edition.",
    "poster-86-of-100": "A hundred dots for every hundred barrels of oil produced in Alberta, Saskatchewan and British Columbia: 86 are Alberta's, 14 are Saskatchewan's and BC's share rounds to under one. Real production figures for September 2026, with the source and method printed on the sheet. Available as a dark Night edition and a cream Paper edition.",
    "poster-decline-shape": "The Arps family of decline curves from b = 0 to b = 1.5 on one sheet: exponential, hyperbolic and harmonic, the shapes every well-file reader should be able to recognise. Equations and a short reading guide are printed on the poster. Available as a dark Night edition and a cream Paper edition.",
    "sheet-units-and-conversions": "A one-page, 11 x 17 inch PDF of oil, gas, energy and pressure conversion factors, plus the rule for turning a volume into a daily rate. Print it for your desk or your truck; for your own use. Instant download.",
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



def fmt_price(a):
    return f"{a:.2f}"


def price_html(kind=None, amount=None):
    a = PRICE[kind] if amount is None else amount
    return f'<span class="price">CAD ${fmt_price(a)} <small>launch price</small></span>'


def pid(kind, slug):
    return f"{kind}-{slug}"


def page_name(kind, slug):
    return f"product-{pid(kind, slug)}.html"


def spi(key, picks, alt):
    """Photos from the Printify/Shopify store (downloaded by shop/fetch_shopify.py): [(file, alt, w, h)], labels."""
    imgs = [(f"sp-{key}-{i}.jpg", f"{alt}, {lab.lower()}", 1000, 1000) for i, lab in picks]
    return imgs, [lab for _i, lab in picks]


APP_PICKS = [(4, "Back, black"), (7, "Back, charcoal"), (10, "Back, navy"), (1, "Front, chest logo"), (6, "Folded")]
MUG_PICKS = [(1, "Front"), (2, "Side"), (3, "Handle"), (4, "Other side")]
HAT_PICKS = [(1, "Front, black"), (2, "Front, charcoal"), (3, "Back"), (4, "Side"), (5, "Other side")]
TOQUE_PICKS = [(1, "Black"), (2, "Charcoal"), (4, "Worn"), (5, "Worn, back"), (7, "Worn, charcoal"), (8, "Worn, charcoal back")]
POSTER_PICKS = [("night", 1, "Night"), ("paper", 1, "Paper"), ("night", 4, "Night, on the wall"), ("paper", 4, "Paper, on the wall"), ("night", 3, "Rolled")]


def catalogue():
    """Every product as a dict: id, kind, slug, title, blurb, images [(file, alt, w, h)], page."""
    out = []
    for s, t, b in POSTERS:
        imgs = [(f"sp-poster-{s}-{ed}-{i}.jpg", f"{t} poster, {lab.lower()}", 1000, 1000) for ed, i, lab in POSTER_PICKS]
        out.append(dict(kind="poster", slug=s, title=t + " poster", short=t, blurb=b, images=imgs, labels=[x[2] for x in POSTER_PICKS]))
    for s, n, k, b in APPAREL:
        imgs, labs = spi(f"{k}-{s}", APP_PICKS, f"{n} {k}")
        out.append(dict(kind=k, slug=s, title=f"{n} {'hoodie' if k == 'hoodie' else 't-shirt'}", short=n, blurb=b, images=imgs, labels=labs))
    for s, n, b in MUGS:
        imgs, labs = spi(f"mug-{s}", MUG_PICKS, f"{n} mug")
        out.append(dict(kind="mug", slug=s, title=f"{n} mug", short=n, blurb=b, images=imgs, labels=labs))
    for s, n, b in HATS:
        imgs, labs = spi(f"hat-{s}", HAT_PICKS, f"{n} hat")
        out.append(dict(kind="hat", slug=s, title=f"{n} hat", short=n, blurb=b, images=imgs, labels=labs))
    for s, n, b in TOQUES:
        imgs, labs = spi(f"toque-{s}", TOQUE_PICKS, f"{n} toque")
        out.append(dict(kind="toque", slug=s, title=f"{n} toque", short=n, blurb=b, images=imgs, labels=labs))
    for s, t, b in SHEETS:
        out.append(dict(kind="sheet", slug=s, title=f"{t} reference sheet", short=t, blurb=b, images=[(f"sheet-{s}.jpg", f"{t} reference sheet", 1000, 1545)]))
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
            f'<h3><a href="{href}">{esc(title)}</a></h3>{extra}{price_html(kind)}<span class="go"><a class="btn primary" href="{href}">Choose options</a></span></div></div>')


def card_of(it):
    """Card for a catalogue item: the showcase image is the back print for apparel, the night colourway for posters."""
    k = it["kind"]
    f, alt, w, h = it["images"][0]
    return prod(it["slug"], k, it["short"], it["blurb"], card_img(f, alt, w, h), w, h)


def kind_label(k):
    return {"poster": "Data-art poster", "hoodie": "Hoodie", "tee": "T-shirt", "sticker": "Sticker", "sheet": "Digital download", "mug": "Mug", "hat": "Hat", "toque": "Toque"}[k]


def body():
    items = catalogue()
    by = {it["id"]: it for it in items}
    of = lambda *kinds: [it for it in items if it["kind"] in kinds]
    grid = lambda lst, cls="pgrid": f'<div class="{cls}">' + "".join(card_of(x) for x in lst) + '</div>'
    o = []
    o.append('<div class="shop-hero"><span class="badge">Now open</span>'
             '<h1>The Tidywells <span class="grad">shop</span></h1>'
             '<p>Hoodies, toques, hats, mugs and sticker packs for people who work in oil and gas, and posters drawn from the open data.</p>'
             '<ul class="trust"><li>Printed to order</li><li>Secure checkout by Shopify</li><li>Prices in CAD, launch price while it lasts</li><li>Size guide on every page</li></ul>'
             '<nav class="chips" aria-label="Shop sections"><a href="#apparel">Apparel</a><a href="#headwear">Toques and hats</a><a href="#drinkware">Mugs</a><a href="#stickers">Sticker packs</a>'
             '<a href="#posters">Posters</a><a href="#downloads">Digital</a><a href="#your-well">Make your own</a></nav></div>')
    o.append('<h2 id="best">Crew favourites</h2>' + grid([by[i] for i in BEST], "pgrid four"))
    o.append('<h2 id="apparel">Apparel</h2><p>Heavy type on the back, a small Tidywells mark on the left chest. True to size, with a size guide on every page.</p>' + grid(of("hoodie", "tee")))
    o.append('<h2 id="headwear">Toques and hats</h2><p>Embroidered text. Warm toques for the winter crew, adjustable hats for the rest of the year.</p>' + grid(of("toque", "hat")))
    o.append('<h2 id="drinkware">Mugs</h2>' + grid(of("mug")))
    stick = [f'<div class="prod" data-slug="bundle-{b[0]}"><div class="pimg">{card_img(b[5], b[1], 1000, 1000)}</div><div class="pi"><span class="tag">{"Most designs" if b[4] == 9 else "Sticker sheet"}</span><h3>{esc(b[1])}</h3><p>{esc(b[2])}</p>'
             f'{price_html(amount=b[3])}<span class="shop-note">About CAD ${fmt_price(b[3] / b[4])} a sticker.</span><span class="go">Ordering needs JavaScript.</span></div></div>' for b in BUNDLES]
    names = "".join(f'<li>{esc(n)}</li>' for _s, n in STICKERS)
    o.append('<h2 id="stickers">Hard-hat sticker sheets</h2><p>Kiss-cut A5 sheets, ready to peel and stick on a hard hat, toolbox or truck dash. Fixed designs per sheet; the bigger sheets fit more, smaller.</p><div class="pgrid">' + "".join(stick) + '</div>'
             f'<details class="fold"><summary>The nine designs</summary><ul class="stk">{names}</ul></details>')
    ps = []
    for it in of("poster"):
        s = it["slug"]
        ps.append(prod(s, "poster", it["short"], it["blurb"], f'<img src="{IMG}sp-poster-{s}-night-1.jpg" alt="{esc(it["short"])} poster, 18 by 24 inch" width="1000" height="1000" loading="lazy">', 1000, 1000))
    o.append('<h2 id="posters">Data-art posters</h2><p>18 × 24 inch, drawn from the open Tidywells dataset. The numbers match <a href="data.html">the CSV you can download</a> and the poster says where they come from. Each comes as a dark Night edition and a cream Paper edition.</p>'
             '<div class="pgrid">' + "".join(ps) + '</div>')
    o.append('<h2 id="downloads">Digital download</h2><p>An 11 × 17 inch sheet to pin up beside your screen. Print it as often as you like for your own use.</p>' + grid(of("sheet")))
    o.append('<div class="well-card" id="your-well"><div class="wc-text"><span class="tag">Make your own</span><h2>Your Well poster</h2>'
             '<p>Turn one well\'s monthly production into a poster, for a well you own or may use. It runs in your browser and the file never leaves your device.</p>'
             '<p><a class="btn primary" href="your-well.html">Make a poster</a></p>'
             '<p class="shop-note">We do not sell prints of other people\'s wells from public files; that needs the regulator\'s written confirmation.</p></div>'
             f'<figure><img src="{IMG}your-well-example.jpg" alt="Example Your Well poster built from synthetic data" width="720" height="960" loading="lazy"><figcaption>Example, made from synthetic data</figcaption></figure></div>')
    o.append('<h2>Good to know</h2><div class="faq"><p><b>How do sizes fit?</b><br>True to size. Every hoodie and tee page has a size guide with flat measurements.</p>'
             '<p><b>Who makes and ships the products?</b><br>Our fulfilment partner. Production and delivery times follow the partner schedule and are shown at checkout.</p>'
             '<p><b>Is this affiliated with a regulator or an operator?</b><br>No. The posters use public regulator data and original wording, and no company names or logos appear on any product. Posters are not investment advice.</p>'
             '<p><b>Where does the money go?</b><br>It helps keep the open data, tools and analysis free. Tidywells is built by one person; see <a href="about.html">About</a>.</p></div>')
    o.append(LINKJS)
    return "\n".join(o)


def home_strip():
    items = {it["id"]: it for it in catalogue()}
    pick = ["hoodie-build-the-pipeline", "hoodie-ottawa-doesnt-pump-oil", "mug-build-the-pipeline", "toque-camp-life", "hat-build-the-pipeline", "poster-record-barrels"]
    cards = ""
    for i in pick:
        it = items[i]
        f, alt, w, h = it["images"][0]
        cards += (f'<a class="prod" href="{it["page"]}" style="text-decoration:none;color:inherit"><img src="{IMG}{f}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy">'
                  f'<div class="pi"><span class="tag">{esc(kind_label(it["kind"]))}</span><h3>{esc(it["short"])}</h3></div></a>')
    return ('<!--SHOP--><section class="strip"><span class="badge">Now open</span>'
            '<h2>The Tidywells shop</h2><p>Hoodies, toques, hats, mugs and sticker packs for people who work in oil and gas, plus posters drawn from real data.</p>'
            f'<div class="pgrid">{cards}</div>'
            f'<p class="shop-note">Hoodies from CAD ${fmt_price(PRICE["hoodie"])} · toques from CAD ${fmt_price(PRICE["toque"])} · mugs from CAD ${fmt_price(PRICE["mug"])} (launch prices)</p>'
            '<p><a class="btn primary" href="shop.html">See the collection</a> <a class="btn" href="shop.html#posters">Data-art posters</a></p></section><!--/SHOP-->')


def product_page(it, items):
    """One search-landing page per product, with structured data (no offer data until a store URL exists)."""
    import json
    t, kind = it["title"], it["kind"]
    imgs = it["images"]
    pics = "".join(f'<img src="{IMG}{f}" alt="{esc(a)}" width="{w}" height="{h}" data-pi="{i}"{"" if i == 0 else " hidden"}>' for i, (f, a, w, h) in enumerate(imgs))
    sw = ""
    if len(imgs) > 1:
        labels = it.get("labels") or ("Night", "Paper")
        sw = '<div class="sw" role="group" aria-label="View">' + "".join(f'<button type="button" data-pi="{i}" aria-pressed="{"true" if i == 0 else "false"}">{l}</button>' for i, l in enumerate(labels[:len(imgs)])) + '</div>'
    tts = '<p class="tts"><strong>True to size.</strong> Order the size you normally wear; the size guide below shows the flat measurements.</p>'
    specs = "".join(f"<li>{esc(x)}</li>" for x in SPECS[kind])
    related = [x for x in items if x["kind"] == kind and x["id"] != it["id"]][:4]
    rel = "".join(f'<a class="prod" href="{r["page"]}" style="text-decoration:none;color:inherit"><img src="{IMG}{r["images"][0][0]}" alt="{esc(r["images"][0][1])}" width="{r["images"][0][2]}" height="{r["images"][0][3]}" loading="lazy"><div class="pi"><h3>{esc(r["short"])}</h3>{price_html(kind)}</div></a>' for r in related)
    ld = {"@context": "https://schema.org", "@type": "Product", "name": t, "description": DESC[it["id"]], "sku": it["id"], "brand": {"@type": "Brand", "name": "Tidywells"},
          "image": [f"https://tidywells.com/{IMG}{f}" for f, *_ in imgs], "url": f"https://tidywells.com/{it['page']}"}
    body_ = (f'<p class="crumb"><a href="shop.html">Shop</a> &rsaquo; {esc(kind_label(kind))}</p>'
             f'<div class="ppage"><div class="pview">{pics}{sw}</div><div class="pdet" data-slug="{esc(it["id"])}"><span class="tag">{esc(kind_label(kind))}</span><h1>{esc(t)}</h1>'
             f'<p class="plead">{esc(it["blurb"])}</p><p>{price_html(kind)}</p><p class="go soon" data-slug="{esc(it["id"])}">Opening soon. <a href="shop.html#waitlist">Get an email when the shop opens</a>.</p>'
             f'<h2>About this design</h2><p>{esc(DESC[it["id"]])}</p>{tts if kind in SIZES else ""}'
             f'<h2>Details</h2><ul class="specs">{specs}</ul>{size_chart(kind) if kind in SIZES else ""}'
             '<p class="shop-note">Launch price in Canadian dollars; shipping and tax are added at checkout and the store confirms the final price. Tidywells is not affiliated with any regulator or operator.</p></div></div>'
             f'<h2>More from this range</h2><div class="pgrid">{rel}</div>')
    body_ += f'<script type="application/ld+json">{json.dumps(ld)}</script><script src="shop-links.js"></script><script src="shop.js"></script>'
    return page(it["page"], t, f"{t} from the Tidywells shop. {it['blurb']}", body_, css="article{max-width:none}")


def posterbox(prefix, topic):
    """'Hang this chart' strip for articles: three matched posters with prices, linking to their product pages."""
    sets = {"snapshot": ["record-barrels", "peak-vs-now", "86-of-100"], "gas": ["peak-vs-now", "record-barrels", "decline-shape"], "decline": ["decline-shape", "record-barrels", "ab-oil"], "default": ["record-barrels", "86-of-100", "decline-shape"]}
    names = {s: t for s, t, _ in POSTERS}
    cards = "".join(f'<a class="prod" href="{prefix}{page_name("poster", s)}" style="text-decoration:none;color:inherit"><img src="{prefix}{IMG}sp-poster-{s}-night-1.jpg" alt="{esc(names[s])} poster" width="1000" height="1000" loading="lazy"><div class="pi"><h3>{esc(names[s])}</h3>{price_html("poster")}</div></a>' for s in sets.get(topic, sets["default"]))
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
                     f"{DESC[pid(k, s)]} True to size. Large back print with a small Tidywells mark on the left chest.", TAGS_BASE + ["funny shirt", "decline curve", "roughneck", "oilfield humor", "gift for him"]))
    for bid, bt, bb, bp, bn, _img in BUNDLES:
        rows.append((bid, f"Sticker pack {bn}", f"{bt}, Hard Hat Stickers, Oil and Gas Humor, Laptop Decals",
                     f"{bb} A5 kiss-cut vinyl sticker sheet made for hard hats, laptops and truck dashboards. No oil company names or logos.", TAGS_BASE + ["hard hat sticker", "laptop sticker", "vinyl sticker", "sticker pack", "oilfield"]))
    for s, n, b in MUGS:
        rows.append((f"mug-{s}", "Mug 11oz", f"{n} Mug, Oilfield Coffee Mug, Oil and Gas Gift",
                     DESC[pid("mug", s)], TAGS_BASE + ["coffee mug", "oilfield mug", "gift for him", "work mug", "oil and gas"]))
    for s, n, b in HATS:
        rows.append((f"hat-{s}", "Hat", f"{n} Embroidered Hat, Oilfield Hat, Oil and Gas Gift",
                     DESC[pid("hat", s)], TAGS_BASE + ["embroidered hat", "dad hat", "oilfield hat", "gift for him", "oil and gas"]))
    for s, n, b in TOQUES:
        rows.append((f"toque-{s}", "Toque", f"{n} Toque Beanie, Embroidered Winter Hat, Oilfield Gift",
                     DESC[pid("toque", s)], TAGS_BASE + ["toque", "beanie", "winter hat", "oilfield", "gift for him"]))
    for s, t, b in SHEETS:
        rows.append((f"sheet-{s}", "Digital download PDF 11x17", f"{t} Cheat Sheet PDF, Oil and Gas Reference, Printable 11x17",
                     DESC[pid("sheet", s)], TAGS_BASE + ["cheat sheet", "printable", "pdf download", "reference", "digital download"]))
    with open(ROOT / "shop" / "listings.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "title", "description", "tags"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], "|".join(list(dict.fromkeys(r[4]))[:13])])
    return rows


def store_links(rows):
    """docs/shop-links.js: the Shopify product page for every listing. A Shopify handle is the lower-cased title with
    apostrophes dropped and every other run of non-alphanumerics turned into one hyphen."""
    base = "https://tidywells.myshopify.com/products/"
    handle = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower().replace("'", "")).strip("-")
    links = {}
    # Shopify handles that differ from the listing title (a duplicated product, a retitled sheet)
    fix = {"complete-sheet-of-9-hard-hat-stickers-oil-and-gas-humor-laptop-decals": "sticker-sheet-of-9-complete-hard-hat-sticker-set-oil-and-gas-humor-laptop-decals"}
    for rid, _type, title, *_ in rows:
        h0 = handle(title)
        h = base + fix.get(h0, h0)
        if rid.startswith("poster-") and rid.endswith(("-night", "-paper")):
            slug, ed = rid[:-6] if rid.endswith("-night") else rid[:-6], rid.rsplit("-", 1)[1]
            links.setdefault(slug, {})[ed] = h
        elif rid.startswith("stickers-"):
            links["bundle-" + rid] = h
        else:
            links[rid] = h
    (DOCS / "shop-links.js").write_text("// Generated by shop/build_shop.py: Shopify product pages. Buttons show only when config.js sets TIDYWELLS_SHOP_OPEN = true.\n"
                                        "window.TIDYWELLS_SHOP_LINKS = " + json.dumps(links, indent=1) + ";\n", encoding="utf-8")


def main():
    store_links(listings())
    html = page("shop.html", "Shop", "Oil and gas hoodies, toques, hats, mugs, stickers and posters drawn from real data from Tidywells.", body(),
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
