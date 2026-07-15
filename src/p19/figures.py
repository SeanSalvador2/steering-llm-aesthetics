"""Figure builders F1-F13 from results tables (PLAN §V.1; matplotlib Agg, CPU).

Reusable plotting functions imported by the notebooks (notebooks carry narrative + orchestration;
reusable machinery lives here). All functions take already-computed data and return a matplotlib
Figure; none re-run analysis. Agg backend so they render headless.

House style (PLAN §V.1 "professional matplotlib"): a colorblind-safe palette (Okabe-Ito), axis
labels carrying units, titles carrying the F-id and the question the figure answers, CI bands /
error bars wherever there is uncertainty, and no chartjunk. The palette and the small `_finish`
helper keep every figure in one visual system.
"""
from __future__ import annotations

from typing import Sequence

import matplotlib  # noqa: F401  (backend is left as-is: 'agg' when headless, 'inline' inside a notebook)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# --- Okabe-Ito colorblind-safe palette (PLAN §V.1) -----------------------------------------
PALETTE = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "yellow": "#F0E442",
    "grey": "#666666",
    "black": "#000000",
}
# semantic roles
C_PRIMARY = PALETTE["blue"]      # objective / POC signal
C_ACCENT = PALETTE["vermillion"] # effect / steering
C_GOOD = PALETTE["green"]        # pass / render-success
C_WARN = PALETTE["orange"]       # threshold / caution
C_REF = PALETTE["grey"]          # reference lines / CIs
C_SECOND = PALETTE["purple"]     # secondary signal (preference / PSI)


def _finish(fig: "plt.Figure", ax=None) -> "plt.Figure":
    """Common polish: de-clutter spines, light grid, tight layout (no chartjunk)."""
    axes = fig.axes if ax is None else [ax]
    for a in axes:
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
        a.grid(True, which="major", axis="both", color="#e6e6e6", lw=0.6, zorder=0)
        a.set_axisbelow(True)
    fig.tight_layout()
    return fig


# =========================================================================== F1 — ablation forest
def forest_plot(rows: Sequence[dict], title: str = "F1 · Which components carry the skill? "
                "(ablation forest)", xlabel: str = "standardized δ vs reference (95% CI)",
                panel: str | None = None) -> "plt.Figure":
    """F1: standardized delta vs reference with CIs. rows: {label, delta, lo, hi[, sig]}.

    A row with truthy `sig` is drawn filled (survives Holm); non-significant rows are hollow.
    `panel` (e.g. "POC" / "BT-utility") is appended to the title for the twin-panel layout.
    """
    fig, ax = plt.subplots(figsize=(6.2, max(2.2, 0.46 * len(rows))))
    ys = range(len(rows))
    for y, r in zip(ys, rows):
        ax.plot([r["lo"], r["hi"]], [y, y], color=C_REF, lw=1.6, zorder=2)
        sig = r.get("sig", True)
        ax.plot(r["delta"], y, "o", ms=7, color=C_ACCENT if sig else "white",
                markeredgecolor=C_ACCENT, markeredgewidth=1.6, zorder=3)
    ax.axvline(0, color=C_REF, ls="--", lw=1, zorder=1)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([r["label"] for r in rows])
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_title(title if panel is None else f"{title}\n[{panel}]", fontsize=10)
    return _finish(fig, ax)


# =========================================================================== F2 — nec × suff scatter
def necessity_sufficiency_scatter(
    points: Sequence[dict],
    title: str = "F2 · Are components necessary vs sufficient? (RQ1 × RQ2)",
) -> "plt.Figure":
    """F2: x = sufficiency δ (AOI-Cᵢ−NEUTRAL), y = necessity δ (FULL−LOO-Cᵢ), one point per component.

    points: {label, suff, nec[, suff_lo, suff_hi, nec_lo, nec_hi]}. The y=x line marks
    "necessity == sufficiency" (no interactions, THEORY T1.7); points above it are more necessary
    than sufficient (positive interaction load).
    """
    fig, ax = plt.subplots(figsize=(5.4, 5.2))
    xs = [p["suff"] for p in points]
    ys = [p["nec"] for p in points]
    lo = min(0, min(xs), min(ys)) - 0.05
    hi = max(xs + ys) + 0.1
    ax.plot([lo, hi], [lo, hi], ls="--", color=C_REF, lw=1, label="necessity = sufficiency (no 2FI)")
    for p in points:
        if {"suff_lo", "suff_hi"} <= set(p):
            ax.plot([p["suff_lo"], p["suff_hi"]], [p["nec"], p["nec"]], color=C_REF, lw=1, alpha=0.6)
        if {"nec_lo", "nec_hi"} <= set(p):
            ax.plot([p["suff"], p["suff"]], [p["nec_lo"], p["nec_hi"]], color=C_REF, lw=1, alpha=0.6)
        ax.plot(p["suff"], p["nec"], "o", ms=9, color=C_PRIMARY, zorder=3)
        ax.annotate(p["label"], (p["suff"], p["nec"]), textcoords="offset points",
                    xytext=(7, 5), fontsize=9)
    ax.axhline(0, color=C_REF, lw=0.8)
    ax.axvline(0, color=C_REF, lw=0.8)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("sufficiency δ   (AOI-Cᵢ − NEUTRAL, POC units)")
    ax.set_ylabel("necessity δ   (FULL − LOO-Cᵢ, POC units)")
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8, loc="lower right")
    return _finish(fig, ax)


# =========================================================================== F3 — interaction heatmap
def interaction_heatmap(matrix, labels: Sequence[str] = ("C1", "C2", "C3", "C4", "C5"),
                        star_mask=None, vlim: float | None = None,
                        title: str = "F3 · Do components interact? (2FI heatmap)") -> "plt.Figure":
    """F3: 5x5 two-factor-interaction coefficient heatmap; BH-significant cells starred."""
    M = np.asarray(matrix, float)
    if vlim is None:
        vlim = max(1e-6, float(np.nanmax(np.abs(M))))
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-vlim, vmax=vlim)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    if star_mask is not None:
        sm = np.asarray(star_mask)
        for i in range(len(labels)):
            for j in range(len(labels)):
                if sm[i, j]:
                    ax.text(j, i, "★", ha="center", va="center", color="black", fontsize=12)
    fig.colorbar(im, ax=ax, label="2FI coefficient βᵢⱼ (POC units)", fraction=0.046, pad=0.04)
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    return fig


# =========================================================================== F4 — metric correlation
def metric_correlation_matrix(
    corr, labels: Sequence[str], family_bounds: Sequence[int] | None = None,
    title: str = "F4 · Which objective metrics are redundant? (Spearman ρ)",
) -> "plt.Figure":
    """F4: objective-metric × objective-metric Spearman correlation matrix, family blocks outlined."""
    M = np.asarray(corr, float)
    n = len(labels)
    fig, ax = plt.subplots(figsize=(max(5.5, 0.5 * n + 2), max(5.0, 0.5 * n + 1.5)))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels, fontsize=7)
    if family_bounds:
        for b in family_bounds:
            ax.axhline(b - 0.5, color="black", lw=0.8)
            ax.axvline(b - 0.5, color="black", lw=0.8)
    fig.colorbar(im, ax=ax, label="Spearman ρ", fraction=0.046, pad=0.04)
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    return fig


# =========================================================================== F5 — localization
def localization_plot(layers: Sequence[int], auc: Sequence[float], selectivity: Sequence[float],
                      patch: Sequence[float] | None = None, band: Sequence[int] | None = None,
                      auc_min: float = 0.80, sel_min: float = 0.15,
                      title: str = "F5 · Where does the skill signal live? (localization by layer)"
                      ) -> "plt.Figure":
    """F5: probe AUC + selectivity + patch %-recovered by layer, band shaded, thresholds drawn."""
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(layers, auc, "-o", label="probe AUC", color=C_PRIMARY, zorder=3)
    ax.plot(layers, selectivity, "-s", label="selectivity", color=C_WARN, zorder=3)
    if patch is not None:
        ax.plot(layers, patch, "-^", label="patch %-recovered", color=C_GOOD, zorder=3)
    ax.axhline(auc_min, color=C_PRIMARY, ls=":", lw=1)
    ax.axhline(sel_min, color=C_WARN, ls=":", lw=1)
    if band:
        ax.axvspan(min(band) - 0.5, max(band) + 0.5, color=PALETTE["yellow"], alpha=0.25,
                   label="chosen band", zorder=0)
    ax.set_xlabel("layer ℓ (of 28)")
    ax.set_ylabel("score  (AUC & selectivity ∈ [0,1]; patch = fraction recovered)")
    ax.legend(fontsize=8, loc="center right")
    ax.set_title(title, fontsize=10)
    return _finish(fig, ax)


# =========================================================================== F6 — steering heatmap
def steering_heatmap(
    layers: Sequence[int], rhos: Sequence[float], gain, guardrail_mask=None, star: tuple | None = None,
    title: str = "F6 · Where and how hard to steer? (dev POC-gain by α×layer)",
) -> "plt.Figure":
    """F6: heatmap of dev POC-gain over (layer, ρ); guardrail-violating cells hatched; ℓ*,ρ* starred.

    gain[i, j] = dev POC-gain at rhos[i], layers[j]. guardrail_mask[i,j] True => KL/render violated.
    """
    G = np.asarray(gain, float)
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    vlim = max(1e-6, float(np.nanmax(np.abs(G))))
    im = ax.imshow(G, cmap="RdBu_r", vmin=-vlim, vmax=vlim, aspect="auto", origin="lower")
    ax.set_xticks(range(len(layers)))
    ax.set_xticklabels(layers)
    ax.set_yticks(range(len(rhos)))
    ax.set_yticklabels(rhos)
    if guardrail_mask is not None:
        gm = np.asarray(guardrail_mask)
        for i in range(len(rhos)):
            for j in range(len(layers)):
                if gm[i, j]:
                    ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                               hatch="///", edgecolor="black", lw=0.0))
    if star is not None:
        ax.plot(star[0], star[1], marker="*", color="black", ms=18, markeredgecolor="white",
                label="frozen (ℓ*, ρ*)")
        ax.legend(fontsize=8, loc="upper right")
    fig.colorbar(im, ax=ax, label="dev POC-gain (POC units)", fraction=0.046, pad=0.04)
    ax.set_xlabel("layer ℓ")
    ax.set_ylabel("ρ (norm-relative coefficient)")
    ax.set_title(title + "\n(hatched = KL>0.30 nats or render<0.90 guardrail)", fontsize=9)
    fig.tight_layout()
    return fig


# =========================================================================== F7 — dose-response
def dose_response(rho: Sequence[float], poc_gain: Sequence[float], render: Sequence[float],
                  kl_threshold: float = 0.30, render_min: float = 0.90, gain_lo=None, gain_hi=None,
                  title: str = "F7 · How much steering is too much? (dose-response)") -> "plt.Figure":
    """F7: POC-gain (with CI band) & render-success vs ρ, failure region shaded where render<min."""
    rho = list(rho)
    fig, ax1 = plt.subplots(figsize=(7.2, 4.2))
    ax1.plot(rho, poc_gain, "-o", color=C_ACCENT, label="POC-gain", zorder=3)
    if gain_lo is not None and gain_hi is not None:
        ax1.fill_between(rho, gain_lo, gain_hi, color=C_ACCENT, alpha=0.15, zorder=1)
    ax1.axhline(0, color=C_REF, lw=1)
    ax1.set_xlabel("ρ (norm-relative steering coefficient)")
    ax1.set_ylabel("POC-gain vs unsteered (POC units)", color=C_ACCENT)
    ax1.tick_params(axis="y", labelcolor=C_ACCENT)
    ax2 = ax1.twinx()
    ax2.plot(rho, render, "-s", color=C_PRIMARY, label="render-success", zorder=3)
    ax2.axhline(render_min, color=C_PRIMARY, ls="--", lw=1)
    ax2.set_ylabel("render-success (fraction)", color=C_PRIMARY)
    ax2.tick_params(axis="y", labelcolor=C_PRIMARY)
    ax2.set_ylim(0, 1.02)
    for r, rs in zip(rho, render):
        if rs < render_min:
            ax1.axvspan(r - 0.02, r + 0.02, color="#f0f0f0", alpha=0.7, zorder=0)
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    ax1.set_title(title + "  (grey = render below floor)", fontsize=10)
    fig.tight_layout()
    return fig


# =========================================================================== F8 — held-out bars
def heldout_bars(arms: dict[str, float], errors: dict[str, float] | None = None,
                 reproduced_pct: float | None = None,
                 title: str = "F8 · Does the direction steer with no prompt? (held-out causal test)"
                 ) -> "plt.Figure":
    """F8: POC by arm {unsteered, steered, random, FULL} with error bars + %-reproduced annotation."""
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    names = list(arms)
    vals = [arms[n] for n in names]
    errs = [errors.get(n, 0) for n in names] if errors else None
    colormap = {"unsteered": C_REF, "steered": C_ACCENT, "random": PALETTE["sky"], "FULL": C_PRIMARY}
    colors = [colormap.get(n, C_REF) for n in names]
    ax.bar(names, vals, yerr=errs, color=colors, capsize=5, zorder=3, edgecolor="white")
    if reproduced_pct is not None:
        ax.annotate(f"{reproduced_pct:.0f}% of skill gain reproduced", xy=(0.5, 0.94),
                    xycoords="axes fraction", ha="center", fontsize=9,
                    bbox=dict(boxstyle="round", fc="#fff6e6", ec=C_WARN))
    ax.axhline(0, color=C_REF, lw=0.8)
    ax.set_ylabel("POC (held-out, POC units)")
    ax.set_title(title, fontsize=10)
    return _finish(fig, ax)


# =========================================================================== F9 — correspondence
def correspondence_figure(
    cos_matrix, labels: Sequence[str], signature_grid, sig_rows: Sequence[str],
    sig_cols: Sequence[str], title: str = "F9 · Does each component steer its own metric family? (RQ8)",
) -> "plt.Figure":
    """F9: left = cosine matrix among {v_Cᵢ, v_full}; right = steer-family × ablation-family match grid.

    signature_grid[i, j] in [0,1] = alignment of sub-vector i's steering signature with ablation
    family j; the diagonal lighting up is "correspondence found".
    """
    C = np.asarray(cos_matrix, float)
    S = np.asarray(signature_grid, float)
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.8))
    imL = axL.imshow(C, cmap="RdBu_r", vmin=-1, vmax=1)
    axL.set_xticks(range(len(labels)))
    axL.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    axL.set_yticks(range(len(labels)))
    axL.set_yticklabels(labels, fontsize=8)
    axL.set_title("cosine among sub-directions\n(near-0 off-diagonal ⇒ orthogonal)", fontsize=9)
    fig.colorbar(imL, ax=axL, label="cosine", fraction=0.046, pad=0.04)

    imR = axR.imshow(S, cmap="Greens", vmin=0, vmax=1)
    axR.set_xticks(range(len(sig_cols)))
    axR.set_xticklabels(sig_cols, rotation=45, ha="right", fontsize=8)
    axR.set_yticks(range(len(sig_rows)))
    axR.set_yticklabels(sig_rows, fontsize=8)
    axR.set_title("steer signature × ablation signature\n(bright diagonal ⇒ correspondence)",
                  fontsize=9)
    fig.colorbar(imR, ax=axR, label="signature match", fraction=0.046, pad=0.04)
    fig.suptitle(title, fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


# =========================================================================== F10 — PSI validation
def psi_validation(human_rating: Sequence[float], psi: Sequence[float], rho: float,
                   rho_gate: float = 0.40,
                   title: str = "F10 · Does PSI track human 'AI-slop' judgment? (oracle gate)"
                   ) -> "plt.Figure":
    """F10: PSI vs human 'AI-generated' rating with the Spearman ρ and the admission gate annotated."""
    fig, ax = plt.subplots(figsize=(5.4, 5.0))
    hr = np.asarray(human_rating, float)
    ps = np.asarray(psi, float)
    ax.scatter(hr, ps, alpha=0.6, color=C_SECOND, edgecolor="white", zorder=3)
    if len(hr) >= 2 and np.std(hr) > 0:
        b, a = np.polyfit(hr, ps, 1)
        xs = np.linspace(hr.min(), hr.max(), 20)
        ax.plot(xs, a + b * xs, color=C_REF, lw=1.5, ls="--")
    passed = rho >= rho_gate
    ax.annotate(f"Spearman ρ = {rho:.2f}\ngate ρ ≥ {rho_gate:.2f}: "
                f"{'ADMIT' if passed else 'DEMOTE → 6-term POC'}",
                xy=(0.05, 0.86), xycoords="axes fraction", fontsize=9,
                bbox=dict(boxstyle="round", fc="#eef7f0" if passed else "#fdeaea",
                          ec=C_GOOD if passed else C_ACCENT))
    ax.set_xlabel("human 'looks AI-generated' rating (1–5)")
    ax.set_ylabel("purple-slop index PSI (0–1, lower = less slop)")
    ax.set_title(title, fontsize=10)
    return _finish(fig, ax)


# =========================================================================== F11 — judge reliability
def reliability_bars(alpha_K: float, ac1: float, pi_max: float, alpha_ci: tuple | None = None,
                     ac1_ci: tuple | None = None, alpha_gate: float = 0.667, ac1_gate: float = 0.80,
                     title: str = "F11 · Can we trust the VLM judge? (reliability gate)"
                     ) -> "plt.Figure":
    """F11: α_K, AC1, and π_max with bootstrap CIs and the two gate thresholds."""
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    names = ["α_K (ordinal)", "AC1 (Gwet)", "π_max (skew)"]
    vals = [alpha_K, ac1, pi_max]
    errs = None
    if alpha_ci and ac1_ci:
        errs = [[alpha_K - alpha_ci[0], ac1 - ac1_ci[0], 0],
                [alpha_ci[1] - alpha_K, ac1_ci[1] - ac1, 0]]
    ax.bar(names, vals, yerr=errs, color=[C_PRIMARY, C_GOOD, C_WARN], capsize=5, zorder=3,
           edgecolor="white")
    ax.axhline(alpha_gate, color=C_PRIMARY, ls="--", lw=1, label=f"α gate {alpha_gate:.3f}")
    ax.axhline(ac1_gate, color=C_GOOD, ls="--", lw=1, label=f"AC1 gate {ac1_gate:.2f}")
    ax.set_ylim(0, 1)
    ax.set_ylabel("coefficient value")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title(title, fontsize=10)
    return _finish(fig, ax)


# =========================================================================== F12 — anti-steerable
def anti_steerable_bars(
    types: Sequence[str], fractions: Sequence[float], seen_mask: Sequence[bool],
    threshold: float = 0.50,
    title: str = "F12 · Where does steering fail? (anti-steerable fraction by task type)",
) -> "plt.Figure":
    """F12: bar per task type (seen vs unseen colored), horizontal 50% brittleness line."""
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    colors = [C_PRIMARY if s else C_ACCENT for s in seen_mask]
    ax.bar(range(len(types)), fractions, color=colors, zorder=3, edgecolor="white")
    ax.axhline(threshold, color=C_REF, ls="--", lw=1.2, label=f"{threshold:.0%} brittleness line")
    ax.set_xticks(range(len(types)))
    ax.set_xticklabels(types, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("anti-steerable fraction (steered POC < unsteered)")
    ax.set_ylim(0, 1)
    handles = [plt.Rectangle((0, 0), 1, 1, color=C_PRIMARY),
               plt.Rectangle((0, 0), 1, 1, color=C_ACCENT)]
    ax.legend(handles + [ax.get_lines()[0]], ["seen type", "unseen (OOD) type",
              f"{threshold:.0%} line"], fontsize=8, loc="upper left")
    ax.set_title(title, fontsize=10)
    return _finish(fig, ax)


# =========================================================================== F13 — stability
def stability_plot(n: Sequence[int], cos: Sequence[float], threshold: float = 0.01,
                   title: str = "F13 · Is the extracted direction stable? (running-mean cosine)"
                   ) -> "plt.Figure":
    """F13: cosine of the running mean vs n examples, plateau threshold line."""
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.plot(n, cos, "-o", color=C_PRIMARY, zorder=3)
    ax.axhline(1 - threshold, color=C_ACCENT, ls="--", lw=1.2,
               label=f"plateau (Δcos < {threshold})")
    ax.set_xlabel("n extraction examples")
    ax.set_ylabel("cos(running mean, earlier mean)")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title(title, fontsize=10)
    return _finish(fig, ax)
