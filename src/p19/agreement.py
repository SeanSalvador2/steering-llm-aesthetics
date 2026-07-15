"""Chance-corrected agreement: Krippendorff alpha (ordinal) + Gwet AC1 (THEORY §T4; PLAN §III.8).

The reliability gate (PREREG §5): trust the preference signal iff alpha_K >= 0.667 OR (AC1 >= 0.80
under demonstrable marginal skew). Both coefficients and their bootstrap CIs run here on synthetic
labels; on Colab they run on the judge-vs-Sean N=100 subset.

Data model: `units` is a list of per-item rating dicts {rater_id: category} (missing raters allowed).
Categories are an ordered list (ordinal distance uses their order; THEORY T4.4).
"""
from __future__ import annotations

import itertools
import math
import random
from typing import Any, Callable, Hashable, Sequence

import numpy as np


def _category_index(categories: Sequence[Hashable]) -> dict[Hashable, int]:
    return {c: i for i, c in enumerate(categories)}


def _infer_categories(units: list[dict]) -> list[Hashable]:
    seen: list[Hashable] = []
    for u in units:
        for v in u.values():
            if v is not None and v not in seen:
                seen.append(v)
    # if all ints, sort numerically for a sensible ordinal order
    if all(isinstance(x, (int, float)) for x in seen):
        return sorted(seen)
    return seen


def coincidence_matrix(units: list[dict], categories: Sequence[Hashable]) -> np.ndarray:
    """Krippendorff coincidence matrix o_ck (THEORY T4.3).

    Each unit with m_u >= 2 ratings contributes each ordered pair (c,k) weighted 1/(m_u - 1).
    """
    idx = _category_index(categories)
    q = len(categories)
    o = np.zeros((q, q), dtype=np.float64)
    for u in units:
        vals = [v for v in u.values() if v is not None]
        m = len(vals)
        if m < 2:
            continue
        for a, b in itertools.permutations(vals, 2):
            o[idx[a], idx[b]] += 1.0 / (m - 1)
    return o


def _delta2(categories: Sequence[Hashable], n_c: np.ndarray, level: str) -> np.ndarray:
    """Squared distance matrix delta^2_ck (THEORY T4.4). 'nominal' or 'ordinal'."""
    q = len(categories)
    d2 = np.zeros((q, q))
    if level == "nominal":
        for c in range(q):
            for k in range(q):
                d2[c, k] = 0.0 if c == k else 1.0
        return d2
    # ordinal: (sum_{g=c}^{k} n_g - (n_c + n_k)/2)^2
    for c in range(q):
        for k in range(q):
            lo, hi = (c, k) if c <= k else (k, c)
            s = n_c[lo:hi + 1].sum() - (n_c[c] + n_c[k]) / 2.0
            d2[c, k] = s * s
    return d2


def krippendorff_alpha(units: list[dict], level: str = "ordinal",
                       categories: Sequence[Hashable] | None = None) -> float:
    """Krippendorff's alpha = 1 - D_o/D_e (THEORY T4.2/T4.3), with the (n-1)-corrected D_e."""
    cats = list(categories) if categories is not None else _infer_categories(units)
    if len(cats) < 2:
        return 1.0
    o = coincidence_matrix(units, cats)
    n_c = o.sum(axis=1)
    n = n_c.sum()
    if n <= 1:
        return float("nan")
    d2 = _delta2(cats, n_c, level)
    d_o = (o * d2).sum() / n
    d_e = (np.outer(n_c, n_c) * d2).sum() / (n * (n - 1))
    if d_e == 0:
        return 1.0
    return 1.0 - d_o / d_e


def gwet_ac1(units: list[dict], categories: Sequence[Hashable] | None = None) -> float:
    """Gwet's AC1 (THEORY T4.5): p_e^gamma = (1/(q-1)) sum pi_k(1-pi_k); stable under skew."""
    cats = list(categories) if categories is not None else _infer_categories(units)
    q = len(cats)
    if q < 2:
        return 1.0
    idx = _category_index(cats)

    # observed agreement p_o: over items with >= 2 ratings, mean pairwise agreement
    agrees, pairs = 0.0, 0.0
    counts = np.zeros(q)
    total_ratings = 0
    for u in units:
        vals = [v for v in u.values() if v is not None]
        for v in vals:
            counts[idx[v]] += 1
            total_ratings += 1
        m = len(vals)
        if m < 2:
            continue
        for a, b in itertools.combinations(vals, 2):
            pairs += 1
            if a == b:
                agrees += 1
    if pairs == 0 or total_ratings == 0:
        return float("nan")
    p_o = agrees / pairs
    pi = counts / total_ratings
    p_e = (1.0 / (q - 1)) * float(np.sum(pi * (1 - pi)))
    if p_e == 1:
        return 1.0
    return (p_o - p_e) / (1 - p_e)


def marginal_distribution(units: list[dict],
                          categories: Sequence[Hashable] | None = None) -> dict:
    """Pooled marginal category shares + pi_max (for the demonstrable-skew check, T4.4)."""
    cats = list(categories) if categories is not None else _infer_categories(units)
    idx = _category_index(cats)
    counts = np.zeros(len(cats))
    for u in units:
        for v in u.values():
            if v is not None:
                counts[idx[v]] += 1
    total = counts.sum() or 1.0
    shares = {c: counts[idx[c]] / total for c in cats}
    return {"shares": shares, "pi_max": float(counts.max() / total)}


def bootstrap_ci(func: Callable[[list[dict]], float], units: list[dict],
                 B: int = 2000, seed: int = 0, alpha: float = 0.05) -> dict:
    """Percentile bootstrap CI resampling whole units (THEORY T4.1 CIs)."""
    rng = random.Random(seed)
    n = len(units)
    stats = []
    for _ in range(B):
        sample = [units[rng.randrange(n)] for _ in range(n)]
        val = func(sample)
        if val == val:  # not NaN
            stats.append(val)
    stats.sort()
    if not stats:
        return {"point": float("nan"), "lo": float("nan"), "hi": float("nan")}
    lo = stats[int((alpha / 2) * len(stats))]
    hi = stats[min(len(stats) - 1, int((1 - alpha / 2) * len(stats)))]
    return {"point": func(units), "lo": lo, "hi": hi, "B": len(stats)}


def reliability_gate(units: list[dict], categories: Sequence[Hashable] | None = None,
                     alpha_min: float = 0.667, ac1_min: float = 0.80,
                     skew_pi_max: float = 0.80) -> dict:
    """The preregistered disjunctive gate (PREREG §5; THEORY T4.6).

    Pass iff alpha_K >= alpha_min OR (AC1 >= ac1_min AND pi_max >= skew_pi_max).
    """
    a = krippendorff_alpha(units, "ordinal", categories)
    ac1 = gwet_ac1(units, categories)
    marg = marginal_distribution(units, categories)
    skew = marg["pi_max"] >= skew_pi_max
    passed = (a >= alpha_min) or (ac1 >= ac1_min and skew)
    return {
        "alpha_K": a, "AC1": ac1, "pi_max": marg["pi_max"],
        "demonstrable_skew": skew, "pass": bool(passed),
        "rung": "alpha" if a >= alpha_min else ("ac1_skew" if passed else "fail"),
    }
