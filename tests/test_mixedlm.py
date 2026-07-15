"""Factorial design-matrix + MixedLM tests (THEORY §T1-T3; PLAN §III.2/§III.6)."""
import numpy as np
import pandas as pd

from p19 import mixedlm as ml


def test_design_matrix_rank_and_orthogonality():
    """16x16 model matrix is full rank and orthogonal (X^T X = 16 I) (THEORY T1.3)."""
    X, names, ids = ml.factorial_design_matrix()
    assert X.shape == (16, 16)
    assert np.linalg.matrix_rank(X) == 16
    assert np.allclose(X.T @ X, 16 * np.eye(16))
    assert len(names) == 16 and names[0] == "intercept"


def test_E_equals_ABCD_parity():
    """Every in-fraction row has product of signs = +1 and E == ABCD (THEORY T1.2/T1.3)."""
    signs = np.array([c["sign"] for c in ml.factorial_cells()], float)
    assert np.allclose(signs.prod(axis=1), 1.0)             # I = ABCDE
    assert np.allclose(signs[:, 4], signs[:, :4].prod(axis=1))  # E = ABCD (collinearity guard)


def test_alias_structure_matches_theory():
    """Alias cosets via I=ABCDE: A<->BCDE, AB<->CDE, DE<->ABC (THEORY T2.2)."""
    al = ml.alias_structure()
    assert al["A"] == "BCDE" and al["AB"] == "CDE" and al["DE"] == "ABC"
    assert al["E"] == "ABCD"


def _sim_factorial(true_beta, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for c in ml.factorial_cells():
        sign = dict(zip(ml.FACTORS, c["sign"]))
        mu = 1.0 + sum(true_beta[f] * sign[f] for f in ml.FACTORS)
        for pr in range(40):
            u = rng.normal(0, 0.3)
            for s in range(3):
                row = {"cell_id": c["id"], "prompt_id": f"p{pr}", "seed": s,
                       "y": mu + u + rng.normal(0, 0.4)}
                row.update({f: sign[f] for f in ml.FACTORS})
                rows.append(row)
    return pd.DataFrame(rows)


def test_ols_effects_recover_truth():
    """Closed-form orthogonal effects (2*beta) recover the simulated truth (THEORY T1.5)."""
    true = {"C1": 0.5, "C2": 0.3, "C3": 0.1, "C4": 0.05, "C5": 0.6}
    eff = ml.estimate_effects_ols(_sim_factorial(true), "y")
    for f in ml.FACTORS:
        assert abs(eff[f] - 2 * true[f]) < 0.15, (f, eff[f])


def test_factorial_fit_recovers_and_records_rung():
    """Factorial fit recovers main effects and records the ladder rung used (THEORY T3.6)."""
    true = {"C1": 0.5, "C2": 0.3, "C3": 0.1, "C4": 0.05, "C5": 0.6}
    res = ml.fit_factorial(_sim_factorial(true), "y")
    assert res["rung"]  # a rung was recorded (mixedlm_* or ols_cluster_robust)
    for f in ml.FACTORS:
        assert abs(res["coefs"][f]["est"] - true[f]) < 0.1, (f, res["coefs"][f])
    assert res["coefs"]["C5"]["p"] < 0.001  # the large C5 effect is significant


def test_paired_contrast_recovers_gap():
    """FULL vs AOI-C5 paired contrast recovers the mean gap with a CI (THEORY T1.4/T3.3)."""
    true = {"C1": 0.5, "C2": 0.3, "C3": 0.1, "C4": 0.05, "C5": 0.6}
    df = _sim_factorial(true)
    pc = ml.paired_contrast(df, "FULL", "AOI-C5", "y")
    # FULL mu = 1+sum(all +) ; AOI-C5 mu = 1 - C1-C2-C3-C4 + C5 ; gap = 2*(C1+C2+C3+C4)
    expected = 2 * (0.5 + 0.3 + 0.1 + 0.05)
    assert abs(pc.estimate - expected) < 0.2
    assert pc.rung
