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


def test_fit_recovers_noiseless_hyperbolic():
    from tidywells import fit_arps
    t = np.arange(60) / 12
    q = arps_rate(t, 200, 1.2, 1.0)
    f = fit_arps(t, q)
    assert abs(f["qi"] - 200) / 200 < 0.03
    assert abs(f["di"] - 1.2) / 1.2 < 0.1
    assert abs(f["b"] - 1.0) <= 0.1


def test_fit_exponential_and_noise():
    from tidywells import fit_arps
    rng = np.random.default_rng(1)
    t = np.arange(48) / 12
    q = arps_rate(t, 100, 0.4, 0) * np.exp(rng.normal(0, 0.05, 48))
    f = fit_arps(t, q)
    assert abs(f["qi"] - 100) / 100 < 0.1 and abs(f["di"] - 0.4) < 0.1
    assert f["rmse_log"] < 0.15


def test_fit_skips_ramp_up_and_bad_points():
    from tidywells import fit_arps
    t = np.arange(40) / 12
    q = arps_rate(t, 80, 0.6, 0.5)
    q[:3] = [5, 20, 50]; q[10] = np.nan; q[11] = 0
    f = fit_arps(t, q)
    assert abs(f["qi"] - 80) / 80 < 0.15


def test_fit_warns_when_b_unconstrained_and_rejects_tiny_input():
    import pytest
    from tidywells import fit_arps
    t = np.arange(8) / 12
    f = fit_arps(t, arps_rate(t, 100, 0.5, 0))
    assert f["warnings"]
    with pytest.raises(ValueError):
        fit_arps(t[:4], arps_rate(t[:4], 100, 0.5, 0))
