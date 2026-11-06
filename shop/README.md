# Tidywells shop: how it is built and how to launch it

Everything the shop sells is generated from code in this folder, so it can be rebuilt, checked and changed like the rest of the project.

| File | What it does |
|---|---|
| `art.py` | 18 data-art posters (9 designs x Night/Paper) computed from `docs/data/tidywells-monthly-production.csv` |
| `art_goods.py` | 12 apparel designs (light and dark ink), garment mockups, 6 stickers, 2 notebook covers |
| `cheats.py` | 3 printable 11 x 17 reference sheets |
| `render.js` | Renders SVG/HTML to print PNGs (poster 5400x7200 = 300 dpi at 18x24 in, apparel 3600x4800 transparent), JPEG previews and PDFs |
| `build_shop.py` | Writes `docs/shop.html`, `docs/your-well.html`, the home-page strip, and `listings.csv` (store titles, descriptions, tags) |

Rebuild the site pages after changing the catalogue: `python shop/build_shop.py && python posts/build_feed.py`.
Rebuild the artwork (needs Node, Playwright and the `@fontsource` packages for Fraunces, Inter and IBM Plex Mono, all SIL OFL):

```
python shop/art.py out && python shop/art_goods.py out && python shop/cheats.py out
# merge out/manifest.json and out/manifest-sheets.json, then:
node shop/render.js out/manifest-all.json     # print files land in out/print, previews in out/web
```

The previews on the site are the files in `docs/img/shop/`. Print-size files are not committed (about 45 MB); regenerate them with the commands above.

## Launch checklist (the parts only you can do)

1. **Search trademarks first.** Search the Canadian (CIPO) and US (USPTO) databases for every slogan and for the shop name before you print anything. The slogans are plain phrases, but a search is cheap and a takedown is not.
2. **Pick a storefront.** Printful or Printify for production and shipping, connected to Etsy (search traffic) and/or Shopify or Square (your own store). Use `listings.csv` for titles, descriptions and tags (Etsy limits are already respected).
3. **Upload print files**: posters `print/posters/*.png` (18x24 in), apparel `print/apparel/*-light-ink-*.png` on black, navy and heather-dark garments and `*-dark-ink-*.png` on white, sand and light garments, stickers `print/stickers/*.png`, notebooks `print/notebooks/*.png`, digital sheets `print/digital/*.pdf`.
4. **Order samples** of one hoodie, one tee, one poster and one sticker before you publish. Check colour, ink contrast on each garment colour and the poster print quality.
5. **Set prices yourself** from the supplier's base costs, shipping and fees. This repo deliberately contains no prices.
6. **Connect the site.** In `docs/config.js` set `TIDYWELLS_SHOP_URL` to your storefront (https only). The badge changes to "Now open" and every card shows "View in store". Per-product links go in `TIDYWELLS_SHOP_LINKS` (keys are the `data-slug` values on `shop.html`). `tests/test_shop.py` will then need updating on purpose: it blocks prices and sale wording while no store is connected.
7. **Business basics.** Register the business and tax setup as your province requires (ask an accountant), and check marketplace terms.
8. **Well-level prints.** The "Your Well" tool runs in the visitor's browser on their own data. Do not sell prints of specific named wells from public files until the regulator confirms the terms in writing.

## Honesty rules the tests enforce

- Poster figures match the open dataset (recomputed from the CSV in a test).
- No company names or logos in product text or art.
- No prices, "sale" or discount wording until a store URL is set. Garment images are labelled as illustrative mockups.

## Prices, bundles and product pages
- Launch prices (CAD) are proposals in `shop/build_shop.py` (`PRICE`, `BUNDLES`). Check each against the supplier's base cost, shipping and fees before opening; margins are NOT verified.
- Every item has its own page (`docs/product-*.html`), generated. Product JSON-LD carries no `offers` until the shop is live.
- Waitlist form posts to the Buttondown action in `docs/config.js` with tag `shop-launch`.
- Articles carry a poster box after `</main>`; Dataset JSON-LD on data.html comes from `docs/data/manifest.json`.
