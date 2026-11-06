// Shop page behaviour: colourway swatches; store links appear only when config.js sets them.
(function () {
  "use strict";
  // product page: colourway switch between the pictures
  document.querySelectorAll(".pview").forEach(function (v) {
    v.querySelectorAll(".sw button").forEach(function (b) {
      b.addEventListener("click", function () {
        v.querySelectorAll("img[data-pi]").forEach(function (im) { im.hidden = im.getAttribute("data-pi") !== b.getAttribute("data-pi"); });
        v.querySelectorAll(".sw button").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
      });
    });
  });
  document.querySelectorAll(".prod").forEach(function (card) {
    var img = card.querySelector("img[data-base]");
    if (img) {
      card.querySelectorAll(".sw button").forEach(function (b) {
        b.addEventListener("click", function () {
          img.src = img.getAttribute("data-base") + b.getAttribute("data-cw") + ".jpg";
          card.querySelectorAll(".sw button").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
        });
      });
    }
  });
  document.addEventListener("DOMContentLoaded", function () {
  var action = window.TIDYWELLS_NEWSLETTER_ACTION || "";
  document.querySelectorAll(".waitlist").forEach(function (wl) {
  if (action) {
    wl.innerHTML = '<form action="' + action.replace(/"/g, "") + '" method="post" target="_blank"><input type="hidden" value="1" name="embed"><input type="hidden" name="tag" value="shop-launch">' +
      '<input type="email" name="email" required placeholder="you@example.com" aria-label="Email address"><button type="submit" class="btn primary">Tell me when it opens</button></form>' +
      '<p class="shop-note">You will be added to the Tidywells email list with a shop-launch tag. Unsubscribe any time from any email.</p>';
  } else {
    wl.innerHTML = '<p class="shop-note">Follow on <a href="https://tidywells.substack.com/" target="_blank" rel="noopener">Substack</a> to hear when the shop opens.</p>';
  }
  });
  // Shop open: cards point to the product page on this site, where the buy widget (below) talks to Shopify's Storefront API.
  var open = window.TIDYWELLS_SHOP_OPEN === true;
  if (open) {
    document.querySelectorAll(".badge").forEach(function (b) { b.textContent = "Now open"; });
    twHype();
    var st = document.createElement("style"); st.textContent = "#waitlist,#waitlist2,.waitlist-end{display:none!important}"; document.head.appendChild(st);
    document.querySelectorAll(".prod .go").forEach(function (go) {
      var a = go.parentNode.querySelector("h3 a");
      if (a) { go.className = "go"; go.innerHTML = '<a class="btn primary" href="' + a.getAttribute("href") + '">Choose options</a>'; }
    });
  }
  });
})();

// product page: click the picture for a larger preview; click again to zoom in, Esc or the x to close
(function () {
  "use strict";
  var view = document.querySelector(".pview");
  if (!view) return;
  var box, img, zoomed = false;
  function build() {
    box = document.createElement("div");
    box.className = "lb"; box.hidden = true; box.setAttribute("role", "dialog"); box.setAttribute("aria-modal", "true"); box.setAttribute("aria-label", "Larger picture");
    box.innerHTML = '<button type="button" class="lb-x" aria-label="Close">&times;</button><div class="lb-s"><img alt=""></div><p class="lb-h">Click the picture to zoom, Esc to close</p>';
    document.body.appendChild(box);
    img = box.querySelector("img");
    box.addEventListener("click", function (e) { if (e.target === img) { zoomed = !zoomed; box.classList.toggle("zoom", zoomed); } else close(); });
    document.addEventListener("keydown", function (e) { if (!box.hidden && e.key === "Escape") close(); });
  }
  function open(src, alt) {
    if (!box) build();
    img.src = src; img.alt = alt || ""; zoomed = false; box.classList.remove("zoom"); box.hidden = false;
    document.documentElement.style.overflow = "hidden"; box.querySelector(".lb-x").focus();
  }
  function close() { box.hidden = true; document.documentElement.style.overflow = ""; }
  view.querySelectorAll("img").forEach(function (im) {
    im.tabIndex = 0; im.setAttribute("role", "button"); im.style.cursor = "zoom-in";
    function go() { open(im.getAttribute("data-full") || im.currentSrc || im.src, im.alt); }
    im.addEventListener("click", go);
    im.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
  });
})();

// Buy widget: products, options and checkout come from Shopify's Storefront API; the visitor never leaves tidywells.com until the
// hosted Shopify checkout. Needs config.js: TIDYWELLS_SHOP_OPEN = true and TIDYWELLS_STOREFRONT = {domain, token} (the token is public by design).
function twBuy() {
  "use strict";
  var cfg = window.TIDYWELLS_STOREFRONT, links = window.TIDYWELLS_SHOP_LINKS || {};
  if (window.TIDYWELLS_SHOP_OPEN !== true || !cfg || !cfg.domain || !cfg.token) return;
  var API = "https://" + cfg.domain + "/api/2025-01/graphql.json", KEY = "tw_cart";
  function gql(q, v) {
    return fetch(API, { method: "POST", headers: { "Content-Type": "application/json", "X-Shopify-Storefront-Access-Token": cfg.token }, body: JSON.stringify({ query: q, variables: v || {} }) })
      .then(function (r) { return r.json(); }).then(function (j) { if (j.errors) throw new Error(j.errors[0].message); return j.data; });
  }
  function store(k, v) { try { if (v === undefined) return JSON.parse(localStorage.getItem(k) || "null"); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, JSON.stringify(v)); } catch (e) { return null; } }
  var CART = "cart{id checkoutUrl totalQuantity}";
  function bar(c) {
    var el = document.getElementById("tw-cart");
    if (!c || !c.totalQuantity) { if (el) el.remove(); return; }
    if (!el) { el = document.createElement("a"); el.id = "tw-cart"; el.className = "btn primary"; el.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:50;box-shadow:0 6px 24px rgba(0,0,0,.25)"; document.body.appendChild(el); }
    el.href = c.checkoutUrl; el.textContent = "Checkout (" + c.totalQuantity + ")";
  }
  function add(variantId, qty) {
    var saved = store(KEY), line = [{ merchandiseId: variantId, quantity: qty }];
    function create() { return gql("mutation($l:[CartLineInput!]){cartCreate(input:{lines:$l}){" + CART + " userErrors{message}}}", { l: line }).then(function (d) { return d.cartCreate; }); }
    var p = saved ? gql("mutation($id:ID!,$l:[CartLineInput!]!){cartLinesAdd(cartId:$id,lines:$l){" + CART + " userErrors{message}}}", { id: saved, l: line }).then(function (d) { return d.cartLinesAdd; }).then(function (r) { return (r.cart ? r : create()); }, create) : create();
    return p.then(function (r) { if (!r.cart) throw new Error((r.userErrors[0] || {}).message || "Could not add to cart"); store(KEY, r.cart.id); bar(r.cart); return r.cart; });
  }
  var saved = store(KEY);
  if (saved) gql("query($id:ID!){cart(id:$id){id checkoutUrl totalQuantity}}", { id: saved }).then(function (d) { if (d.cart) bar(d.cart); else store(KEY, null); }, function () {});
  // shop page: sticker sheets have no page of their own, so they get a direct Add to cart button
  document.querySelectorAll(".prod[data-slug]").forEach(function (card) {
    var go = card.querySelector(".go"), u = links[card.getAttribute("data-slug")];
    if (!go || card.querySelector("h3 a") || typeof u !== "string") return;
    gql('{product(handle:"' + u.split("/products/")[1] + '"){variants(first:1){nodes{id availableForSale}}}}').then(function (d) {
      var v = d.product && d.product.variants.nodes[0]; if (!v || !v.availableForSale) return;
      go.className = "go"; go.textContent = "";
      var b = document.createElement("button"); b.type = "button"; b.className = "btn primary"; b.textContent = "Add to cart";
      b.addEventListener("click", function () { b.disabled = true; b.textContent = "Adding..."; add(v.id, 1).then(function () { b.disabled = false; b.textContent = "Added. Add another"; }, function () { b.disabled = false; b.textContent = "Try again"; }); });
      go.appendChild(b);
    }, function () {});
  });
  var host = document.querySelector(".go[data-slug]");
  if (!host) return;
  var u = links[host.getAttribute("data-slug")];
  if (!u) return;
  var handles = typeof u === "object" ? [["Night", u.night], ["Paper", u.paper]] : [["", u]];
  handles = handles.filter(function (h) { return h[1]; }).map(function (h) { return [h[0], h[1].split("/products/")[1]]; });
  var Q = "title options{name values} variants(first:100){nodes{id availableForSale price{amount currencyCode} selectedOptions{name value}}}";
  var q = "{" + handles.map(function (h, i) { return "p" + i + ':product(handle:"' + h[1] + '"){' + Q + "}"; }).join(" ") + "}";
  host.className = "go"; host.textContent = "Loading options...";
  gql(q).then(function (d) {
    var prods = handles.map(function (h, i) { return { ed: h[0], p: d["p" + i] }; }).filter(function (x) { return x.p; });
    if (!prods.length) throw new Error("not found");
    var box = document.createElement("div"); box.className = "buy"; box.style.cssText = "display:grid;gap:10px;max-width:380px";
    var sels = [], cur = prods[0].p, status = document.createElement("p"), price = document.createElement("p"), qty = document.createElement("input");
    function field(label, opts, onchange) {
      var l = document.createElement("label"), s = document.createElement("select"); l.textContent = label + " "; l.style.cssText = "display:grid;gap:4px;font-weight:600";
      s.style.cssText = "padding:8px;border-radius:8px;font:inherit"; opts.forEach(function (o) { var e = document.createElement("option"); e.value = e.textContent = o; s.appendChild(e); });
      s.addEventListener("change", onchange); l.appendChild(s); box.appendChild(l); return s;
    }
    var edSel = prods.length > 1 ? field("Edition", prods.map(function (x) { return x.ed; }), function () { cur = prods.filter(function (x) { return x.ed === edSel.value; })[0].p; build(); }) : null;
    var optBox = document.createElement("div"); optBox.style.cssText = "display:grid;gap:10px"; box.appendChild(optBox);
    function variant() {
      var want = sels.map(function (s) { return [s.getAttribute("data-n"), s.value]; });
      return cur.variants.nodes.filter(function (v) { return want.every(function (w) { return v.selectedOptions.some(function (o) { return o.name === w[0] && o.value === w[1]; }); }); })[0] || cur.variants.nodes[0];
    }
    function refresh() { var v = variant(); price.textContent = "CAD $" + Number(v.price.amount).toFixed(2); status.textContent = v.availableForSale ? "" : "Sold out"; btns.forEach(function (b) { b.disabled = !v.availableForSale; }); }
    function build() {
      optBox.innerHTML = ""; sels = [];
      cur.options.filter(function (o) { return !(o.values.length === 1 && o.values[0] === "Default Title"); }).forEach(function (o) {
        var l = document.createElement("label"), s = document.createElement("select"); l.textContent = o.name + " "; l.style.cssText = "display:grid;gap:4px;font-weight:600";
        s.style.cssText = "padding:8px;border-radius:8px;font:inherit"; s.setAttribute("data-n", o.name);
        o.values.forEach(function (x) { var e = document.createElement("option"); e.value = e.textContent = x; s.appendChild(e); });
        s.addEventListener("change", refresh); l.appendChild(s); optBox.appendChild(l); sels.push(s);
      });
      refresh();
    }
    qty.type = "number"; qty.min = 1; qty.max = 20; qty.value = 1; qty.setAttribute("aria-label", "Quantity"); qty.style.cssText = "width:80px;padding:8px;border-radius:8px;font:inherit";
    var row = document.createElement("div"); row.style.cssText = "display:flex;gap:10px;align-items:center;flex-wrap:wrap";
    var addB = document.createElement("button"), buyB = document.createElement("button"), btns = [addB, buyB];
    addB.type = buyB.type = "button"; addB.className = "btn"; buyB.className = "btn primary"; addB.textContent = "Add to cart"; buyB.textContent = "Buy now";
    function go(now) {
      var v = variant(), n = Math.max(1, Math.min(20, parseInt(qty.value, 10) || 1)); btns.forEach(function (b) { b.disabled = true; }); status.textContent = "Adding...";
      add(v.id, n).then(function (c) { if (now) location.href = c.checkoutUrl; else { status.textContent = "Added. Checkout is in the corner."; btns.forEach(function (b) { b.disabled = false; }); } },
        function (e) { status.textContent = "Sorry, that did not work (" + e.message + "). Try again."; btns.forEach(function (b) { b.disabled = false; }); });
    }
    addB.addEventListener("click", function () { go(false); }); buyB.addEventListener("click", function () { go(true); });
    row.appendChild(qty); row.appendChild(addB); row.appendChild(buyB);
    price.style.cssText = "font-weight:700;margin:0"; status.style.cssText = "margin:0;color:var(--muted)"; status.setAttribute("aria-live", "polite");
    box.appendChild(price); box.appendChild(row); box.appendChild(status);
    build(); host.textContent = ""; host.appendChild(box);
    var note = document.createElement("p"); note.className = "shop-note"; note.textContent = (/sheet-/.test(host.getAttribute("data-slug")) ? "Instant download after payment. " : "Printed to order, delivered in about 5 to 7 business days. ") + "Taxes and shipping are shown at checkout. Payment is handled securely by Shopify."; host.appendChild(note);
  }).catch(function () { host.innerHTML = 'Not available right now. <a href="shop.html">Back to the shop</a>.'; });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", twBuy); else twBuy();

// Marketing labels on the shop: ribbons, one-line captions and button wording. Honest claims only: no fake stock counts, no invented sales numbers.
function twHype() {
  var HOT = { "hoodie-build-the-pipeline": "Hot pick", "hoodie-ottawa-doesnt-pump-oil": "Crowd favourite", "toque-camp-life": "Cold-snap essential", "mug-build-the-pipeline": "Gift-ready",
              "bundle-stickers-complete-set": "Best value", "sheet-units-and-conversions": "Instant download" };
  var KIND = { hoodie: ["Fresh drop", "Heavy, warm, printed to order. Hoodie season is here."], tee: ["Fresh drop", "Soft tee, loud back print. Printed to order."], toque: ["Winter-ready", "Warm toque with an embroidered line. Printed to order."],
               hat: ["Fresh drop", "Embroidered, adjustable, one size fits most."], mug: ["Gift-ready", "The coffee mug your crew will fight over."], poster: ["Launch price while it lasts", "18 x 24 in. Real data, drawn clean."],
               bundle: ["Launch price while it lasts", "More stickers per dollar on the bigger sheets."], sheet: ["Instant download", "Pin it up today. No shipping, no waiting."] };
  function kindOf(slug) { var m = /^(hoodie|tee|toque|hat|mug|poster|bundle|sheet)/.exec(slug); return m ? m[1] : ""; }
  var st = document.createElement("style");
  st.textContent = ".pimg{position:relative;display:block}.hype{position:absolute;top:10px;left:10px;z-index:2;background:#d6304b;color:#fff;font-size:10.5px;font-weight:800;line-height:1;white-space:nowrap;letter-spacing:.03em;text-transform:uppercase;padding:5px 9px;border-radius:999px;width:max-content;max-width:calc(100% - 20px);box-shadow:0 2px 8px rgba(0,0,0,.25)}.hype.alt{background:#0f1e45}.hype.hot::before{content:'\\1F525 '}" +
    ".cap{font-size:12.5px;color:var(--muted);margin:2px 0 6px}.cap b{color:#d6304b}.proof{font-size:13px;margin:8px 0;padding:8px 10px;border-left:3px solid #d6304b;background:rgba(214,48,75,.07);border-radius:0 6px 6px 0}";
  document.head.appendChild(st);
  document.querySelectorAll(".prod[data-slug]").forEach(function (card) {
    var slug = card.getAttribute("data-slug"), k = KIND[kindOf(slug)], hot = HOT[slug];
    if (!hot) return;
    var box = card.querySelector(".pimg"); if (box && !box.querySelector(".hype")) {
      var r = document.createElement("span"); r.className = "hype" + (hot ? " hot" : " alt"); r.textContent = hot || (k && k[0]) || ""; if (r.textContent) box.appendChild(r);
    }
    var price = card.querySelector(".price"); if (price && k && !card.querySelector(".cap")) {
      var c = document.createElement("p"); c.className = "cap"; c.textContent = k[1]; price.parentNode.insertBefore(c, price);
    }
    var btn = card.querySelector(".go a.btn"); if (btn) btn.textContent = kindOf(slug) === "sheet" ? "Get it now" : hot ? "Grab yours" : "Choose options";
  });
  document.querySelectorAll("h2#best").forEach(function (h) { h.textContent = "Crew favourites"; });
  document.querySelectorAll(".go[data-slug]").forEach(function (go) {
    var slug = go.getAttribute("data-slug"), k = KIND[kindOf(slug)], hot = HOT[slug];
    if (!k || !hot || go.previousElementSibling && go.previousElementSibling.classList.contains("proof")) return;
    var d = document.createElement("p"); d.className = "proof";
    d.innerHTML = "<b>" + (hot || k[0]) + ".</b> " + k[1] + " Launch price while it lasts.";
    go.parentNode.insertBefore(d, go);
  });
}
