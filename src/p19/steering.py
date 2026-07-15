"""Direction extraction + steering (THEORY §T8; PLAN §IV S2.2-S2.5).

Direction math (diff-in-means, PCA/LAT, unit-norm, cosine) is pure-numpy and CPU-tested on
synthetic activations. The KL guardrail and steered generation drive the HF model through
src/p19/hooks.py; they are import-guarded and exercised on the tiny Qwen2 stand-in.

  diff_in_means  v_l = mean_h_FULL - mean_h_NEUTRAL ; v_hat = v/||v||   (THEORY T8.2)
  pca_direction  PC1 of paired differences (LAT / RepE cross-check)      (PLAN S2.2)
  mean_token_kl  coherence guardrail on a fixed 512-token eval text      (THEORY T8.6)
  sweep grid     S2.3 (rho x layer x variant) with guardrails -> freeze   (PLAN S2.3)
  S2.4 arms      unsteered / steered / norm-matched-random(k=5) / FULL-ref (PLAN S2.4)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .config import steering_grids_config, steering_frozen_config


# --------------------------------------------------------------------------- direction math (CPU)

def diff_in_means(full_mean: np.ndarray, neutral_mean: np.ndarray) -> np.ndarray:
    """v_l = mean_h^FULL - mean_h^NEUTRAL (THEORY T8.2)."""
    return np.asarray(full_mean, float) - np.asarray(neutral_mean, float)


def unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def pca_direction(paired_diffs: np.ndarray) -> np.ndarray:
    """RepE/LAT reading vector: top singular vector of the paired differences (PLAN S2.2).

    paired_diffs: [n_pairs, d] of (FULL-NEUTRAL) difference vectors. Taken ABOUT THE ORIGIN (not
    mean-centered): the FULL-NEUTRAL differences are consistently signed, so the shared design
    direction is their dominant second-moment axis; centering would remove exactly that signal and
    leave only isotropic nuisance variance. Sign-aligned to the mean difference; returned unit-norm.
    """
    X = np.asarray(paired_diffs, float)
    _, _, Vt = np.linalg.svd(X, full_matrices=False)  # about the origin (uncentered)
    pc1 = Vt[0]
    if np.dot(pc1, X.mean(axis=0)) < 0:  # sign-align to the mean shift
        pc1 = -pc1
    return unit(pc1)


def direction_agreement(v_diff: np.ndarray, paired_diffs: np.ndarray,
                        probe_w: np.ndarray | None = None) -> dict:
    """Cosine agreement of diff-in-means with PCA-PC1 (and optionally a probe direction; PLAN S2.2)."""
    pc1 = pca_direction(paired_diffs)
    out = {"cos_diff_pca": cosine(v_diff, pc1)}
    if probe_w is not None:
        out["cos_diff_probe"] = cosine(v_diff, probe_w)
    return out


def running_mean_cosine_stability(vectors: Sequence[np.ndarray], delta: int = None) -> dict:
    """Cosine-plateau check for the running mean (PLAN S2.0): require dcos < 0.01 over the last 20%.

    vectors[i] = the running mean after i+1 examples. Returns the max |dcos| over the tail window
    and whether it is below 0.01 (plateau reached).
    """
    V = [np.asarray(v, float) for v in vectors]
    n = len(V)
    if n < 5:
        return {"plateaued": False, "max_dcos_tail": float("nan"), "n": n}
    d = delta if delta else max(1, n // 10)
    tail_start = int(0.8 * n)
    dcos = []
    for i in range(max(d, tail_start), n):
        dcos.append(abs(1.0 - cosine(V[i], V[i - d])))
    mx = max(dcos) if dcos else float("nan")
    return {"plateaued": mx < 0.01, "max_dcos_tail": mx, "n": n, "delta": d}


# --------------------------------------------------------------------------- grids / freeze

def sweep_configs(stage: str = "coarse") -> list[dict]:
    """Enumerate the S2.3 sweep configs (layer x rho x variant) for coarse/refine (PLAN S2.3)."""
    g = steering_grids_config()
    s = g[stage]
    if stage == "coarse":
        layers, rhos, variants = s["layers"], s["rho_grid"], s["variants"]
    else:  # refine expands variants; layers/rhos are chosen from the coarse best at run time
        layers, rhos, variants = g["layers"][: s["best_n_layers"]], g["rho_grid"][: s["best_n_rho"]], s["variants"]
    return [{"layer": L, "rho": r, "variant": v} for L in layers for r in rhos for v in variants]


def select_operating_point(sweep_rows: list[dict], kl_threshold: float | None = None,
                           render_min: float | None = None) -> dict:
    """Freeze (ell*, rho*, variant*) = argmax dev POC-gain s.t. guardrails (PLAN S2.3 / PREREG §7).

    sweep_rows: dicts with keys {layer, rho, variant, poc_gain, mean_kl, render_success}. Ties
    broken by lower KL (gentler operating point). Returns the winning row or {} if none clear.
    """
    g = steering_grids_config()
    kl_t = g["kl_threshold"] if kl_threshold is None else kl_threshold
    r_min = g["render_min"] if render_min is None else render_min
    feasible = [r for r in sweep_rows
                if r["mean_kl"] <= kl_t and r["render_success"] >= r_min and r["poc_gain"] > 0]
    if not feasible:
        return {}
    feasible.sort(key=lambda r: (-r["poc_gain"], r["mean_kl"]))
    return feasible[0]


def write_frozen(path, layer_star: int, rho_star: float, variant_star: str, **selection) -> dict:
    """Write config/steering_frozen.yaml after the dev sweep (PLAN S2.3; git-tag before held-out)."""
    import yaml

    doc = dict(steering_frozen_config())
    doc.update({
        "frozen": True, "layer_star": int(layer_star), "rho_star": float(rho_star),
        "variant_star": variant_star,
    })
    doc["selection"] = {**doc.get("selection", {}), **selection}
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, sort_keys=False)
    return doc


def norm_matched_random(v_ref: np.ndarray, k: int = 5, seed: int = 0) -> list[np.ndarray]:
    """k random Gaussian directions re-normalized to ||v_ref|| (specificity control; PLAN S2.4)."""
    rng = np.random.default_rng(seed)
    d = np.asarray(v_ref).shape[0]
    target = float(np.linalg.norm(v_ref))
    out = []
    for _ in range(k):
        r = rng.standard_normal(d)
        out.append(unit(r) * target)
    return out


def reproduction_fraction(poc_steered: float, poc_unsteered: float, poc_full: float) -> float:
    """%skill-reproduced = (POC_steered - POC_unsteered)/(POC_FULL - POC_unsteered) (PLAN S2.4)."""
    denom = poc_full - poc_unsteered
    if denom == 0:
        return float("nan")
    return 100.0 * (poc_steered - poc_unsteered) / denom


def attenuation_pct(poc_full: float, poc_full_ablated: float, poc_unsteered: float) -> float:
    """attenuation% = (POC_FULL - POC_FULL-ablated)/(POC_FULL - POC_unsteered) (flip test; PLAN S2.5)."""
    denom = poc_full - poc_unsteered
    if denom == 0:
        return float("nan")
    return 100.0 * (poc_full - poc_full_ablated) / denom


# --------------------------------------------------------------------------- KL guardrail (GPU)

def mean_token_kl(model, eval_ids, layer: int, vhat, alpha: float) -> float:
    """Mean per-token KL(steered || unsteered) over a fixed eval text (THEORY T8.6). Import-guarded.

    Drives the model steered (addition hook at `layer`) vs unsteered and averages the per-token KL
    of the next-token distributions. Runs on the tiny Qwen2 model in tests; on the 7B on Colab.
    """
    import torch
    import torch.nn.functional as F
    from . import hooks

    with torch.no_grad():
        base_logits = model(eval_ids).logits
        v = torch.as_tensor(np.asarray(vhat), dtype=base_logits.dtype)
        with hooks.addition_hook(model, layer, v, alpha):
            steer_logits = model(eval_ids).logits
        p = F.log_softmax(steer_logits, dim=-1)
        q = F.log_softmax(base_logits, dim=-1)
        kl = (p.exp() * (p - q)).sum(dim=-1)  # KL(steered||unsteered) per token
        return float(kl.mean())
