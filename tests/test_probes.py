"""Probe + selectivity tests on synthetic activations (THEORY §T8.5; PLAN §IV S2.1a)."""
import numpy as np

from p19 import probes


def _synthetic(sep, n_prompts=40, seed=0):
    """FULL vs NEUTRAL with a real class separation `sep`; grouped by prompt."""
    rng = np.random.default_rng(seed)
    X, y, g = [], [], []
    axis = rng.standard_normal(32)
    axis /= np.linalg.norm(axis)
    for p in range(n_prompts):
        for label in (0, 1):
            base = rng.standard_normal(32)
            X.append(base + (sep if label else -sep) * axis)
            y.append(label)
            g.append(p)
    return np.array(X), np.array(y), np.array(g)


def test_selectivity_high_for_real_signal():
    """A real skill/neutral separation gives high AUC and high selectivity (THEORY T8.9)."""
    X, y, g = _synthetic(sep=2.0)
    res = probes.probe_layer(X, y, g)
    assert res["auc"] > 0.85
    assert res["selectivity"] > 0.3          # control task (random labels) near chance


def test_no_signal_low_auc():
    """No separation -> AUC ~ 0.5 (THEORY T8.5)."""
    X, y, g = _synthetic(sep=0.0)
    res = probes.probe_layer(X, y, g)
    assert res["auc"] < 0.65


def test_choose_band_contiguous():
    """Band = maximal contiguous layers meeting AUC/selectivity/patch thresholds (PLAN RQ5)."""
    stats = {
        10: {"auc": 0.6, "selectivity": 0.05},
        11: {"auc": 0.85, "selectivity": 0.2},
        12: {"auc": 0.9, "selectivity": 0.25},
        13: {"auc": 0.88, "selectivity": 0.2},
        14: {"auc": 0.7, "selectivity": 0.05},
    }
    patch = {11: 0.4, 12: 0.5, 13: 0.3}
    band = probes.choose_band(stats, patch)
    assert band["band"] == [11, 12, 13] and not band["diffuse"]


def test_choose_band_diffuse_fallback():
    """No layer meets all three -> single peak-AUC layer, flagged diffuse (PLAN RQ5)."""
    stats = {5: {"auc": 0.7, "selectivity": 0.05}, 6: {"auc": 0.75, "selectivity": 0.1}}
    band = probes.choose_band(stats)
    assert band["diffuse"] and band["band"] == [6]
