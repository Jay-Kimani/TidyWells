// Arps decline with terminal exponential switch. Mirrors src/tidywells/decline.py.
// Rate per day, time in years, nominal decline in 1/year. Illustrative only.
const DPY = 365.25;
function arpsRate(t, qi, di, b) {
  return b === 0 ? qi * Math.exp(-di * t) : qi / Math.pow(1 + b * di * t, 1 / b);
}
function forecast(qi, di, b, dMin, years, step = 1 / 12) {
  const n = Math.round(years / step), out = { t: [], rate: [], volume: [] };
  const sw = b > 0 && di > dMin ? (di / dMin - 1) / (b * di) : Infinity;
  const qSw = isFinite(sw) ? arpsRate(sw, qi, di, b) : 0;
  for (let i = 0; i < n; i++) {
    const t = i * step;
    const q = t <= sw ? arpsRate(t, qi, di, b) : qSw * Math.exp(-dMin * (t - sw));
    out.t.push(t); out.rate.push(q); out.volume.push(q * step * DPY);
  }
  return out;
}
function npv(f, price, opex, fixed, disc, step = 1 / 12) {
  let s = 0;
  for (let i = 0; i < f.t.length; i++)
    s += (f.volume[i] * (price - opex) - fixed * step) / Math.pow(1 + disc, f.t[i]);
  return s;
}
if (typeof module !== "undefined") module.exports = { arpsRate, forecast, npv };
