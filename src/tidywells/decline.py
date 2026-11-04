"""Arps decline with a switch to terminal exponential decline.

Rates in volume/day, time in years, nominal decline Di in 1/year.
Illustrative only; not for reserves reporting.
"""
import numpy as np

DAYS_PER_YEAR = 365.25


def arps_rate(t, qi, di, b):
    """Rate at time t (years). b=0 exponential, 0<b<=2 hyperbolic."""
    t = np.asarray(t, dtype=float)
    if b < 0 or b > 2:
        raise ValueError("b must be between 0 and 2")
    if di <= 0 or qi <= 0:
        raise ValueError("qi and di must be positive")
    if b == 0:
        return qi * np.exp(-di * t)
    return qi / np.power(1.0 + b * di * t, 1.0 / b)


def forecast(qi, di, b, d_min=0.06, years=30, step=1 / 12):
    """Monthly forecast; switches to exponential when decline falls to d_min.

    Returns dict with t (years), rate (per day), volume (per period).
    """
    t = np.arange(0, years, step)
    if b == 0 or di <= d_min:
        rate = arps_rate(t, qi, di, 0) if b == 0 else arps_rate(t, qi, di, b)
    else:
        # instantaneous decline D(t) = di / (1 + b*di*t); switch when D = d_min
        t_sw = (di / d_min - 1.0) / (b * di)
        q_sw = arps_rate(t_sw, qi, di, b)
        rate = np.where(
            t <= t_sw,
            arps_rate(t, qi, di, b),
            q_sw * np.exp(-d_min * (t - t_sw)),
        )
    volume = rate * step * DAYS_PER_YEAR
    return {"t": t, "rate": rate, "volume": volume}


def npv(volume, t, price, opex_per_unit=0.0, fixed_cost_per_year=0.0, discount=0.10, step=1 / 12):
    """Simple discounted net revenue, no royalties or taxes."""
    volume = np.asarray(volume, dtype=float)
    t = np.asarray(t, dtype=float)
    cash = volume * (price - opex_per_unit) - fixed_cost_per_year * step
    return float(np.sum(cash / np.power(1.0 + discount, t)))


def fit_arps(t, q, from_peak=True, b_max=2.0, di_range=(0.01, 10.0)):
    """Fit q = arps_rate(t, qi, di, b) to monthly rates by least squares on log(q).

    t: years (increasing); q: rate per day. Zero, negative and NaN points are dropped.
    from_peak: ignore everything before the highest rate (ramp-up, cleanup).
    Returns dict(qi, di, b, rmse_log, n, warnings). b is searched on a bounded grid in
    [0, b_max]; hyperbolic fits are ill-conditioned, so we also report whether b is
    well determined by the data. Needs numpy only.
    """
    t = np.asarray(t, dtype=float)
    q = np.asarray(q, dtype=float)
    ok = np.isfinite(t) & np.isfinite(q) & (q > 0)
    t, q = t[ok], q[ok]
    warns = []
    if from_peak and len(q):
        i0 = int(np.argmax(q))
        t, q = t[i0:], q[i0:]
    n = len(q)
    if n < 6:
        raise ValueError(f"need at least 6 positive points after the peak, got {n}")
    if n < 12:
        warns.append("fewer than 12 points: treat the fit as rough")
    t = t - t[0]
    lq = np.log(q)

    def sse_grid(bs, dis):
        best = []
        for b in bs:
            row = []
            for di in dis:
                shape = np.log(arps_rate(t, 1.0, di, b))
                lqi = np.mean(lq - shape)
                r = lq - shape - lqi
                row.append((float(np.sum(r * r)), float(lqi)))
            best.append(row)
        return best

    bs = np.linspace(0.0, b_max, 21)
    dis = np.geomspace(di_range[0], di_range[1], 80)
    grid = sse_grid(bs, dis)
    per_b = [min(range(len(dis)), key=lambda j: grid[i][j][0]) for i in range(len(bs))]
    per_b_sse = np.array([grid[i][per_b[i]][0] for i in range(len(bs))])
    ib = int(np.argmin(per_b_sse))
    # refine di around the best cell
    jb = per_b[ib]
    lo, hi = dis[max(jb - 1, 0)], dis[min(jb + 1, len(dis) - 1)]
    fine = np.geomspace(lo, hi, 60)
    fg = sse_grid([bs[ib]], fine)[0]
    jf = min(range(len(fine)), key=lambda j: fg[j][0])
    sse, lqi = fg[jf]
    di, b, qi = float(fine[jf]), float(bs[ib]), float(np.exp(lqi))
    rmse = float(np.sqrt(sse / n))

    near = bs[per_b_sse <= per_b_sse.min() * 1.05 + 1e-12]
    if near.max() - near.min() > 0.8:
        warns.append(f"b is poorly determined (anything from {near.min():.1f} to {near.max():.1f} fits about equally well)")
    if b >= b_max - 1e-9:
        warns.append("b hit the upper bound")
    if di >= di_range[1] * 0.95:
        warns.append("decline hit the upper bound")
    if q[-1] > q[0]:
        warns.append("rate is higher at the end than at the peak: not a clean decline")
    if rmse > 0.5:
        warns.append("poor fit (erratic data, shut-ins or re-completions?)")
    return {"qi": qi, "di": di, "b": b, "rmse_log": rmse, "n": n, "warnings": warns}
