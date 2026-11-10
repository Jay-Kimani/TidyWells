// Email list with a 5% welcome code. Shows a slim offer bar on every page, the footer signup panel, and a note on product pages.
// The code is public: anyone can use it. It is applied to the cart automatically by shop.js when visitors have joined on this device.
(function () {
  var CODE = "WELCOME5", KEY = "tw_code";
  var action = window.TIDYWELLS_NEWSLETTER_ACTION || "";
  var feed = document.querySelector('link[rel=alternate][type="application/rss+xml"]');
  var rss = feed ? feed.href : "/feed.xml";
  function ls(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} return null; }
  function ss(k, v) { try { if (v === undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k, v); } catch (e) {} return null; }

  var st = document.createElement("style");
  st.textContent = ".tw-offer{display:flex;gap:10px 14px;flex-wrap:wrap;align-items:center;justify-content:center;padding:9px 40px 9px 16px;background:var(--navy,#0a1a30);color:#fff;font-size:14px;line-height:1.35;position:relative;text-align:center}" +
    ".tw-offer b{color:#ffb070}.tw-offer form{display:flex;gap:6px;flex-wrap:nowrap;justify-content:center}@media(max-width:620px){.tw-offer form{display:none}.tw-offer{padding:8px 38px 8px 14px;font-size:13px;justify-content:flex-start;text-align:left}}.tw-offer input[type=email]{min-width:200px;padding:6px 10px;border-radius:6px;border:1px solid rgba(255,255,255,.35);background:#fff;color:#111;font:inherit}" +
    ".tw-offer button.go{padding:6px 14px;border:0;border-radius:6px;background:#ff963c;color:#1a1000;font:inherit;font-weight:700;cursor:pointer}" +
    ".tw-offer .x{position:absolute;right:8px;top:6px;background:none;border:0;color:#fff;font-size:20px;line-height:1;cursor:pointer;opacity:.7}" +
    ".tw-offer code,.tw-ok code{background:rgba(255,255,255,.16);padding:2px 8px;border-radius:5px;font-weight:700;letter-spacing:.04em}.tw-ok code{background:var(--chip,#eee);color:inherit}" +
    ".tw-offer-note{margin:6px 0;font-size:13.5px;color:var(--muted)}.tw-offer-note b{color:var(--fg)}";
  document.head.appendChild(st);

  function joined() { return ls(KEY) === CODE; }
  function done(email) { ls(KEY, CODE); document.dispatchEvent(new CustomEvent("tw-joined")); }
  function join(email) {
    if (!action) return Promise.reject(new Error("no list"));
    var body = new URLSearchParams(); body.set("email", email); body.set("embed", "1"); body.set("tag", "welcome-5-percent");
    return fetch(action, { method: "POST", mode: "no-cors", body: body });
  }
  function okHtml() {
    return 'You are in. Your code is <code>' + CODE + '</code>: 5% off your first order, applied at checkout on tidywells.com. Check your inbox to confirm your subscription.';
  }
  function wire(form, msg, after) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var inp = form.querySelector("input[type=email]"), btn = form.querySelector("button[type=submit]");
      if (!inp.value || !inp.checkValidity()) { inp.reportValidity(); return; }
      btn.disabled = true;
      join(inp.value).then(function () { done(); msg.innerHTML = okHtml(); form.hidden = true; form.style.display = "none"; if (after) after(); },
        function () { btn.disabled = false; msg.textContent = "Could not sign you up just now. Please try again in a minute."; });
    });
  }
  function formHtml(label) {
    return '<form><input type="email" name="email" required placeholder="you@example.com" aria-label="Email address"><button type="submit" class="go">' + label + '</button></form>';
  }

  // 1. offer bar on every page
  if (action && !ss("tw_bar_closed")) {
    var bar = document.createElement("div"); bar.className = "tw-offer"; bar.setAttribute("role", "region"); bar.setAttribute("aria-label", "Welcome offer");
    var msg = document.createElement("span");
    if (joined()) {
      msg.innerHTML = 'Your welcome code: <code>' + CODE + '</code> for 5% off your first order, applied at checkout.';
      bar.appendChild(msg);
    } else {
      msg.innerHTML = '<b>5% off your first order.</b> Join the email list and get the code.';
      bar.appendChild(msg);
      var holder = document.createElement("span"); holder.innerHTML = formHtml("Get my code"); bar.appendChild(holder);
      wire(holder.firstChild, msg);
    }
    var x = document.createElement("button"); x.className = "x"; x.type = "button"; x.setAttribute("aria-label", "Close"); x.textContent = "×";
    x.addEventListener("click", function () { bar.remove(); ss("tw_bar_closed", "1"); }); bar.appendChild(x);
    document.body.insertBefore(bar, document.body.firstChild);
  }

  // 2. note under the price on product pages
  if (document.querySelector(".pview")) {
    var pr = document.querySelector(".price");
    if (pr && !document.querySelector(".tw-offer-note")) {
      var n = document.createElement("p"); n.className = "tw-offer-note";
      var show = function () { n.innerHTML = joined() ? 'Your code <b>' + CODE + '</b> takes 5% off your first order at checkout.' : '<b>5% off your first order</b> when you <a href="#subscribe">join the email list</a>.'; };
      show(); document.addEventListener("tw-joined", show);
      (pr.closest("p") || pr).insertAdjacentElement("afterend", n);
    }
  }

  // 3. footer panel
  var box = document.getElementById("subscribe"); if (!box) return;
  var html = '<div class="panel" style="margin:16px 0"><b>Join the list: 5% off your first order</b>' +
    '<p style="margin:4px 0;font-size:14px;color:var(--muted)">New analysis about every two weeks, plus the occasional shop note. ';
  if (action) {
    html += 'Or use <a href="' + rss + '">RSS</a>.</p><div class="tw-ok" style="font-size:14px"></div>' +
      '<form style="display:flex;gap:8px;flex-wrap:wrap"><input type="email" name="email" required placeholder="you@example.com" aria-label="Email address" style="flex:1;min-width:200px"><button type="submit">Get my 5% code</button></form>' +
      '<p style="margin:6px 0 0;font-size:12px;color:var(--muted)">By subscribing you agree to receive emails about new Tidywells posts and shop offers. Unsubscribe any time with the link in every email.</p>';
  } else {
    html += 'Follow by <a href="' + rss + '">RSS</a> (email signup coming soon).</p>';
  }
  html += '<p style="margin:8px 0 0;font-size:14px">Prefer your inbox? <a href="https://tidywells.substack.com/" target="_blank" rel="noopener"><b>Subscribe on Substack</b></a>.</p>';
  box.innerHTML = html + '</div>';
  var f = box.querySelector("form"), m = box.querySelector(".tw-ok");
  if (f) {
    if (joined()) { m.innerHTML = 'Your code: <code>' + CODE + '</code>, 5% off your first order.'; f.hidden = true; f.style.display = "none"; }
    else wire(f, m);
  }
})();
