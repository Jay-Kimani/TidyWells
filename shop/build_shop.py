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

POSTERS = []  # the old data-art posters were retired; the physical posters are the "print" kind in LEDUC
APPAREL = [  # slug, name, garment, blurb
    ("powered-by-oil", "Powered by Oil", "tee", "Short, clean, and true."),
    ("powered-by-oil", "Powered by Oil", "hoodie", "Short, clean, and true."),
    ("hyperbolic-decline", "Hyperbolic Decline", "hoodie", "HYPERBOLIC DECLINE across the back in white, with a blue decline curve and \"my motivation\" underneath."),
    ("darcys-law", "Darcy's Law", "tee", "How fluid moves through rock."),
]
STICKERS = []  # stickers retired
MUGS = []  # mugs retired
MUG_TITLE = {"leduc": "Leduc Pumpjack Mug, Alberta Oilfield Coffee Mug, Oil and Gas Gift"}
HATS = [("powered-by-oil", "Powered by Oil", "Embroidered text, three words and a fact.")]
PATCH_HATS = [("patch-oval", "Oval Patch Trucker", "Tidywells Patch Trucker Hat, Oilfield Hat, Oil and Gas Gift", "A retro oilfield patch, oval, on a foam-front trucker.")]
TOQUES = [("fire-rescue-blowout", "Fire Rescue Blowout", "The firefighting and blowout specialist patch, embroidered on the cuff."),
          ("powered-by-oil", "Powered by Oil", "Embroidered text, three words and a fact.")]
LEDUC = [  # slug, kind, short name, exact store title, blurb
    ("leduc-pumpjack", "hoodie", "Leduc Pumpjack", "Leduc Pumpjack Hoodie, Alberta Oilfield Gift, Oil and Gas Hoodie", "A Leduc pumpjack across the back, a small Tidywells label on the chest."),
    ("leduc-pumpjack", "tee", "Leduc Pumpjack", "Leduc Pumpjack T-Shirt, Alberta Oilfield Gift, Oil and Gas Tee", "A Leduc pumpjack across the back, a small Tidywells label on the chest."),
]
SHEETS = []  # digital downloads removed: physical posters only
FEATURED = []



LINKJS = ('<script src="shop-links.js"></script><script src="shop-links.js"></script><script src="shop.js"></script>')


PRICE = {"hoodie": 74.99, "tee": 36.99, "mug": 24.99, "hat": 49.99, "toque": 39.99, "poster": 44.99, "sheet": 8.99, "crewneck": 59.99, "print": 44.99}  # CAD prices; confirmed in the store
BUNDLES = []  # stickers retired
SPECS = {
    "poster": ["18 x 24 inch print, Dark Night or cream Paper edition (separate listings)", "Drawn from the open Tidywells dataset, data through September 2026", "Source, method and data window printed on the poster", "Produced and shipped by our fulfilment partner; timing shown at checkout"],
    "hoodie": ["Large design printed on the back, small Tidywells mark on the left chest", "Light-ink design for dark garments", "No oil company names or logos", "Garment colours, sizes and fabric are set in the store listing", "The images above are illustrative mockups of the print placement"],
    "tee": ["Large design printed on the back, small Tidywells mark on the left chest", "Light-ink design for dark garments", "No oil company names or logos", "Garment colours, sizes and fabric are set in the store listing", "The images above are illustrative mockups of the print placement"],
    "sticker": ["A5 kiss-cut sheet, 5.8 x 8.3 inch, with the stickers already laid out", "Peel one off for a hard hat, laptop, toolbox or truck dash", "Fixed designs per sheet; no oil company names or logos", "Final material and finish are set in the store listing"],
    "mug": ["11 oz ceramic mug, design wraps around", "Dishwasher and microwave safe (confirm in the store listing)", "No oil company names or logos"],
    "patchhat": ["Full-colour printed patch design on the front panel of a foam-front mesh-back trucker", "Adjustable snapback; one size fits most (22.8 inch)", "Colour combinations are set in the store listing", "Original artwork, no oil company names or logos"],
    "hat": ["Embroidered text on the front panel", "Adjustable fit; colour set in the store listing", "No oil company names or logos"],
    "crewneck": ["Large design printed on the back, small Tidywells label on the left chest", "Heavy blend crewneck, 50% cotton and 50% polyester", "No oil company names or logos", "Garment colours and sizes are set in the store listing"],
    "print": ["18 x 24 inch print on cream paper with a navy and red rule", "Original artwork, no company names or logos", "Paper finish and shipping are set in the store listing"],
    "toque": ["Cuffed knit toque (beanie) with embroidered cuff", "One size; fabric and lining are set in the store listing", "No oil company names or logos"],
    "sheet": ["11 x 17 inch PDF, instant digital download", "For your own use: print as often as you like", "Standard published conversion factors and public regulator file layouts"],
}

POSTER_TAIL = " Four headline figures sit under the chart, and the source, method and data window are printed at the foot, so it reads like a figure from a report rather than decoration. Available as a dark Night edition and a cream Paper edition."
DESC = {
    "hoodie-leduc-pumpjack": "A Leduc pumpjack in red, black and cream across the back, with Tidywells and Alberta Oilfield Gear across the top. A small Tidywells decline-curve label sits on the left chest. Available in black, navy and white. Original artwork, no company names or logos.",
    "tee-leduc-pumpjack": "A Leduc pumpjack in red, black and cream across the back, with Tidywells and Alberta Oilfield Gear across the top. A small Tidywells decline-curve label sits on the left chest. Available in black, navy and white. Original artwork, no company names or logos.",
    "crewneck-leduc-pumpjack": "A Leduc pumpjack in red, black and cream across the back, with Tidywells and Alberta Oilfield Gear across the top. A small Tidywells decline-curve label sits on the left chest. A heavy blend crewneck in black, navy and white. Original artwork, no company names or logos.",
    "print-leduc-pumpjack": "A Leduc pumpjack in red, black and cream on a cream paper ground, framed with a navy and red rule and Tidywells at the foot. Leduc is where Alberta's modern oil industry began in 1947. 18 x 24 inch print. Original artwork, no company names or logos.",
    "print-oil-and-gas-commission": "A retro tin-sign style Tidywells Oil and Gas Commission poster: a coffee cup and a pumpjack buddy walking out of the Alberta foothills under a Canadian flag. 18 x 24 inch print. Original artwork, no company names or logos. The Oil and Gas Commission is a joke; Tidywells is not affiliated with any regulator or operator.",
    "print-drilling-gear-bigfoot": "A Tidywells Drilling Gear poster: a Sasquatch strolling past a pumpjack at sunset in the Alberta foothills, with a Canadian flag in the background. 18 x 24 inch print. Original artwork, no company names or logos. Tidywells is not affiliated with any regulator or operator.",
    "print-support-natural-resources": "A Tidywells Support Natural Resources poster in a vintage enamel-sign style, established 2013. 18 x 24 inch print. Original artwork, no company names or logos. Tidywells is not affiliated with any regulator or operator.",
    "print-boom-bust-repeat": "A Tidywells Boom. Bust. Repeat. Alberta poster in a vintage tin-sign style. 18 x 24 inch print. Original artwork, no company names or logos. Tidywells is not affiliated with any regulator or operator.",
    "bundle-stickers-leduc-and-tidywells": "One A5 kiss-cut sheet with three stickers: the big Leduc pumpjack, the Tidywells decline-curve label and the Tidywells oilfield patch. Peel one off and stick it on a hard hat, laptop, toolbox or truck dash.",
    "bundle-stickers-3-pack": "A5 kiss-cut sheet with three of our best-known designs: Build the Pipeline, Scrap the Tanker Ban and Powered by Oil. Peel one off and stick it on a hard hat, toolbox or truck dash. About 2.5 inch each.",
    "bundle-stickers-6-pack": "A5 kiss-cut sheet of six designs: Build the Pipeline, Scrap the Tanker Ban, Powered by Oil, Camp Life, Ottawa Doesn't Pump Oil and Darcy's Law. About 2.3 inch each, ready to peel and stick.",
    "bundle-stickers-complete-set": "One A5 kiss-cut sheet with every design in the collection, one of each: nine stickers at about 1.7 inch. The best value per sticker.",
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
    "mug-leduc": "A bold Leduc pumpjack print in red, black and cream on an 11 oz mug, for anyone who grew up near or worked the Alberta oilfield. Original design, no company names or logos.",
    "mug-support-natural-resources": "The Support Natural Resources artwork on an 11 oz mug: a pumpjack, a service rig truck and the Rockies at sunset. Original design, no company names or logos.",
    "mug-bigfoot-drilling-gear": "The Drilling Gear artwork on an 11 oz mug: a Bigfoot walking past a pumpjack and the Canadian flag against a mountain sunset. Original design, no company names or logos.",
    "mug-boom-bust-repeat": "The Boom. Bust. Repeat. Alberta artwork on an 11 oz mug: a pumpjack in front of a red sun, with mountains and pines. Original design, no company names or logos.",
    "mug-fire-rescue-blowout": "The Fire Rescue Blowout patch on an 11 oz mug: a burning derrick against the mountains, Firefighting and Blowout Specialist, Alberta, BC and Sask. Original design, no company names or logos.",
    "mug-oil-and-gas-commission": "The Tidywells Oil and Gas Commission artwork on an 11 oz mug: a cartoon oil drum and wellhead walking the Alberta oilfield. A joke commission, not a real regulator. Original design, no company names or logos.",
    "mug-hyperbolic-decline": "A small decline curve under the line, on an 11 oz mug: for anyone whose enthusiasm follows an Arps curve. Original design, no company names or logos.",
    "hat-powered-by-oil": "Embroidered text on the front of an adjustable hat: powered by oil, three words and a fact. Original design, no company names or logos.",
    "tee-powered-by-oil": "Three words and a fact, in heavy type on the back. For the lunchroom, the truck and everyone who has noticed what the lights run on. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-camp-life": "Two words for anyone who has done the rotation: the bunkhouse, the cafeteria, the long drive in and the longer one home. Heavy type on the back. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-darcys-law": "Darcy's law, set large on the back: flow rate equals permeability times area times pressure difference, over viscosity times length. How fluid moves through rock, first written down in 1856. For engineers, geologists and anyone who has argued about permeability. Printed in light ink for dark garments. Original design, no company names or logos.",
    "sticker-powered-by-oil": "A 3 inch die-cut-style sticker in heavy type. Made for hard hats, lunch kits and truck dashboards.",
    "sticker-camp-life": "A 3 inch die-cut-style sticker for the rotation: camp life. Made for hard hats, lunch kits and truck dashboards.",
    "sticker-darcys-law": "A 3 inch die-cut-style sticker with Darcy's law. For the engineers' laptop lid.",
    "sticker-pv-znrt": "A 3 inch die-cut-style sticker with the real gas law, pV = znRT. For the engineers' laptop lid.",
    "mug-powered-by-oil": "Three words in heavy type on an 11 oz mug. A coffee cup with a point of view. Original design, no company names or logos.",
    "hat-patch-oval": "A retro oilfield patch on a foam-front mesh-back trucker: a burning derrick against the mountains, Tidywells in bold type, Firefighting and Blowout Specialist across the top and Alberta, BC and Sask underneath. Full-colour print, adjustable snapback. Original artwork, no company names or logos.",
    "toque-powered-by-oil": "A cuffed toque with POWERED BY OIL. embroidered in white on the cuff: three words and a fact. Original design, no company names or logos.",
    "toque-fire-rescue-blowout": "A cuffed toque with the Fire Rescue Blowout patch embroidered on the cuff: a burning derrick, the mountains and Alberta, BC and Sask lettering. Original design, no company names or logos.",
    "hoodie-oil-and-gas": "Just the industry's name, big and plain on the back: Oil & Gas. A heavyweight hoodie for the crew, the office and the drive home. Printed in light ink for dark garments. Original design, no company names or logos.",
    "tee-oil-and-gas-crew": "Oil & Gas Crew in heavy type on the back. Simple, clean and easy to wear to the site, the shop or the pub. Printed in light ink for dark garments. Original design, no company names or logos.",
    "poster-record-barrels": "Western Canada's oil, stacked on a zero baseline: Alberta, Saskatchewan and BC from January 2022 to September 2026, with the record month marked. The one to hang where the people who pump it will see it. Four headline figures and the source and method are printed on the sheet. Available as a dark Night edition and a cream Paper edition.",
    "poster-peak-vs-now": "Six streams of oil and gas ranked by how close each one is to its own best month. Alberta oil sits closest to its peak. Gas is seasonal and BC oil is very small, and the poster says so. Bars start at zero, and the source and method are printed on the sheet. Available as a dark Night edition and a cream Paper edition.",
    "poster-86-of-100": "A hundred dots for every hundred barrels of oil produced in Alberta, Saskatchewan and British Columbia: 86 are Alberta's, 14 are Saskatchewan's and BC's share rounds to under one. Real production figures for September 2026, with the source and method printed on the sheet. Available as a dark Night edition and a cream Paper edition.",
    "poster-decline-shape": "The Arps family of decline curves from b = 0 to b = 1.5 on one sheet: exponential, hyperbolic and harmonic, the shapes every well-file reader should be able to recognise. Equations and a short reading guide are printed on the poster. Available as a dark Night edition and a cream Paper edition.",
    "sheet-units-and-conversions": "A one-page, 11 x 17 inch PDF of oil, gas, energy and pressure conversion factors, plus the rule for turning a volume into a daily rate. Print it for your desk or your truck; for your own use. Instant download.",
}
SIZES = {
    "crewneck": ("Unisex crewneck", ["S", "M", "L", "XL", "2XL", "3XL"], [(20, 26), (22, 27), (24, 28), (26, 29), (28, 30), (30, 31)]),
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
    return f'<span class="price">CAD ${fmt_price(a)}</span>'


def pid(kind, slug):
    return f"{kind}-{slug}"


def page_name(kind, slug):
    return f"product-{pid(kind, slug)}.html"


def spi(key, picks, alt):
    """Photos from the Printify/Shopify store (downloaded by shop/fetch_shopify.py): [(file, alt, w, h)], labels."""
    imgs = [(f"sp-{key}-{i}.jpg", f"{alt}, {lab.lower()}", 1000, 1000) for i, lab in picks]
    return imgs, [lab for _i, lab in picks]


HOODIE_PICKS = [(1, "Front, black"), (4, "Back, black"), (11, "Worn, black"), (9, "Worn, black, back"), (10, "Worn, black (2)"), (8, "Worn, black (3)"), (7, "Lifestyle, black"), (6, "Folded, black"),
                (2, "Front, charcoal"), (12, "Back, charcoal"), (19, "Worn, charcoal"), (17, "Worn, charcoal, back"), (18, "Worn, charcoal (2)"), (16, "Worn, charcoal (3)"),
                (3, "Front, navy"), (20, "Back, navy"), (28, "Worn, navy"), (26, "Worn, navy, back"), (27, "Worn, navy (2)"), (25, "Worn, navy (3)")]
TEE_PICKS = [(1, "Front, black"), (4, "Back, black"), (9, "Worn, black"), (10, "Worn, black, back"), (8, "Worn, black (3)"), (7, "Lifestyle, black"), (6, "Folded, black"),
             (2, "Front, charcoal"), (11, "Back, charcoal"), (16, "Worn, charcoal"), (17, "Worn, charcoal, back"),
             (3, "Front, navy"), (18, "Back, navy"), (24, "Worn, navy"), (25, "Worn, navy, back"), (23, "Worn, navy (3)")]
APP_PICKS = HOODIE_PICKS
PATCH_PICKS = [(1, "Black, front"), (5, "Black, worn"), (3, "Black, side"), (4, "Black, back")]
MUG_PICKS = [(1, "Front"), (5, "On the desk"), (6, "On the table"), (2, "Side"), (3, "Handle")]
HAT_PICKS = [(1, "Front, black"), (6, "Worn, black"), (7, "Worn, black, back"), (2, "Front, charcoal"), (12, "Worn, charcoal"), (13, "Worn, charcoal, back"), (3, "Back"), (4, "Side")]
LEDUC_PICKS = {
    "hoodie": [(4, "Back, black"), (1, "Front, black"), (11, "Worn, black"), (9, "Worn, black, back"), (12, "Back, navy"), (2, "Front, navy"), (19, "Worn, navy"), (17, "Worn, navy, back"), (20, "Back, white"), (3, "Front, white")],
    "tee": [(4, "Back, black"), (1, "Front, black"), (9, "Worn, black"), (10, "Worn, black, back"), (11, "Back, navy"), (2, "Front, navy"), (16, "Worn, navy"), (17, "Worn, navy, back"), (18, "Back, white"), (3, "Front, white")],
    "crewneck": [(8, "Back, black"), (2, "Front, black"), (11, "Worn, black"), (12, "Back, navy"), (3, "Front, navy"), (16, "Worn, navy"), (4, "Back, white"), (1, "Front, white"), (7, "Worn, white")],
    "print": [(2, "Poster"), (4, "On the wall"), (3, "Rolled")],
}
TOQUE_PICKS = [(1, "Black"), (2, "Charcoal"), (4, "Worn"), (5, "Worn, back"), (7, "Worn, charcoal"), (8, "Worn, charcoal back")]
POSTER_PICKS = [("night", 1, "Night"), ("paper", 1, "Paper"), ("night", 4, "Night, on the wall"), ("paper", 4, "Paper, on the wall"), ("night", 3, "Rolled")]


NEWSETS = [  # slug, short name, {kind: exact store title}, blurb, colours, tags
    ("drilling-gear", "Drilling Gear", {"hoodie": "Tidywells Drilling Gear Hoodie, Sasquatch Pumpjack, Alberta Oilfield Gift", "tee": "Tidywells Drilling Gear T-Shirt, Sasquatch Pumpjack, Alberta Oilfield Gift"},
     "A Sasquatch walking past a pumpjack under a retro sunset, Drilling Gear across the back.", "black and navy", ["sasquatch", "pumpjack", "retro sunset"]),
    ("support-natural-resources", "Support Natural Resources", {"hoodie": "Tidywells Support Natural Resources Hoodie, Pumpjack and Rig Graphic, Alberta Oilfield Gift", "tee": "Tidywells Support Natural Resources T-Shirt, Pumpjack and Rig Graphic, Alberta Oilfield Gift"},
     "A pumpjack, a rig and a service truck under a rust-orange sun, Support Natural Resources across the back.", "black and navy", ["pumpjack", "service truck", "oilfield gift"]),
]
_KIND_W = {"hoodie": "hoodie", "tee": "t-shirt"}
_KIND_LABEL = {"hoodie": "Hoodie", "tee": "T-shirt"}
_P1 = {"hoodie": [(4, "Back, black"), (1, "Front, black"), (11, "Worn, black"), (9, "Worn, black, back"), (12, "Back, navy"), (2, "Front, navy"), (19, "Worn, navy"), (17, "Worn, navy, back"), (20, "Back, white"), (3, "Front, white")],
       "tee": [(4, "Back, black"), (1, "Front, black"), (9, "Worn, black"), (10, "Worn, black, back"), (11, "Back, navy"), (2, "Front, navy"), (16, "Worn, navy"), (17, "Worn, navy, back"), (18, "Back, white"), (3, "Front, white")],
       "crewneck": [(8, "Back, black"), (2, "Front, black"), (11, "Worn, black"), (12, "Back, navy"), (3, "Front, navy"), (16, "Worn, navy"), (4, "Back, white"), (1, "Front, white"), (7, "Worn, white")]}
_P2 = {"hoodie": [(4, "Back, black"), (1, "Front, black"), (7, "Worn, black"), (8, "Worn, black, back"), (12, "Back, navy"), (2, "Front, navy"), (15, "Worn, navy"), (16, "Worn, navy, back")],
       "tee": [(3, "Back, black"), (1, "Front, black"), (8, "Worn, black"), (9, "Worn, black, back"), (10, "Back, navy"), (2, "Front, navy"), (15, "Worn, navy"), (16, "Worn, navy, back")],
       "crewneck": [(3, "Back, black"), (1, "Front, black"), (6, "Worn, black"), (7, "Back, navy"), (2, "Front, navy"), (10, "Worn, navy")]}
_P3 = {"hoodie": [(2, "Back"), (3, "Back, hood up"), (1, "Front"), (4, "Folded")], "tee": [(2, "Back"), (1, "Front"), (4, "Folded")], "crewneck": [(2, "Back"), (1, "Front"), (5, "Worn"), (3, "Folded"), (4, "Flat lay")]}
NEW_PICKS = {"drilling-gear": _P2, "support-natural-resources": _P2}
_FAB = {"hoodie": "A heavy blend hooded sweatshirt, 50% cotton and 50% polyester.", "tee": "A soft, lightweight unisex tee in ring-spun cotton."}
_ART = {"drilling-gear": "A retro sunset graphic of a Sasquatch walking past a pumpjack, the Rockies and a maple leaf behind, with Tidywells across the top and Drilling Gear across the bottom.",
        "support-natural-resources": "A bold Support Natural Resources graphic across the back: a pumpjack, a drilling rig, storage tanks, mountains and pines, with a service truck in front, under a rust-orange sun."}
for _s, _n, _t, _b, _c, _tg in NEWSETS:
    for _k in _t:
        DESC[pid(_k, _s)] = f"{_ART[_s]} A small Tidywells decline-curve logo sits on the left chest. Available in {_c}. {_FAB[_k]} Original artwork, no company names or logos."
# Hand-edited galleries (images, alt text, view labels, description), written by shop/snapshot_galleries.py.
# They override the pick lists above so rebuilding never undoes a manual edit.
GALLERIES = json.loads((Path(__file__).parent / "galleries.json").read_text(encoding="utf-8")) if (Path(__file__).parent / "galleries.json").exists() else {}
for _id, _g in GALLERIES.items():
    DESC[_id] = _g["desc"]
SPECS.update({
    "hoodie-art": ["Large design printed on the back, small Tidywells logo on the left chest", "Heavy blend hooded sweatshirt, 50% cotton and 50% polyester", "Original artwork, no company names or logos", "Garment colours and sizes are set in the store listing"],
    "tee-art": ["Large design printed on the back, small Tidywells logo on the left chest", "Soft lightweight unisex tee, ring-spun cotton", "Original artwork, no company names or logos", "Garment colours and sizes are set in the store listing"],
    "crewneck-art": ["Large design printed on the back, small Tidywells logo on the left chest", "Heavy blend crewneck, 50% cotton and 50% polyester", "Original artwork, no company names or logos", "Garment colours and sizes are set in the store listing"],
})


def catalogue():
    """Every product as a dict: id, kind, slug, title, blurb, images [(file, alt, w, h)], page."""
    out = []
    for s, t, b in POSTERS:
        imgs = [(f"sp-poster-{s}-{ed}-{i}.jpg", f"{t} poster, {lab.lower()}", 1000, 1000) for ed, i, lab in POSTER_PICKS]
        out.append(dict(kind="poster", slug=s, title=t + " poster", short=t, blurb=b, images=imgs, labels=[x[2] for x in POSTER_PICKS]))
    for s, n, k, b in APPAREL:
        imgs, labs = spi(f"{k}-{s}", HOODIE_PICKS if k == "hoodie" else TEE_PICKS, f"{n} {k}")
        out.append(dict(kind=k, slug=s, title=f"{n} {'hoodie' if k == 'hoodie' else 't-shirt'}", short=n, blurb=b, images=imgs, labels=labs))
    for s, k, n, t, b in LEDUC:
        imgs, labs = spi(f"{k}-{s}", LEDUC_PICKS[k], f"{n} {k}")
        out.append(dict(kind=k, slug=s, title=t if False else f"{n} " + {"hoodie": "hoodie", "tee": "t-shirt", "crewneck": "crewneck", "print": "poster"}[k], short=n, blurb=b, images=imgs, labels=labs, **({"specs": f"{k}-art"} if k != "print" else {})))
    for s, n, tl, b, _c, _tg in NEWSETS:
        for k in tl:
            imgs, labs = spi(f"{k}-{s}", NEW_PICKS[s][k], f"{n} {k}")
            out.append(dict(kind=k, slug=s, title=f"{n} {_KIND_W[k]}", short=n, blurb=b, images=imgs, labels=labs, specs=f"{k}-art"))
    for s, n, b in MUGS:
        imgs, labs = spi(f"mug-{s}", MUG_PICKS, f"{n} mug")
        out.append(dict(kind="mug", slug=s, title=f"{n} mug", short=n, blurb=b, images=imgs, labels=labs))
    for s, n, b in HATS:
        imgs, labs = spi(f"hat-{s}", HAT_PICKS, f"{n} hat")
        out.append(dict(kind="hat", slug=s, title=f"{n} hat", short=n, blurb=b, images=imgs, labels=labs))
    for s, n, _t, b in PATCH_HATS:
        imgs, labs = spi(f"hat-{s}", PATCH_PICKS, f"{n} hat")
        out.append(dict(kind="hat", slug=s, title=f"{n} hat", short=n, blurb=b, images=imgs, labels=labs, specs="patchhat"))
    for s, n, b in TOQUES:
        imgs, labs = spi(f"toque-{s}", TOQUE_PICKS, f"{n} toque")
        out.append(dict(kind="toque", slug=s, title=f"{n} toque", short=n, blurb=b, images=imgs, labels=labs))
    for s, t, b in SHEETS:
        out.append(dict(kind="sheet", slug=s, title=f"{t} reference sheet", short=t, blurb=b, images=[(f"sheet-{s}.jpg", f"{t} reference sheet", 1000, 1545)]))
    for it in out:
        it["id"] = pid(it["kind"], it["slug"])
        it["page"] = page_name(it["kind"], it["slug"])
        g = GALLERIES.get(it["id"])
        if g:
            it["images"] = [tuple(i) for i in g["images"]]
            it["labels"] = g["labels"]
            it["blurb"] = g["blurb"]
            SPECS["page-" + it["id"]] = g["specs"]
            it["specs"] = "page-" + it["id"]
    return out


def sticker_items():
    """The three sticker sheets, each with its own product page (kept out of catalogue(): they have their own price and no size options)."""
    out = []
    for bid, bt, bb, bp, bn, img in BUNDLES:
        out.append(dict(kind="sticker", slug=bid, id="bundle-" + bid, page=f"product-bundle-{bid}.html", title=bt, short=bt, blurb=bb, price=bp,
                        images=[(img, bt, 1000, 1000)]))
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
    return {"poster": "Data-art poster", "hoodie": "Hoodie", "tee": "T-shirt", "sticker": "Sticker sheet", "sheet": "Digital download", "mug": "Mug", "hat": "Hat", "toque": "Toque", "crewneck": "Crewneck", "print": "Poster"}[k]


def body():
    items = catalogue()
    by = {it["id"]: it for it in items}
    of = lambda *kinds: [it for it in items if it["kind"] in kinds]
    grid = lambda lst, cls="pgrid": f'<div class="{cls}">' + "".join(card_of(x) for x in lst) + '</div>'
    o = []
    o.append('<div class="shop-hero"><h1>Shop</h1>'
             '<p class="shop-meta">Delivery in 5 to 7 business days &middot; Prices in CAD &middot; Secure checkout by Shopify</p>'
             '<nav class="chips" aria-label="Shop sections"><a href="#apparel">Apparel</a><a href="#headwear">Toques and hats</a>'
             '<a href="#downloads">Free sheets</a></nav></div>')
    o.append('<h2 id="apparel">Apparel</h2>' + grid(of("hoodie", "crewneck", "tee")))
    o.append('<h2 id="headwear">Toques and hats</h2>' + grid(of("toque", "hat")))
    dl = [("tidywells-units-and-conversions.pdf", "dl-units.png", "Units & Conversions", "Oil, gas, energy and pressure factors, plus the rule for turning a monthly volume into a daily rate."),
          ("tidywells-decline-curves-one-page.pdf", "dl-decline.png", "Decline Curves, One Page", "The Arps family in the order you will meet it: exponential, hyperbolic, harmonic."),
          ("tidywells-regulator-data-gotchas.pdf", "dl-gotchas.png", "Regulator Data Gotchas", "The unit and layout traps in public regulator production files.")]
    cards = "".join(f'<div class="prod"><a class="pimg" href="downloads/{f}">{card_img(im, t, 440, 680)}</a><div class="pi"><span class="tag">Free PDF</span><h3><a href="downloads/{f}">{esc(t)}</a></h3><p>{esc(b)}</p><span class="shop-note">11 x 17 inch. For your own use, print as often as you like.</span><span class="go"><a class="btn primary" href="downloads/{f}" download>Download free</a></span></div></div>' for f, im, t, b in dl)
    o.append('<h2 id="downloads">Free reference sheets</h2><p>Pin one up beside your screen. They are free to download.</p><div class="pgrid">' + cards + '</div>')
    o.append('<h2>Good to know</h2><div class="faq"><p><b>How do sizes fit?</b><br>True to size. Every hoodie and tee page has a size guide with flat measurements.</p>'
             '<p><b>Who makes and ships the products?</b><br>Our fulfilment partner makes and ships each order. Delivery takes about 5 to 7 business days; the shipping cost is shown at checkout before you pay.</p>'
             '<p><b>Is this affiliated with a regulator or an operator?</b><br>No. No company names or logos appear on any product.</p>'
             '<p><b>Where does the money go?</b><br>It helps keep the open data, tools and analysis free. Tidywells is built by one person; see <a href="about.html">About</a>.</p></div>')
    o.append(LINKJS)
    return "\n".join(o)


def home_strip():
    items = {it["id"]: it for it in catalogue()}
    pick = ["hoodie-leduc-pumpjack", "tee-powered-by-oil", "toque-fire-rescue-blowout", "toque-powered-by-oil", "hat-patch-oval", "hat-powered-by-oil"]
    cards = ""
    for i in pick:
        it = items[i]
        f, alt, w, h = it["images"][0]
        cards += (f'<a class="prod" href="{it["page"]}" style="text-decoration:none;color:inherit"><img src="{IMG}{f}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy">'
                  f'<div class="pi"><span class="tag">{esc(kind_label(it["kind"]))}</span><h3>{esc(it["short"])}</h3></div></a>')
    return ('<!--SHOP--><section class="strip">'
            '<h2>Shop</h2>'
            f'<div class="pgrid">{cards}</div>'
            '<p><a class="btn primary" href="shop.html">Shop all</a></p></section><!--/SHOP-->')


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
    specs = "".join(f"<li>{esc(x)}</li>" for x in SPECS[it.get("specs") or kind])
    related = [x for x in items if x["kind"] == kind and x["id"] != it["id"]][:4]
    rel = "".join(f'<a class="prod" href="{r["page"]}" style="text-decoration:none;color:inherit"><img src="{IMG}{r["images"][0][0]}" alt="{esc(r["images"][0][1])}" width="{r["images"][0][2]}" height="{r["images"][0][3]}" loading="lazy"><div class="pi"><h3>{esc(r["short"])}</h3>{price_html(kind, r.get("price"))}</div></a>' for r in related)
    ld = {"@context": "https://schema.org", "@type": "Product", "name": t, "description": DESC[it["id"]], "sku": it["id"], "brand": {"@type": "Brand", "name": "Tidywells"},
          "image": [f"https://tidywells.com/{IMG}{f}" for f, *_ in imgs], "url": f"https://tidywells.com/{it['page']}"}
    guide = size_chart(kind).replace("<h2>Size guide</h2>", "") if kind in SIZES else ""
    acc = (f'<details open><summary>About this design</summary><p>{esc(DESC[it["id"]])}</p></details>'
           f'<details><summary>Details</summary>{tts if kind in SIZES else ""}<ul class="specs">{specs}</ul></details>'
           + (f'<details id="size-guide"><summary>Size guide</summary>{guide}</details>' if guide else "")
           + '<details><summary>Shipping and returns</summary><p>Delivered in about 5 to 7 business days. Shipping and tax are added at checkout and the store confirms the final price in Canadian dollars. Tidywells is not affiliated with any regulator or operator.</p></details>')
    body_ = (f'<div class="pdp"><p class="crumb"><a href="shop.html">Shop</a> / {esc(kind_label(kind))}</p>'
             f'<div class="ppage"><div class="pview">{pics}{sw}</div><div class="pdet" data-slug="{esc(it["id"])}"><span class="tag">{esc(kind_label(kind))}</span><h1>{esc(t)}</h1>'
             f'<p class="plead">{esc(it["blurb"])}</p><p class="pprice">{price_html(kind, it.get("price"))}</p><p class="go soon" data-slug="{esc(it["id"])}">Opening soon. <a href="shop.html#waitlist">Get an email when the shop opens</a>.</p>'
             f'<div class="pacc">{acc}</div></div></div>'
             f'<h2 class="pmore">More from this range</h2><div class="pgrid">{rel}</div></div>')
    body_ += f'<script type="application/ld+json">{json.dumps(ld)}</script><script src="shop-links.js"></script><script src="shop.js"></script>'
    return page(it["page"], t, f"{t} from the Tidywells shop. {it['blurb']}", body_, css="article{max-width:none}")


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
    for s, k, n, t, b in LEDUC:
        rows.append((f"{k}-{s}", {"hoodie": "Hoodie", "tee": "T-shirt", "crewneck": "Crewneck", "print": "Poster 18x24in"}[k], t, DESC[pid(k, s)], TAGS_BASE + ["leduc", "pumpjack", "alberta", "oilfield gift", "gift for him"]))
    for s, n, tl, b, _c, tg in NEWSETS:
        for k, t in tl.items():
            rows.append((f"{k}-{s}", _KIND_LABEL[k], t, DESC[pid(k, s)], TAGS_BASE + tg + ["oilfield gift", "gift for him"]))
    for s, n, k, b in APPAREL:
        rows.append((f"{k}-{s}", "Hoodie" if k == "hoodie" else "T-shirt", f"{n} {'Hoodie' if k == 'hoodie' else 'T-Shirt'}, Oil and Gas Humor, Decline Curve Gift",
                     f"{DESC[pid(k, s)]} True to size. Large back print with a small Tidywells mark on the left chest.", TAGS_BASE + ["funny shirt", "decline curve", "roughneck", "oilfield humor", "gift for him"]))
    for bid, bt, bb, bp, bn, _img in BUNDLES:
        rows.append((bid, f"Sticker pack {bn}", f"{bt}, Hard Hat Stickers, Oil and Gas Humor, Laptop Decals",
                     f"{bb} A5 kiss-cut vinyl sticker sheet made for hard hats, laptops and truck dashboards. No oil company names or logos.", TAGS_BASE + ["hard hat sticker", "laptop sticker", "vinyl sticker", "sticker pack", "oilfield"]))
    for s, n, b in MUGS:
        rows.append((f"mug-{s}", "Mug 11oz", MUG_TITLE.get(s, f"{n} Mug, Oilfield Coffee Mug, Oil and Gas Gift"),
                     DESC[pid("mug", s)], TAGS_BASE + ["coffee mug", "oilfield mug", "gift for him", "work mug", "oil and gas"]))
    for s, n, b in HATS:
        rows.append((f"hat-{s}", "Hat", f"{n} Embroidered Hat, Oilfield Hat, Oil and Gas Gift",
                     DESC[pid("hat", s)], TAGS_BASE + ["embroidered hat", "dad hat", "oilfield hat", "gift for him", "oil and gas"]))
    for s, n, t, b in PATCH_HATS:
        rows.append((f"hat-{s}", "Hat", t, DESC[pid("hat", s)], TAGS_BASE + ["trucker hat", "patch hat", "oilfield hat", "gift for him", "oil and gas"]))
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
    fix = {"hyperbolic-decline-hoodie-oil-and-gas-humor-decline-curve-gift": "hyperbolic-decline-my-motivation-hoodie-oilfield-humor-oil-and-gas-gift", "powered-by-oil-hoodie-oil-and-gas-humor-decline-curve-gift": "powered-by-oil-hoodie-oil-and-gas-humor-alberta-oilfield-gift", "leduc-pumpjack-mug-alberta-oilfield-coffee-mug-oil-and-gas-gift": "build-the-pipeline-mug-oilfield-coffee-mug-oil-and-gas-gift", "fire-rescue-blowout-toque-beanie-embroidered-winter-hat-oilfield-gift": "camp-life-toque-beanie-embroidered-winter-hat-oilfield-gift", "powered-by-oil-toque-beanie-embroidered-winter-hat-oilfield-gift": "powered-by-oil-toque-beanie-embroidered-winter-hat-oilfield-gift", "leduc-and-tidywells-sticker-sheet-hard-hat-stickers-oil-and-gas-humor-laptop-decals": "sticker-sheet-of-3-leduc-pumpjack-and-tidywells-logo-stickers-oilfield-laptop-decals", "complete-sheet-of-9-hard-hat-stickers-oil-and-gas-humor-laptop-decals": "sticker-sheet-of-9-complete-hard-hat-sticker-set-oil-and-gas-humor-laptop-decals"}
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
    html = page("shop.html", "Shop", "Oil and gas hoodies, t-shirts, toques and hats from Tidywells.", body(),
                css="article{max-width:none}")
    (DOCS / "shop.html").write_text(html, encoding="utf-8")
    items = catalogue()
    for it in items:
        (DOCS / it["page"]).write_text(product_page(it, items), encoding="utf-8")
    for it in sticker_items():
        (DOCS / it["page"]).write_text(product_page(it, sticker_items()), encoding="utf-8")
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
