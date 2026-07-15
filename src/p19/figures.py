"""Figure builders F1-F13 from results tables (PLAN §V.1; matplotlib Agg, CPU).

Reusable plotting functions imported by the notebooks (notebooks carry narrative + orchestration;
reusable machinery lives here). All functions take already-computed data and return a matplotlib
Figure; none re-run analysis. Agg backend so they render headless.
"""
from __future__ import annotations

from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def forest_plot(rows: Sequence[dict], title: str = "F1 — ablation forest") -> "plt.Figure":
    """F1: standardized delta vs reference with CIs. rows: {label, delta, lo, hi}."""
    fig, ax = plt.subplots(figsize=(6, max(2, 0.4 * len(rows))))
    ys = range(len(rows))
    for y, r in zip(ys, rows):
        ax.plot([r["lo"], r["hi"]], [y, y], color="#444", lw=1.5)
        ax.plot(r["delta"], y, "o", color="#b7472a")
    ax.axvline(0, color="#999", ls="--", lw=1)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([r["label"] for r in rows])
    ax.set_xlabel("standardized δ (95% CI)")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def localization_plot(layers: Sequence[int], auc: Sequence[float], selectivity: Sequence[float],
                      patch: Sequence[float] | None = None, band: Sequence[int] | None = None,
                      title: str = "F5 — localization by layer") -> "plt.Figure":
    """F5: probe AUC + selectivity + patch %-recovered by layer, band shaded."""
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(layers, auc, "-o", label="probe AUC", color="#1f77b4")
    ax.plot(layers, selectivity, "-s", label="selectivity", color="#ff7f0e")
    if patch is not None:
        ax.plot(layers, patch, "-^", label="patch %-recovered", color="#2ca02c")
    if band:
        ax.axvspan(min(band) - 0.5, max(band) + 0.5, color="#ffe08a", alpha=0.3, label="band")
    ax.set_xlabel("layer")
    ax.set_ylabel("score")
    ax.legend()
    ax.set_title(title)
    fig.tight_layout()
    return fig


def dose_response(rho: Sequence[float], poc_gain: Sequence[float], render: Sequence[float],
                  kl_threshold: float = 0.30, render_min: float = 0.90,
                  title: str = "F7 — dose-response") -> "plt.Figure":
    """F7: POC-gain & render-success vs rho, with failure shading."""
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.plot(rho, poc_gain, "-o", color="#b7472a", label="POC-gain")
    ax1.axhline(0, color="#ccc", lw=1)
    ax1.set_xlabel("ρ (norm-relative coefficient)")
    ax1.set_ylabel("POC-gain", color="#b7472a")
    ax2 = ax1.twinx()
    ax2.plot(rho, render, "-s", color="#1f77b4", label="render-success")
    ax2.axhline(render_min, color="#1f77b4", ls="--", lw=1)
    ax2.set_ylabel("render-success", color="#1f77b4")
    for r, rs in zip(rho, render):
        if rs < render_min:
            ax1.axvspan(r - 0.02, r + 0.02, color="#f0f0f0", alpha=0.5)
    ax1.set_title(title)
    fig.tight_layout()
    return fig


def heldout_bars(arms: dict[str, float], errors: dict[str, float] | None = None,
                 reproduced_pct: float | None = None,
                 title: str = "F8 — held-out causal bar") -> "plt.Figure":
    """F8: POC by arm {unsteered, steered, random, FULL} with %-reproduced annotation."""
    fig, ax = plt.subplots(figsize=(6, 4))
    names = list(arms)
    vals = [arms[n] for n in names]
    errs = [errors.get(n, 0) for n in names] if errors else None
    ax.bar(names, vals, yerr=errs, color=["#999", "#b7472a", "#888", "#1f77b4"][: len(names)],
           capsize=4)
    if reproduced_pct is not None:
        ax.annotate(f"{reproduced_pct:.0f}% reproduced", xy=(0.5, 0.9),
                    xycoords="axes fraction", ha="center")
    ax.set_ylabel("POC")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def psi_validation(human_rating: Sequence[float], psi: Sequence[float], rho: float,
                   title: str = "F10 — PSI validation") -> "plt.Figure":
    """F10: PSI vs human 'AI-generated' rating with the Spearman rho annotated."""
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(human_rating, psi, alpha=0.6, color="#7c3aed")
    ax.set_xlabel("human 'looks AI-generated' (1-5)")
    ax.set_ylabel("PSI")
    ax.annotate(f"ρ = {rho:.2f}", xy=(0.05, 0.92), xycoords="axes fraction")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def reliability_bars(alpha_K: float, ac1: float, pi_max: float,
                     title: str = "F11 — judge reliability") -> "plt.Figure":
    """F11: alpha_K, AC1, and pi_max with the gate thresholds."""
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(["alpha_K", "AC1", "pi_max"], [alpha_K, ac1, pi_max],
           color=["#1f77b4", "#2ca02c", "#ff7f0e"])
    ax.axhline(0.667, color="#1f77b4", ls="--", lw=1)
    ax.axhline(0.80, color="#2ca02c", ls="--", lw=1)
    ax.set_ylim(0, 1)
    ax.set_title(title)
    fig.tight_layout()
    return fig


def stability_plot(n: Sequence[int], cos: Sequence[float], threshold: float = 0.01,
                   title: str = "F13 — running-mean cosine stability") -> "plt.Figure":
    """F13: cosine of the running mean vs n examples, plateau threshold line."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(n, cos, "-o", color="#333")
    ax.axhline(1 - threshold, color="#b7472a", ls="--", lw=1, label=f"plateau (Δcos<{threshold})")
    ax.set_xlabel("n examples")
    ax.set_ylabel("cos(running mean, prev)")
    ax.legend()
    ax.set_title(title)
    fig.tight_layout()
    return fig


def interaction_heatmap(matrix, labels: Sequence[str] = ("C1", "C2", "C3", "C4", "C5"),
                        title: str = "F3 — 2FI heatmap") -> "plt.Figure":
    """F3: 5x5 two-factor-interaction coefficient heatmap."""
    import numpy as np

    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(np.asarray(matrix), cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    fig.colorbar(im, ax=ax, label="2FI coefficient")
    ax.set_title(title)
    fig.tight_layout()
    return fig
