"""Patching + activations tests (THEORY §T8.6; PLAN §IV S2.0/S2.1)."""
import numpy as np

from p19 import patching, activations


def test_percent_recovered_endpoints():
    """%rec = 0 at corrupt, 100 at clean, 50 halfway (THEORY T8.6)."""
    assert patching.percent_recovered(0.0, 0.0, 1.0) == 0.0
    assert patching.percent_recovered(1.0, 0.0, 1.0) == 100.0
    assert patching.percent_recovered(0.5, 0.0, 1.0) == 50.0


def test_projection_recovery():
    """Projection-based recovery moves with the v_hat-component toward clean (S2.1c)."""
    vhat = np.array([1.0, 0.0, 0.0])
    corrupt = np.array([0.0, 1.0, 0.0])   # projection 0
    clean = np.array([2.0, 1.0, 0.0])     # projection 2
    patched = np.array([1.0, 1.0, 0.0])   # projection 1 -> 50%
    assert patching.projection_recovery(patched, corrupt, clean, vhat) == 50.0


def test_running_mean_accumulation():
    """Running mean after each example equals the prefix mean (PLAN S2.0)."""
    vecs = [np.array([0.0]), np.array([2.0]), np.array([4.0])]
    rms = activations.accumulate_running_means(vecs)
    assert [float(r) for r in rms] == [0.0, 1.0, 2.0]


def test_stability_report_plateau():
    """A stable corpus reports a plateau at the focus layers (PLAN S2.0 / F13)."""
    rng = np.random.default_rng(0)
    target = rng.standard_normal(16)
    vecs = [target + 0.001 * rng.standard_normal(16) for _ in range(200)]
    rep = activations.stability_report({13: vecs})
    assert rep[13]["plateaued"]


def test_save_load_means(tmp_path):
    """Per-layer means round-trip through the .npz shard (PLAN S2.0 storage)."""
    means = {11: np.arange(4.0), 13: np.ones(4)}
    p = tmp_path / "means.npz"
    activations.save_means(p, means)
    loaded = activations.load_means(p)
    assert set(loaded) == {11, 13} and np.allclose(loaded[11], np.arange(4.0))
