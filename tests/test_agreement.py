"""Chance-corrected agreement tests — reproduces THEORY §T4.3 (kappa paradox)."""
import pytest

from p19 import agreement as ag


def _panel(both1, both0, dis_10, dis_01):
    units = []
    units += [{"j": 1, "h": 1}] * both1
    units += [{"j": 0, "h": 0}] * both0
    units += [{"j": 1, "h": 0}] * dis_10
    units += [{"j": 0, "h": 1}] * dis_01
    return units


def test_kappa_paradox_skewed_panel():
    """Skewed panel (p_o=0.90): alpha_K ~ 0.44 depressed, AC1 ~ 0.878 stable (THEORY T4.3)."""
    sk = _panel(85, 5, 5, 5)
    assert ag.krippendorff_alpha(sk, "ordinal", [0, 1]) == pytest.approx(0.444, abs=0.01)
    assert ag.gwet_ac1(sk, [0, 1]) == pytest.approx(0.878, abs=0.01)
    assert ag.marginal_distribution(sk, [0, 1])["pi_max"] == pytest.approx(0.90, abs=1e-9)


def test_balanced_panel_coincide():
    """Balanced panel (p_o=0.90): alpha_K == AC1 == 0.80 (THEORY T4.3)."""
    ba = _panel(45, 45, 5, 5)
    assert ag.krippendorff_alpha(ba, "ordinal", [0, 1]) == pytest.approx(0.80, abs=0.01)
    assert ag.gwet_ac1(ba, [0, 1]) == pytest.approx(0.80, abs=0.01)


def test_reliability_gate_ac1_rescue_under_skew():
    """Gate passes via the AC1-under-skew rung when alpha_K is paradox-depressed (PREREG §5)."""
    sk = _panel(85, 5, 5, 5)
    gate = ag.reliability_gate(sk, [0, 1])
    assert gate["pass"] and gate["rung"] == "ac1_skew"
    assert gate["demonstrable_skew"]


def test_gate_rejects_low_agreement_when_balanced():
    """AC1 cannot rescue a genuinely low-agreement judge in the balanced case (THEORY T4.4)."""
    # p_o ~ 0.6, balanced -> both coefficients low, no demonstrable skew
    noisy = _panel(30, 30, 20, 20)
    gate = ag.reliability_gate(noisy, [0, 1])
    assert not gate["pass"]


def test_bootstrap_ci_contains_point():
    """Bootstrap CI brackets the point estimate (THEORY T4.1)."""
    sk = _panel(85, 5, 5, 5)
    ci = ag.bootstrap_ci(lambda u: ag.gwet_ac1(u, [0, 1]), sk, B=300, seed=1)
    assert ci["lo"] <= ci["point"] <= ci["hi"]
