"""Per-layer linear probes + control-task selectivity (THEORY §T8.5; PLAN §IV S2.1a).

Logistic probes on mean-response residuals classify FULL vs NEUTRAL, per layer, with 5-fold CV
SPLIT BY PROMPT (never leak a prompt across folds). Selectivity (THEORY T8.9) subtracts the AUC
on a control task (random-but-fixed label per prompt) so a probe that merely memorizes prompt
identity is caught. This module is pure CPU (numpy + scikit-learn) and runs now on synthetic
activations; on Colab it consumes the real per-layer means.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold


def _cv_auc(X: np.ndarray, y: np.ndarray, groups: np.ndarray, n_splits: int = 5,
            seed: int = 0) -> float:
    """Cross-validated AUC with GroupKFold on `groups` (prompt ids); pooled out-of-fold scores."""
    n_splits = min(n_splits, len(np.unique(groups)))
    if n_splits < 2:
        return float("nan")
    gkf = GroupKFold(n_splits=n_splits)
    oof = np.full(len(y), np.nan)
    for tr, te in gkf.split(X, y, groups):
        if len(np.unique(y[tr])) < 2:
            continue
        clf = LogisticRegression(max_iter=2000, C=1.0)
        clf.fit(X[tr], y[tr])
        oof[te] = clf.predict_proba(X[te])[:, 1]
    mask = ~np.isnan(oof)
    if len(np.unique(y[mask])) < 2:
        return float("nan")
    return float(roc_auc_score(y[mask], oof[mask]))


def probe_layer(X: np.ndarray, y: np.ndarray, groups: np.ndarray, seed: int = 0) -> dict:
    """Real AUC, control AUC, and selectivity for one layer (THEORY T8.9).

    Control task: a random-but-fixed label per prompt group (preserves structure, destroys the
    skill/neutral signal). selectivity = AUC_real - AUC_control.
    """
    auc_real = _cv_auc(X, y, groups, seed=seed)
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    ctrl_by_group = {g: int(rng.integers(0, 2)) for g in uniq}
    y_ctrl = np.array([ctrl_by_group[g] for g in groups])
    auc_ctrl = _cv_auc(X, y_ctrl, groups, seed=seed)
    sel = auc_real - auc_ctrl if (auc_real == auc_real and auc_ctrl == auc_ctrl) else float("nan")
    return {"auc": auc_real, "auc_control": auc_ctrl, "selectivity": sel}


def probe_all_layers(means_by_layer: dict[int, np.ndarray], labels: np.ndarray,
                     groups: np.ndarray, seed: int = 0) -> dict[int, dict]:
    """Probe every layer. means_by_layer[l] = [n_examples, d] mean-response residuals."""
    return {l: probe_layer(np.asarray(X), np.asarray(labels), np.asarray(groups), seed)
            for l, X in means_by_layer.items()}


def probe_weight_direction(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """The fitted linear-probe weight direction (for cos vs diff-in-means; PLAN S2.2)."""
    clf = LogisticRegression(max_iter=2000, C=1.0).fit(X, y)
    w = clf.coef_[0]
    n = np.linalg.norm(w)
    return w / n if n > 0 else w


def choose_band(layer_stats: dict[int, dict], patch_recovered: dict[int, float] | None = None,
                auc_min: float = 0.80, sel_min: float = 0.15, patch_min: float = 0.25) -> dict:
    """RQ5 band = maximal contiguous layers with AUC>=.80 & selectivity>=.15 & patch>=25% (PLAN RQ5).

    If no contiguous band meets all three, returns the single peak-AUC layer flagged 'diffuse'.
    """
    layers = sorted(layer_stats)

    def ok(l):
        s = layer_stats[l]
        cond = s["auc"] >= auc_min and s["selectivity"] >= sel_min
        if patch_recovered is not None:
            cond = cond and patch_recovered.get(l, 0.0) >= patch_min
        return cond

    best_run: list[int] = []
    cur: list[int] = []
    for l in layers:
        if ok(l):
            cur.append(l)
            if len(cur) > len(best_run):
                best_run = list(cur)
        else:
            cur = []
    if best_run:
        return {"band": best_run, "diffuse": False}
    peak = max(layers, key=lambda l: layer_stats[l]["auc"])
    return {"band": [peak], "diffuse": True}
