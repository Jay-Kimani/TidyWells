// Arps decline with terminal exponential switch. Mirrors src/tidywells/decline.py.
// Rate per day, time in years, nominal decline in 1/year. Illustrative only.
const DPY = 365.25;
function arpsRate(t, qi, di, b) {
  return b === 0 ? qi * Math.exp(-di * t) : qi / Math.pow(1 + b * di * t, 1 / b);
}
function forecast(qi, di, b, dMin, years, step = 1 / 12, t0 = 0) {
  const n = Math.round(years / step), out = { t: [], rate: [], volume: [] };
  const sw = b > 0 && di > dMin ? (di / dMin - 1) / (b * di) : Infinity;
  const qSw = isFinite(sw) ? arpsRate(sw, qi, di, b) : 0;
  for (let i = 0; i < n; i++) {
    const t = t0 + i * step;
    const q = t <= sw ? arpsRate(t, qi, di, b) : qSw * Math.exp(-dMin * (t - sw));
    out.t.push(i * step); out.rate.push(q); out.volume.push(q * step * DPY);
  }
  return out;
}
function npv(f, price, opex, fixed, disc, step = 1 / 12) {
  let s = 0;
  for (let i = 0; i < f.t.length; i++)
    s += (f.volume[i] * (price - opex) - fixed * step) / Math.pow(1 + disc, f.t[i]);
  return s;
}


// ---- Fit (mirrors fit_arps in src/tidywells/decline.py) ----
function linspace(a, b, n) { return Array.from({ length: n }, (_, i) => a + (b - a) * i / (n - 1)); }
function geomspace(a, b, n) {
  const la = Math.log(a), lb = Math.log(b);
  return Array.from({ length: n }, (_, i) => Math.exp(la + (lb - la) * i / (n - 1)));
}
function fitArps(t, q, opts = {}) {
  const fromPeak = opts.fromPeak !== false, bMax = opts.bMax ?? 2, diRange = opts.diRange || [0.01, 10];
  let idx = [];
  for (let i = 0; i < q.length; i++) if (isFinite(t[i]) && isFinite(q[i]) && q[i] > 0) idx.push(i);
  const warns = [];
  if (fromPeak && idx.length) {
    let best = 0;
    for (let k = 1; k < idx.length; k++) if (q[idx[k]] > q[idx[best]]) best = k;
    idx = idx.slice(best);
  }
  const n = idx.length;
  if (n < 6) throw new Error(`need at least 6 positive points after the peak, got ${n}`);
  if (n < 12) warns.push("fewer than 12 points: treat the fit as rough");
  const t0 = t[idx[0]];
  const tt = idx.map(i => t[i] - t0), lq = idx.map(i => Math.log(q[i]));
  function cell(b, di) {
    let m = 0;
    const sh = tt.map(x => Math.log(arpsRate(x, 1, di, b)));
    for (let i = 0; i < n; i++) m += lq[i] - sh[i];
    m /= n;
    let s = 0;
    for (let i = 0; i < n; i++) { const r = lq[i] - sh[i] - m; s += r * r; }
    return [s, m];
  }
  const bs = linspace(0, bMax, 21), dis = geomspace(diRange[0], diRange[1], 80);
  const perB = [], perBsse = [];
  for (const b of bs) {
    let bj = 0, bs_ = Infinity;
    dis.forEach((di, j) => { const s = cell(b, di)[0]; if (s < bs_) { bs_ = s; bj = j; } });
    perB.push(bj); perBsse.push(bs_);
  }
  let ib = 0;
  perBsse.forEach((s, i) => { if (s < perBsse[ib]) ib = i; });
  const jb = perB[ib];
  const fine = geomspace(dis[Math.max(jb - 1, 0)], dis[Math.min(jb + 1, dis.length - 1)], 60);
  let bestF = 0, sse = Infinity, lqi = 0;
  fine.forEach((di, j) => { const [s, m] = cell(bs[ib], di); if (s < sse) { sse = s; lqi = m; bestF = j; } });
  const di = fine[bestF], b = bs[ib], qi = Math.exp(lqi), rmse = Math.sqrt(sse / n);
  const minS = Math.min(...perBsse), near = bs.filter((_, i) => perBsse[i] <= minS * 1.05 + 1e-12);
  const spread = Math.max(...near) - Math.min(...near);
  if (spread > 0.8) warns.push(`b is poorly determined (anything from ${Math.min(...near).toFixed(1)} to ${Math.max(...near).toFixed(1)} fits about equally well)`);
  if (b >= bMax - 1e-9) warns.push("b hit the upper bound");
  if (di >= diRange[1] * 0.95) warns.push("decline hit the upper bound");
  if (q[idx[idx.length - 1]] > q[idx[0]]) warns.push("rate is higher at the end than at the peak: not a clean decline");
  if (rmse > 0.5) warns.push("poor fit (erratic data, shut-ins or re-completions?)");
  return { qi, di, b, rmseLog: rmse, n, warnings: warns, peakIndex: idx[0], usedIndex: idx };
}

// ---- CSV / paste parsing ----
function splitLine(line, d) {
  const out = []; let cur = "", q = false;
  for (const ch of line) {
    if (ch === '"') q = !q; else if (ch === d && !q) { out.push(cur.trim()); cur = ""; } else cur += ch;
  }
  out.push(cur.trim()); return out;
}
function parseTable(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  if (!lines.length) return { headers: [], rows: [] };
  const first = lines[0];
  const d = [",", "\t", ";"].map(c => [c, first.split(c).length]).sort((a, b) => b[1] - a[1])[0][0];
  let rows = lines.map(l => splitLine(l, d));
  const isNum = s => s !== "" && isFinite(Number(String(s).replace(/,/g, "")));
  const hasHeader = rows[0].some(c => !isNum(c) && !parseMonth(c));
  const headers = hasHeader ? rows.shift() : rows[0].map((_, i) => "column " + (i + 1));
  return { headers, rows };
}
function parseMonth(s) {
  s = String(s).trim();
  let m;
  if ((m = s.match(/^(\d{4})[-\/](\d{1,2})(?:[-\/]\d{1,2})?$/))) return { y: +m[1], m: +m[2] };
  if ((m = s.match(/^(\d{4})(\d{2})$/)) && +m[2] >= 1 && +m[2] <= 12) return { y: +m[1], m: +m[2] };
  const names = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
  if ((m = s.match(/^([A-Za-z]{3})[a-z]*[ -]+(\d{4})$/)) && names.includes(m[1].toLowerCase())) return { y: +m[2], m: names.indexOf(m[1].toLowerCase()) + 1 };
  return null;
}
function daysInMonth(y, m) { return new Date(y, m, 0).getDate(); }

if (typeof module !== "undefined") module.exports = { arpsRate, forecast, npv, fitArps, parseTable, parseMonth };
