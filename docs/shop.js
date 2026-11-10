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
  // welcome code: set by subscribe.js when the visitor joins the email list; applied to the cart automatically
  function codes() { var c = null; try { c = localStorage.getItem("tw_code"); } catch (e) {} return c ? [c] : []; }
  function applyCode(id) {
    var c = codes(); if (!id || !c.length) return;
    gql("mutation($id:ID!,$d:[String!]){cartDiscountCodesUpdate(cartId:$id,discountCodes:$d){cart{id}userErrors{message}}}", { id: id, d: c }).catch(function () {});
  }
  document.addEventListener("tw-joined", function () { applyCode(store(KEY)); });
  function bar(c) {
    var el = document.getElementById("tw-cart");
    if (!c || !c.totalQuantity) { if (el) el.remove(); return; }
    if (!el) { el = document.createElement("a"); el.id = "tw-cart"; el.className = "btn primary"; el.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:50;box-shadow:0 6px 24px rgba(0,0,0,.25)"; document.body.appendChild(el); }
    el.href = c.checkoutUrl; el.textContent = "Checkout (" + c.totalQuantity + ")";
  }
  function add(variantId, qty) {
    var saved = store(KEY), line = [{ merchandiseId: variantId, quantity: qty }];
    function create() { return gql("mutation($l:[CartLineInput!],$d:[String!]){cartCreate(input:{lines:$l,discountCodes:$d}){" + CART + " userErrors{message}}}", { l: line, d: codes() }).then(function (d) { return d.cartCreate; }); }
    var p = saved ? gql("mutation($id:ID!,$l:[CartLineInput!]!){cartLinesAdd(cartId:$id,lines:$l){" + CART + " userErrors{message}}}", { id: saved, l: line }).then(function (d) { return d.cartLinesAdd; }).then(function (r) { return (r.cart ? r : create()); }, create) : create();
    return p.then(function (r) { if (!r.cart) throw new Error((r.userErrors[0] || {}).message || "Could not add to cart"); store(KEY, r.cart.id); bar(r.cart); return r.cart; });
  }
  var saved = store(KEY);
  if (saved) gql("query($id:ID!){cart(id:$id){id checkoutUrl totalQuantity}}", { id: saved }).then(function (d) { if (d.cart) { bar(d.cart); applyCode(saved); } else store(KEY, null); }, function () {});
  // shop page: sticker sheets have no page of their own, so they get a direct Add to cart button
  document.querySelectorAll(".prod[data-slug]").forEach(function (card) {
    var go = card.querySelector(".go"), u = links[card.getAttribute("data-slug")];
    if (!go || !card.hasAttribute("data-quick") || typeof u !== "string") return;
    gql('{product(handle:"' + u.split("/products/")[1] + '"){variants(first:1){nodes{id availableForSale}}}}').then(function (d) {
      var v = d.product && d.product.variants.nodes[0]; if (!v || !v.availableForSale) return;
      go.className = "go"; go.style.cssText = "display:flex;gap:8px;flex-wrap:wrap";
      var b = document.createElement("button"); b.type = "button"; b.className = "btn"; b.textContent = "Add to cart";
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
    if (/hat-patch-oval/.test(host.getAttribute("data-slug") || "")) prods.forEach(function (x) {
      x.p.options.forEach(function (o) { o.values = o.values.filter(function (v) { return !/navy/i.test(v); }); });
      x.p.variants.nodes = x.p.variants.nodes.filter(function (v) { return !v.selectedOptions.some(function (o) { return /navy/i.test(o.value); }); });
    });
    var box = document.createElement("div"); box.className = "buy";
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
    var TWC = { black: "#111111", white: "#ffffff", navy: "#1c2c52", charcoal: "#454a52", grey: "#8b8e94", gray: "#8b8e94", red: "#b3282d", green: "#2f5d3a" };
    function swatch(x) { var w = String(x).toLowerCase().split(/[\s\/]+/); for (var k = w.length - 1; k >= 0; k--) { if (TWC[w[k]]) return TWC[w[k]]; } return "#9a9a9a"; }
    function build() {
      optBox.innerHTML = ""; sels = [];
      cur.options.filter(function (o) { return !(o.values.length === 1 && o.values[0] === "Default Title"); }).forEach(function (o) {
        var isCol = /colou?r/i.test(o.name), wrap = document.createElement("div"), head = document.createElement("div"), nm = document.createElement("span"), cv = document.createElement("b"), grp = document.createElement("div"), s = document.createElement("select");
        wrap.className = "opt"; head.className = "opt-h"; nm.textContent = o.name; head.appendChild(nm); head.appendChild(cv);
        if (/size/i.test(o.name) && document.getElementById("size-guide")) { var sg = document.createElement("a"); sg.href = "#size-guide"; sg.textContent = "Size guide"; sg.addEventListener("click", function () { document.getElementById("size-guide").open = true; }); head.appendChild(sg); }
        grp.className = isCol ? "optsw" : "optgrid"; grp.setAttribute("role", "radiogroup"); grp.setAttribute("aria-label", o.name);
        s.hidden = true; s.setAttribute("data-n", o.name);
        function sync() { cv.textContent = isCol ? s.value : ""; [].forEach.call(grp.children, function (b) { b.setAttribute("aria-checked", b.getAttribute("data-v") === s.value ? "true" : "false"); }); }
        o.values.forEach(function (x) {
          var e = document.createElement("option"); e.value = e.textContent = x; s.appendChild(e);
          var b = document.createElement("button"); b.type = "button"; b.setAttribute("role", "radio"); b.setAttribute("data-v", x); b.setAttribute("aria-label", x);
          if (isCol) { b.className = "sw-c"; var d = document.createElement("i"); d.style.background = swatch(x); b.appendChild(d); } else { b.className = "sz"; b.textContent = x; }
          b.addEventListener("click", function () { s.value = x; sync(); refresh(); if (isCol && window.twGallery) window.twGallery.color(x); });
          grp.appendChild(b);
        });
        wrap.appendChild(head); wrap.appendChild(grp); wrap.appendChild(s); optBox.appendChild(wrap); sels.push(s); sync();
      });
      refresh();
    }
    qty.type = "number"; qty.min = 1; qty.max = 20; qty.value = 1; qty.setAttribute("aria-label", "Quantity"); qty.style.cssText = "width:80px;padding:8px;border-radius:8px;font:inherit";
    var row = document.createElement("div");
    var addB = document.createElement("button"), buyB = document.createElement("button"), btns = [addB, buyB];
    addB.type = buyB.type = "button"; addB.className = "pb pb-solid"; buyB.className = "pb pb-line"; addB.textContent = "Add to cart"; buyB.textContent = "Buy now";
    function go(now) {
      var v = variant(), n = Math.max(1, Math.min(20, parseInt(qty.value, 10) || 1)); btns.forEach(function (b) { b.disabled = true; }); status.textContent = "Adding...";
      add(v.id, n).then(function (c) { if (now) location.href = c.checkoutUrl; else { status.textContent = "Added. Checkout is in the corner."; btns.forEach(function (b) { b.disabled = false; }); } },
        function (e) { status.textContent = "Sorry, that did not work (" + e.message + "). Try again."; btns.forEach(function (b) { b.disabled = false; }); });
    }
    addB.addEventListener("click", function () { go(false); }); buyB.addEventListener("click", function () { go(true); });
    row.className = "buyrow"; row.appendChild(addB); row.appendChild(buyB);
    price.className = "bprice"; status.className = "bstatus"; status.setAttribute("aria-live", "polite");
    box.appendChild(price); box.appendChild(row); box.appendChild(status);
    build(); host.textContent = ""; host.appendChild(box);
    var note = document.createElement("p"); note.className = "shop-note"; note.textContent = (/sheet-/.test(host.getAttribute("data-slug")) ? "Instant download after payment. " : "Delivered in about 5 to 7 business days. ") + "Taxes and shipping are shown at checkout. Payment is handled securely by Shopify."; host.appendChild(note);
  }).catch(function () { host.innerHTML = 'Not available right now. <a href="shop.html">Back to the shop</a>.'; });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", twBuy); else twBuy();

// Marketing labels on the shop: ribbons, one-line captions and button wording. Honest claims only: no fake stock counts, no invented sales numbers.
function twHype() {
  var HOT = { "hoodie-powered-by-oil": "#1 Best seller", "hat-patch-oval": "New arrival", "hoodie-leduc-pumpjack": "Selling out fast", "toque-fire-rescue-blowout": "Winter must-have", "hoodie-support-natural-resources": "Trending now", "tee-darcys-law": "Almost gone", "hat-powered-by-oil": "Fan favourite", "hoodie-drilling-gear": "Just dropped", "toque-powered-by-oil": "Going fast", "hoodie-hyperbolic-decline": "Crowd pick" };
  var KIND = { hoodie: ["Fresh drop", "Heavy and warm. Hoodie season is here."], tee: ["Fresh drop", "Soft tee, loud back print."], toque: ["Winter-ready", "Warm toque with an embroidered line."],
               hat: ["Fresh drop", "Embroidered, adjustable, one size fits most."], mug: ["Gift-ready", "The coffee mug your crew will fight over."], poster: ["Wall-ready", "18 x 24 in. Real data, drawn clean."],
               bundle: ["Better value", "More stickers per dollar on the bigger sheets."], sheet: ["Instant download", "Pin it up today. No shipping, no waiting."] };
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
    var btn = card.querySelector(".go a.btn"); if (btn) btn.textContent = kindOf(slug) === "sheet" ? "Get it now" : "Choose options";
  });
}

// Product gallery: arrows, thumbnail strip, colour buttons and a caption.
(function () {
  "use strict";
  var COL = { black: "#15171c", charcoal: "#454a52", navy: "#1c2c52", white: "#ffffff" };
  function build(v) {
    var btns = [].slice.call(v.querySelectorAll(".sw button")), imgs = [].slice.call(v.querySelectorAll("img[data-pi]"));
    if (btns.length < 2 || !imgs.length) return;
    var stage = document.createElement("div"); stage.className = "stage";
    imgs[0].parentNode.insertBefore(stage, imgs[0]);
    imgs.forEach(function (x) { stage.appendChild(x); });
    var cap = document.createElement("p"); cap.className = "vcap"; cap.setAttribute("aria-live", "polite");
    var strip = document.createElement("div"); strip.className = "thumbs"; strip.setAttribute("role", "group"); strip.setAttribute("aria-label", "Product views");
    var dots = document.createElement("div"); dots.className = "cols";
    var ths = [], cur = 0, colOf = [], last = "", seen = {};
    function pick(i) {
      cur = (i + btns.length) % btns.length; i = cur;
      btns[i].click();
      ths.forEach(function (t, j) { t.setAttribute("aria-pressed", j === i ? "true" : "false"); });
      [].forEach.call(dots.querySelectorAll("button"), function (d) { d.setAttribute("aria-pressed", d.getAttribute("data-c") === colOf[i] ? "true" : "false"); });
      cap.textContent = btns[i].textContent.trim() + "  (" + (i + 1) + " of " + btns.length + ")"; cnt.textContent = (i + 1) + " / " + btns.length;
      try { strip.scrollTo({ left: ths[i].offsetLeft - 8, top: ths[i].offsetTop - 8, behavior: "smooth" }); } catch (e) {}
    }
    function arrow(dir) {
      var a = document.createElement("button"); a.type = "button"; a.className = "arr " + (dir < 0 ? "prev" : "next");
      a.setAttribute("aria-label", dir < 0 ? "Previous image" : "Next image"); a.innerHTML = "<span aria-hidden=\"true\">" + (dir < 0 ? "&#8249;" : "&#8250;") + "</span>";
      a.addEventListener("click", function () { pick(cur + dir); }); stage.appendChild(a);
    }
    var cnt = document.createElement("span"); cnt.className = "cnt"; stage.appendChild(cnt);
    arrow(-1); arrow(1);
    v.setAttribute("tabindex", "0");
    v.addEventListener("keydown", function (e) { if (e.key === "ArrowLeft") { pick(cur - 1); e.preventDefault(); } else if (e.key === "ArrowRight") { pick(cur + 1); e.preventDefault(); } });
    var tx = null;
    stage.addEventListener("touchstart", function (e) { tx = e.touches[0].clientX; }, { passive: true });
    stage.addEventListener("touchend", function (e) { if (tx === null) return; var dx = e.changedTouches[0].clientX - tx; tx = null; if (Math.abs(dx) > 40) pick(cur + (dx < 0 ? 1 : -1)); });
    btns.forEach(function (b, i) {
      var cm = /(black|charcoal|navy|white)/i.exec(b.textContent); if (cm) last = cm[1].toLowerCase(); colOf.push(last);
      var t = document.createElement("button"), im = new Image(); t.type = "button"; t.className = "th"; t.setAttribute("aria-label", b.textContent.trim());
      var src = imgs.filter(function (x) { return x.getAttribute("data-pi") === b.getAttribute("data-pi"); })[0]; im.src = src ? src.getAttribute("src") : ""; im.alt = ""; im.loading = "lazy"; im.width = 72; im.height = 90;
      t.appendChild(im); t.addEventListener("click", function () { pick(i); }); strip.appendChild(t); ths.push(t);
      if (cm && !seen[last]) {
        seen[last] = 1; var d = document.createElement("button"), c = last; d.type = "button"; d.setAttribute("data-i", i); d.setAttribute("data-c", c); d.className = "colbtn";
        d.innerHTML = '<i style="background:' + COL[c] + '"></i>' + c.charAt(0).toUpperCase() + c.slice(1);
        d.addEventListener("click", function () { pick(i); }); dots.appendChild(d);
      }
    });
    v.querySelector(".sw").style.display = "none";
    v.appendChild(strip);
    window.twGallery = { pick: pick, color: function (name) { var w = /(black|charcoal|navy|white)/i.exec(name || ""); if (!w) return; var c = w[1].toLowerCase(); for (var k = 0; k < colOf.length; k++) { if (colOf[k] === c) { pick(k); return; } } } };
    v.appendChild(cap); pick(0);
  }
  function run() { document.querySelectorAll(".pview").forEach(build); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();;
