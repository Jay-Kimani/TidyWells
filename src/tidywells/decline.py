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
