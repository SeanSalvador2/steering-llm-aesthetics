"""Power tests — reproduces THEORY §T6.2 sizing + the mis-plug guard (PLAN §III.7)."""
import warnings

import pytest

from p19 import power as pw


def test_reproduces_plan_decisive_pairs():
    """N_dec reproduces 193.8 / 84.8 / 782.5 for 60/40, 65/35, 55/45 (THEORY T6.2 table)."""
    assert pw.required_decisive_pairs(0.60) == pytest.approx(193.8, abs=0.5)
    assert pw.required_decisive_pairs(0.65) == pytest.approx(84.8, abs=0.5)
    assert pw.required_decisive_pairs(0.55) == pytest.approx(782.5, abs=1.0)


def test_misplug_value_and_guard():
    """The documented mis-plug yields ~93.26 and the two-parameter form warns for p_d<1 (THEORY T6.2)."""
    assert pw.misplug_value() == pytest.approx(93.26, abs=0.5)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        pw.required_total_pairs_two_param(0.1, 0.5)  # marginal delta, p_d<1
        assert any("mis-plug" in str(x.message) for x in w)


def test_impossible_marginal_raises():
    """|delta| > p_d is an impossible marginal and raises (guards conditional-split mis-pass)."""
    with pytest.raises(ValueError):
        pw.required_total_pairs_two_param(0.2, 0.1)


def test_reconciliation_total_times_pd_equals_decisive():
    """N_total(marginal delta) * p_d == N_decisive (the internally-consistent reading; THEORY T6.2)."""
    rec = pw.reconcile_decisive(0.60, 0.5)
    assert rec["n_total_x_pd"] == pytest.approx(rec["n_decisive_direct"], abs=0.1)
    assert rec["delta_marginal"] == pytest.approx(0.1, abs=1e-9)


def test_achieved_n_screen():
    """Post-hoc screen flags under-power when achieved < required at the observed split (THEORY T6.3)."""
    scr = pw.achieved_n_check(0.60, n_decisive=100)  # needs ~194
    assert scr["underpowered"]
    scr2 = pw.achieved_n_check(0.65, n_decisive=100)  # needs ~85
    assert not scr2["underpowered"]


def test_bt_power_simulation_runs():
    """BT simulation-based power returns a probability in [0,1] and scales with n (PLAN §III.7)."""
    lo = pw.bt_power_simulation(40, 0.60, tie_rate=0.1, n_sims=400, seed=0)["power"]
    hi = pw.bt_power_simulation(400, 0.60, tie_rate=0.1, n_sims=400, seed=0)["power"]
    assert 0.0 <= lo <= 1.0 and 0.0 <= hi <= 1.0
    assert hi > lo  # more pairs -> more power


def test_frozen_allocation_power_table():
    """The frozen allocation power table runs and carries analytic context (PREREG §6)."""
    rows = pw.frozen_allocation_power(n_sims=300)
    assert len(rows) == 4
    for r in rows:
        assert "power" in r and "required_decisive" in r and "expected_decisive" in r
