import numpy as np
from tidywells import arps_rate, forecast, npv


def test_exponential_matches_formula():
    assert np.isclose(arps_rate(1.0, 100, 0.5, 0), 100 * np.exp(-0.5))


def test_hyperbolic_starts_at_qi():
    assert np.isclose(arps_rate(0, 100, 0.8, 1.0), 100)


def test_forecast_switches_to_exponential_and_declines():
    f = forecast(100, 0.8, 1.2, d_min=0.06)
    assert np.all(np.diff(f["rate"]) <= 0)
    assert f["volume"].sum() > 0


def test_npv_decreases_with_discount():
    f = forecast(100, 0.5, 0.8)
    assert npv(f["volume"], f["t"], 50, discount=0.05) > npv(f["volume"], f["t"], 50, discount=0.2)
