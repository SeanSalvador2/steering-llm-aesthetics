"""Steering tests: direction math (CPU) + KL guardrail (tiny model) (THEORY §T8; PLAN §IV)."""
import numpy as np
import pytest

from p19 import steering as st


def test_diff_in_means_and_unit():
    """v_l = mean_FULL - mean_NEUTRAL; v_hat is unit-norm (THEORY T8.2)."""
    v = st.diff_in_means(np.array([2.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.0]))
    assert np.allclose(v, [2, 0, 0])
    assert abs(np.linalg.norm(st.unit(v)) - 1.0) < 1e-9


def test_pca_direction_aligns_with_mean_shift():
    """PC1 of paired diffs aligns with the mean difference (LAT cross-check; PLAN S2.2)."""
    rng = np.random.default_rng(0)
    axis = np.array([1.0, 0.0, 0.0])
    diffs = axis + 0.05 * rng.standard_normal((200, 3))
    pc1 = st.pca_direction(diffs)
    assert st.cosine(pc1, axis) > 0.99


def test_cosine_agreement_high_when_isotropic():
    """diff-in-means and PCA-PC1 agree when noise is isotropic (THEORY T8.2 / PLAN S2.2)."""
    rng = np.random.default_rng(1)
    diffs = np.array([1.0, 0, 0]) + 0.05 * rng.standard_normal((300, 3))
    v = diffs.mean(0)
    agr = st.direction_agreement(v, diffs)
    assert agr["cos_diff_pca"] > 0.99


def test_running_mean_cosine_plateau():
    """A stabilizing running mean reaches the cosine plateau; a drifting one does not (PLAN S2.0)."""
    rng = np.random.default_rng(0)
    target = rng.standard_normal(16)
    vecs = [target + 0.001 * rng.standard_normal(16) for _ in range(200)]
    rms = [np.mean(vecs[: i + 1], axis=0) for i in range(len(vecs))]
    assert st.running_mean_cosine_stability(rms)["plateaued"]
    # a sharp late regime change (last 10% points on an orthogonal, large axis) does NOT plateau:
    # the running-mean DIRECTION is still rotating in the tail window.
    A = np.zeros(16); A[0] = 1.0
    B = np.zeros(16); B[1] = 1.0
    drift = [A + 0.001 * rng.standard_normal(16) for _ in range(180)] + [50.0 * B for _ in range(20)]
    rms2 = [np.mean(drift[: i + 1], axis=0) for i in range(len(drift))]
    assert not st.running_mean_cosine_stability(rms2)["plateaued"]


def test_select_operating_point_respects_guardrails():
    """Freeze = argmax POC-gain s.t. KL<=0.30 and render>=0.90; ties broken by lower KL (PREREG §7)."""
    rows = [
        {"layer": 13, "rho": 0.2, "variant": "mean_response", "poc_gain": 0.5, "mean_kl": 0.2, "render_success": 0.95},
        {"layer": 15, "rho": 0.5, "variant": "mean_response", "poc_gain": 0.9, "mean_kl": 0.5, "render_success": 0.95},  # KL too high
        {"layer": 17, "rho": 0.3, "variant": "mean_response", "poc_gain": 0.5, "mean_kl": 0.1, "render_success": 0.95},  # tie -> lower KL
    ]
    best = st.select_operating_point(rows)
    assert best["layer"] == 17  # tie on poc_gain 0.5, lower KL wins
    # nothing feasible -> {}
    assert st.select_operating_point([
        {"layer": 1, "rho": 1.0, "variant": "x", "poc_gain": 1.0, "mean_kl": 0.9, "render_success": 0.5}]) == {}


def test_reproduction_and_attenuation():
    """%-reproduced and attenuation% formulas (PLAN S2.4/S2.5)."""
    assert st.reproduction_fraction(0.5, 0.0, 1.0) == 50.0
    assert st.attenuation_pct(1.0, 0.4, 0.0) == 60.0


def test_norm_matched_random_controls():
    """k=5 random directions match ||v_ref|| (specificity control; PLAN S2.4)."""
    v = np.array([3.0, 4.0, 0.0])  # norm 5
    rs = st.norm_matched_random(v, k=5, seed=0)
    assert len(rs) == 5
    for r in rs:
        assert abs(np.linalg.norm(r) - 5.0) < 1e-9


def test_kl_guardrail_on_tiny_model(tiny_qwen2):
    """Mean per-token KL is ~0 at alpha=0 and grows with alpha (THEORY T8.6)."""
    torch = pytest.importorskip("torch")
    ids = torch.randint(0, 200, (1, 12))
    v = np.random.default_rng(0).standard_normal(64)
    kl0 = st.mean_token_kl(tiny_qwen2, ids, layer=1, vhat=v, alpha=0.0)
    kl_big = st.mean_token_kl(tiny_qwen2, ids, layer=1, vhat=v, alpha=8.0)
    assert kl0 == pytest.approx(0.0, abs=1e-5)
    assert kl_big > kl0
