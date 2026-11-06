// Your Well poster: builds a poster from monthly production the visitor pastes or loads. Runs entirely in the browser.
(function (root) {
  "use strict";
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MONL = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

  function splitLine(l) { return l.indexOf("\t") >= 0 ? l.split("\t") : l.split(","); }
  function parseMonth(s) {
    s = String(s).trim().replace(/^"|"$/g, "");
    var m = /^(\d{4})[-\/]?(\d{1,2})(?:[-\/]\d{1,2})?$/.exec(s);
    if (m && +m[2] >= 1 && +m[2] <= 12) return {y: +m[1], m: +m[2]};
    m = /^([A-Za-z]{3})[a-z]*\.?\s+(\d{4})$/.exec(s);
    if (m) { var i = MON.indexOf(m[1][0].toUpperCase() + m[1].slice(1, 3).toLowerCase()); if (i >= 0) return {y: +m[2], m: i + 1}; }
    return null;
  }
  // Accepts "month,volume" or the File cleaner output (month, well_id, ..., product, volume). Returns {rows, wells, products, error}.
  function parse(text, opt) {
    opt = opt || {};
    var lines = String(text).split(/\r?\n/).filter(function (l) { return l.trim(); });
    if (lines.length < 2) return {error: "Paste at least two lines: a header or first month, then more months."};
    var first = splitLine(lines[0]).map(function (c) { return c.trim().replace(/^"|"$/g, ""); });
    var hasHeader = !parseMonth(first[0]);
    var ci = {month: 0, volume: 1, well: -1, product: -1};
    if (hasHeader) {
      var low = first.map(function (c) { return c.toLowerCase(); });
      var mi = low.indexOf("month"), vi = low.indexOf("volume");
      if (mi >= 0) ci.month = mi;
      if (vi >= 0) ci.volume = vi;
      ci.well = low.indexOf("well_id");
      ci.product = low.indexOf("product");
      lines = lines.slice(1);
    }
    var wells = {}, products = {}, rows = [], bad = 0;
    lines.forEach(function (l) {
      var c = splitLine(l).map(function (x) { return x.trim().replace(/^"|"$/g, ""); });
      var mo = parseMonth(c[ci.month]), v = parseFloat(String(c[ci.volume]).replace(/,/g, ""));
      if (!mo || !isFinite(v)) { bad++; return; }
      var w = ci.well >= 0 ? c[ci.well] : "", p = ci.product >= 0 ? c[ci.product] : "";
      if (w) wells[w] = 1;
      if (p) products[p] = 1;
      rows.push({y: mo.y, m: mo.m, v: v, w: w, p: p});
    });
    if (!rows.length) return {error: "No rows could be read. Expected a month (2024-03) and a number."};
    return {rows: rows, wells: Object.keys(wells).sort(), products: Object.keys(products).sort(), bad: bad};
  }
  function daysIn(y, m) { return new Date(y, m, 0).getDate(); }
  // Sum rows per month (after filtering), optionally convert volume to a daily rate. Returns sorted [{y,m,v}].
  function series(rows, opt) {
    var acc = {};
    rows.forEach(function (r) {
      if (opt.well && r.w !== opt.well) return;
      if (opt.product && r.p !== opt.product) return;
      var k = r.y * 12 + (r.m - 1);
      acc[k] = (acc[k] || 0) + r.v;
    });
    return Object.keys(acc).map(Number).sort(function (a, b) { return a - b; }).map(function (k) {
      var y = Math.floor(k / 12), m = (k % 12) + 1, v = acc[k];
      return {y: y, m: m, v: opt.rate ? v : v / daysIn(y, m)};
    });
  }
  function niceTicks(lo, hi, n) {
    var raw = (hi - lo) / n, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
    var step = (f < 1.5 ? 1 : f < 3.5 ? 2 : f < 7.5 ? 5 : 10) * p, t = [], v = Math.floor(lo / step) * step;
    while (v <= hi + step * 0.001) { t.push(v); v += step; }
    return t;
  }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function fmt(v) { return Math.abs(v) >= 100 ? v.toLocaleString("en-CA", {maximumFractionDigits: 0}) : v.toLocaleString("en-CA", {maximumFractionDigits: 1}); }
  function lab(p) { return MON[p.m - 1] + " " + p.y; }

  var THEMES = {
    night: {bg: "#0a1020", ink: "#eef3ff", muted: "#8fa0c4", line: "#26345a", accent: "#2f9bff", accent2: "#ff6b80"},
    paper: {bg: "#f5f0e4", ink: "#15203b", muted: "#6a6f7d", line: "#d3c9b3", accent: "#0a58ca", accent2: "#c4263f"}
  };
  // Returns an SVG string (900 x 1200). s = series, o = {title, subtitle, unit, theme}
  function poster(s, o) {
    var t = THEMES[o.theme] || THEMES.night, W = 900, H = 1200;
    var title = o.title || "My Well", unit = o.unit || "units per day";
    var vals = s.map(function (p) { return p.v; }), lo0 = Math.min.apply(null, vals), hi0 = Math.max.apply(null, vals);
    var ticks = niceTicks(Math.max(0, lo0 - (hi0 - lo0) * 0.05), hi0 + (hi0 - lo0 || hi0 || 1) * 0.12, 5);
    var lo = ticks[0], hi = ticks[ticks.length - 1], x0 = 95, x1 = 825, y0 = 325, y1 = 810, n = s.length;
    var X = function (i) { return n === 1 ? (x0 + x1) / 2 : x0 + (x1 - x0) * i / (n - 1); };
    var Y = function (v) { return y1 - (y1 - y0) * (v - lo) / (hi - lo); };
    var size = Math.max(40, Math.min(84, Math.floor(740 / (0.56 * title.length))));
    var d = "", g = "";
    s.forEach(function (p, i) { d += (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(p.v).toFixed(1); });
    ticks.forEach(function (v) {
      g += '<line x1="' + x0 + '" y1="' + Y(v).toFixed(1) + '" x2="' + x1 + '" y2="' + Y(v).toFixed(1) + '" stroke="' + t.line + '" stroke-width="1"/>' +
        '<text x="' + (x0 - 10) + '" y="' + (Y(v) + 5).toFixed(1) + '" font-size="14" fill="' + t.muted + '" text-anchor="end" font-family="monospace">' + esc(fmt(v)) + '</text>';
    });
    var yrs = "", seen = {};
    s.forEach(function (p, i) { if (p.m === 1 && !seen[p.y]) { seen[p.y] = 1; yrs += '<text x="' + X(i).toFixed(1) + '" y="' + (y1 + 28) + '" font-size="15" fill="' + t.muted + '" text-anchor="middle" font-family="monospace">' + p.y + '</text>'; } });
    var pk = 0; s.forEach(function (p, i) { if (p.v > s[pk].v) pk = i; });
    var last = s[n - 1], first = s[0], chg = first.v ? (last.v / first.v - 1) * 100 : 0;
    var stat = function (x, big, a, b) {
      return '<text x="' + x + '" y="948" font-size="40" font-weight="700" fill="' + t.ink + '" font-family="Georgia,serif">' + esc(big) + '</text>' +
        '<text x="' + x + '" y="975" font-size="14" fill="' + t.muted + '" font-family="Arial,sans-serif">' + esc(a) + '</text>' +
        '<text x="' + x + '" y="994" font-size="14" fill="' + t.muted + '" font-family="Arial,sans-serif">' + esc(b) + '</text>';
    };
    var sub = o.subtitle || ("Monthly production, " + MONL[first.m - 1] + " " + first.y + " to " + MONL[last.m - 1] + " " + last.y);
    var out = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '">' +
      '<defs><linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="' + t.accent + '" stop-opacity=".35"/><stop offset="1" stop-color="' + t.accent + '" stop-opacity="0"/></linearGradient></defs>' +
      '<rect width="' + W + '" height="' + H + '" fill="' + t.bg + '"/><rect x="14" y="14" width="' + (W - 28) + '" height="' + (H - 28) + '" fill="none" stroke="' + t.line + '"/>' +
      '<text x="55" y="75" font-size="14" letter-spacing="3" font-weight="700" fill="' + t.accent + '" font-family="Arial,sans-serif">MY WELL · MADE WITH TIDYWELLS</text>' +
      '<text x="55" y="185" font-size="' + size + '" font-weight="700" fill="' + t.ink + '" font-family="Georgia,serif">' + esc(title) + '</text>' +
      '<text x="55" y="232" font-size="20" fill="' + t.muted + '" font-family="Arial,sans-serif">' + esc(sub) + '</text>' +
      '<text x="' + x0 + '" y="' + (y0 - 52) + '" font-size="13" letter-spacing="2" fill="' + t.muted + '" font-family="Arial,sans-serif">' + esc(unit.toUpperCase()) + '</text>' + g + yrs +
      '<path d="' + d + 'L' + X(n - 1).toFixed(1) + ' ' + y1 + 'L' + X(0).toFixed(1) + ' ' + y1 + 'Z" fill="url(#ar)"/>' +
      '<path d="' + d + '" fill="none" stroke="' + t.accent + '" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>' +
      (pk !== n - 1 && pk > 0 ? '<circle cx="' + X(pk).toFixed(1) + '" cy="' + Y(s[pk].v).toFixed(1) + '" r="6" fill="' + t.bg + '" stroke="' + t.accent2 + '" stroke-width="3"/><text x="' + X(pk).toFixed(1) + '" y="' + (Y(s[pk].v) - 16).toFixed(1) + '" font-size="15" font-weight="700" fill="' + t.ink + '" text-anchor="' + (pk > n * 0.8 ? "end" : pk < n * 0.2 ? "start" : "middle") + '" font-family="Arial,sans-serif">Peak ' + esc(lab(s[pk]) + ": " + fmt(s[pk].v)) + '</text>' : "") +
      '<circle cx="' + X(n - 1).toFixed(1) + '" cy="' + Y(last.v).toFixed(1) + '" r="6" fill="' + t.bg + '" stroke="' + t.accent2 + '" stroke-width="3"/>' +
      '<line x1="55" y1="905" x2="845" y2="905" stroke="' + t.line + '"/>' +
      stat(55, fmt(last.v), lab(last), unit) + stat(300, (chg >= 0 ? "+" : "−") + Math.abs(chg).toFixed(1) + "%", "since " + lab(first), "") +
      stat(560, fmt(s[pk].v), "peak month", lab(s[pk])) +
      '<text x="55" y="1110" font-size="12" fill="' + t.muted + '" font-family="Arial,sans-serif">Rate = monthly volume divided by days in the month. The vertical axis may not start at zero. Data supplied by the poster’s owner.</text>' +
      '<text x="845" y="1150" font-size="22" font-weight="700" fill="' + t.ink + '" text-anchor="end" font-family="Georgia,serif">tidywells.com</text></svg>';
    return out;
  }
  var api = {parse: parse, series: series, poster: poster, parseMonth: parseMonth, niceTicks: niceTicks};
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.WellPoster = api;
})(typeof window !== "undefined" ? window : globalThis);
