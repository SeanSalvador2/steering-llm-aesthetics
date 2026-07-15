"""Style-controlled Bradley-Terry tests (THEORY §T5; PLAN §III.5)."""
import math

import numpy as np
import pytest

from p19.bt_model import (Judgment, fit_bt, comparison_graph_connected, require_connected,
                          cluster_bootstrap_ci)


def _simulate(true_beta, nu=0.3, n_prompts=40, n_seeds=5, seed=0):
    rng = np.random.default_rng(seed)
    edges = [("FULL", "NEUTRAL"), ("FULL", "LOO-C5"), ("FULL", "BEAUTY1"),
             ("NEUTRAL", "LOO-C5"), ("NEUTRAL", "BEAUTY1")]
    J = []
    for pr in range(n_prompts):
        for s in range(n_seeds):
            for a, b in edges:
                mi, mj = true_beta[a], true_beta[b]
                eA, eB, et = math.exp(mi), math.exp(mj), nu * math.exp((mi + mj) / 2)
                D = eA + eB + et
                out = ["A", "B", "tie"][rng.choice(3, p=[eA / D, eB / D, et / D])]
                J.append(Judgment(a, b, f"p{pr}", out))
    return J


def test_recovers_known_strengths_and_tie():
    """MLE recovers known beta's (reference NEUTRAL=0) and the Davidson nu (THEORY T5.1-T5.3)."""
    true = {"NEUTRAL": 0.0, "FULL": 1.4, "LOO-C5": 0.7, "BEAUTY1": 0.5}
    fit = fit_bt(_simulate(true), reference="NEUTRAL")
    assert fit.converged
    assert fit.beta["NEUTRAL"] == 0.0
    for c in ("FULL", "LOO-C5", "BEAUTY1"):
        assert abs(fit.beta[c] - true[c]) < 0.35, (c, fit.beta[c])
    assert abs(fit.nu - 0.3) < 0.2


def test_style_covariate_absorbs_bias():
    """Adding a style covariate removes a pure style gap (THEORY T5.4/T5.5 omitted-variable)."""
    # A always beats B, but B always has a large 'length' style value; controlling it shrinks beta_A
    J = []
    rng = np.random.default_rng(0)
    for pr in range(40):
        for _ in range(4):
            J.append(Judgment("A", "B", f"p{pr}", "A",
                              styleA={"length": rng.normal(0, 1)},
                              styleB={"length": rng.normal(5, 1)}))
    plain = fit_bt(J, reference="B")
    styled = fit_bt(J, reference="B", style_cols=["length"])
    assert plain.beta["A"] != styled.beta["A"]  # the adjustment moves the estimate


def test_connectivity_checker():
    """Strongly-connected hub graph passes; a disconnected graph is detected (THEORY T5.3)."""
    true = {"NEUTRAL": 0.0, "FULL": 1.0, "LOO-C5": 0.5, "BEAUTY1": 0.4}
    assert comparison_graph_connected(_simulate(true))["connected"]
    disc = [Judgment("FULL", "NEUTRAL", f"p{i}", "A") for i in range(6)] + \
           [Judgment("X", "Y", f"p{i}", "A") for i in range(6)]
    assert not comparison_graph_connected(disc)["connected"]
    with pytest.raises(ValueError):
        require_connected(disc)


def test_cluster_bootstrap_ci_excludes_zero_for_real_effect():
    """A real FULL>NEUTRAL effect has a bootstrap CI excluding 0 (THEORY T3.5/T5.4)."""
    true = {"NEUTRAL": 0.0, "FULL": 1.4, "LOO-C5": 0.7, "BEAUTY1": 0.5}
    ci = cluster_bootstrap_ci(_simulate(true), [("FULL", "NEUTRAL")], B=300)
    res = ci[("FULL", "NEUTRAL")]
    assert res["lo"] > 0 and res["excludes_zero"]
