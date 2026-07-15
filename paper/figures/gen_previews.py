"""Export synthetic pipeline-validation preview figures F1-F13 for the paper draft.

Every figure here is built by the SAME machinery the real paper uses: `p19.figures`
(the plot builders, PLAN Sec. V.1) fed by `p19.synthetic` (planted ground truth,
same seeds as notebooks 05/06a/07a). The output PDFs are therefore an honest preview
of the final figures' layout and encoding, with SIMULATED numbers. Each is wrapped in
the paper by `\synthfig`, whose caption prefix marks it "Synthetic pipeline-validation
preview; replaced by real data (RUNBOOK session N)".

Run:  python paper/figures/gen_previews.py
Deps: matplotlib, numpy, pandas, scipy (all CPU; already in requirements-cpu.txt).
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402

import p19.figures as F  # noqa: E402
import p19.synthetic as S  # noqa: E402
from p19 import poc  # noqa: E402
from p19.config import cells_by_id  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 0


def _save(fig, name: str) -> None:
    path = os.path.join(HERE, name)
    fig.savefig(path, bbox_inches="tight")
    print("wrote", path)


def _poc_by_cell(df):
    """Recover POC per cell from the planted metric table (the real pipeline path)."""
    d = poc.add_poc_column(df.copy())
    return d.groupby("cell_id")["poc"].mean().to_dict()


def main() -> None:
    # ---- Stage-1 planted dataset (notebook 05 path) --------------------------------
    df, truth = S.stage1_dataset(n_prompts=40, seed=SEED)
    poc_by_cell = _poc_by_cell(df)
    neutral = poc_by_cell["NEUTRAL"]

    # F1 — ablation forest (necessity LOO, sufficiency AOI, BEAUTY1, NOSYS vs reference)
    rows = []
    for f in ["C1", "C2", "C3", "C4", "C5"]:
        d = truth.necessity[f]
        rows.append({"label": f"LOO-{f} (necessity)", "delta": d,
                     "lo": d - 0.11, "hi": d + 0.11, "sig": abs(d) > 0.12})
    for f in ["C1", "C2", "C3", "C4", "C5"]:
        d = truth.sufficiency[f]
        rows.append({"label": f"AOI-{f} (sufficiency)", "delta": d,
                     "lo": d - 0.10, "hi": d + 0.10, "sig": abs(d) > 0.12})
    gap = truth.full_neutral_gap
    rows.append({"label": "BEAUTY1 vs NEUTRAL", "delta": truth.beauty_frac * gap,
                 "lo": truth.beauty_frac * gap - 0.12, "hi": truth.beauty_frac * gap + 0.12, "sig": True})
    _save(F.forest_plot(rows, panel="POC (synthetic)"), "F1_preview.pdf")

    # F2 — necessity x sufficiency scatter
    pts = [{"label": f, "suff": truth.sufficiency[f], "nec": truth.necessity[f],
            "suff_lo": truth.sufficiency[f] - 0.09, "suff_hi": truth.sufficiency[f] + 0.09,
            "nec_lo": truth.necessity[f] - 0.10, "nec_hi": truth.necessity[f] + 0.10}
           for f in ["C1", "C2", "C3", "C4", "C5"]]
    _save(F.necessity_sufficiency_scatter(pts), "F2_preview.pdf")

    # F3 — 2FI interaction heatmap (planted C1xC5 super-additive, C2xC3 sub-additive)
    labels = ["C1", "C2", "C3", "C4", "C5"]
    M = np.zeros((5, 5))
    star = np.zeros((5, 5), bool)
    for (a, b), v in truth.twofi.items():
        i, j = labels.index(a), labels.index(b)
        M[i, j] = M[j, i] = v
        star[i, j] = star[j, i] = abs(v) > 0.08
    _save(F.interaction_heatmap(M, labels, star_mask=star), "F3_preview.pdf")

    # F4 — metric-correlation matrix (family-block structure)
    corr, labs, bounds = S.metric_correlation_preview(seed=SEED)
    _save(F.metric_correlation_matrix(corr, labs, family_bounds=bounds), "F4_preview.pdf")

    # F5 — localization by layer (probe AUC + selectivity + patch %-recovered)
    full, neu, groups, y, s2t = S.stage2_activations(seed=SEED)
    layers = list(range(s2t.n_layers))
    # cheap planted-consistent curves (the real ones come from p19.probes / p19.patching on Colab)
    auc = [min(0.99, 0.55 + 0.42 * (s2t.strengths[l] / max(s2t.strengths.values()))) for l in layers]
    sel = [max(0.0, a - 0.62) for a in auc]
    patch = [max(0.0, 0.9 * (s2t.strengths[l] / max(s2t.strengths.values())) - 0.02) for l in layers]
    _save(F.localization_plot(layers, auc, sel, patch, band=list(range(*(s2t.band[0], s2t.band[1] + 1)))
                              if False else list(range(s2t.band[0], s2t.band[1] + 1))), "F5_preview.pdf")

    # F6 — steering alpha x layer heatmap (dev POC-gain) with guardrail hatch + frozen star
    layers6 = [11, 13, 15, 17, 20]
    rhos6 = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
    grid = S.stage2_sweep(layers6, rhos6, opt_layer=15, opt_rho=0.3, seed=SEED)
    gain = np.zeros((len(rhos6), len(layers6)))
    guard = np.zeros((len(rhos6), len(layers6)), bool)
    for r in grid:
        i, j = rhos6.index(r["rho"]), layers6.index(r["layer"])
        gain[i, j] = r["poc_gain"]
        guard[i, j] = (r["mean_kl"] > 0.30) or (r["render_success"] < 0.90)
    star6 = (layers6.index(15), rhos6.index(0.3))
    _save(F.steering_heatmap(layers6, rhos6, gain, guardrail_mask=guard, star=star6), "F6_preview.pdf")

    # F7 — dose-response (POC-gain + render-success vs rho)
    row_at = {r["rho"]: r for r in grid if r["layer"] == 15}
    rr = sorted(row_at)
    pg = [row_at[r]["poc_gain"] for r in rr]
    rs = [row_at[r]["render_success"] for r in rr]
    _save(F.dose_response(rr, pg, rs, gain_lo=[p - 0.05 for p in pg],
                          gain_hi=[p + 0.05 for p in pg]), "F7_preview.pdf")

    # F8 — held-out causal bars {unsteered, steered, random, FULL} + %-reproduced
    arms_df, arms_truth = S.stage2_arms(reproduce_frac=0.6, skill_gap=0.9, seed=SEED)
    means = arms_df.groupby("arm")["poc"].mean()
    base = means["unsteered"]
    arms = {"unsteered": means["unsteered"] - base, "steered": means["steered"] - base,
            "random": means["random"] - base, "FULL": means["full_ref"] - base}
    errs = {k: 0.06 for k in arms}
    _save(F.heldout_bars(arms, errors=errs, reproduced_pct=arms_truth.reproduce_frac * 100),
          "F8_preview.pdf")

    # F9 — correspondence (cosine matrix + signature-match grid)
    cos, sig_grid, labs9, fams = S.stage2_correspondence(seed=SEED)
    _save(F.correspondence_figure(cos, labs9, sig_grid, fams, fams), "F9_preview.pdf")

    # F10 — PSI validation scatter
    human, psi, rho = S.psi_validation_preview(seed=SEED)
    _save(F.psi_validation(human, psi, rho), "F10_preview.pdf")

    # F11 — judge reliability (kappa paradox exemplar: skewed panel alpha_K low, AC1 high)
    from p19.agreement import krippendorff_alpha, gwet_ac1
    labels_syn = S.reliability_labels(n=100, agreement=0.82, skew=0.88, seed=SEED)
    aK = krippendorff_alpha(labels_syn, level="ordinal")
    ac1 = gwet_ac1(labels_syn)
    j = np.array([u["judge"] for u in labels_syn])
    pi_max = float(max(np.bincount(j + 2)) / len(j))
    _save(F.reliability_bars(aK, ac1, float(pi_max), alpha_ci=(aK - 0.08, aK + 0.08),
                             ac1_ci=(ac1 - 0.05, ac1 + 0.05)), "F11_preview.pdf")

    # F12 — anti-steerable fraction by task type (seen vs unseen)
    anti = arms_truth.anti_steerable_by_type
    types = list(anti)
    seen_types = {arms_truth.task_types[p] for p in arms_df[arms_df.split == "seen"].prompt_id.unique()}
    fr = [anti[t] for t in types]
    seen_mask = [t in seen_types for t in types]
    _save(F.anti_steerable_bars(types, fr, seen_mask), "F12_preview.pdf")

    # F13 — running-mean cosine stability
    ns = list(range(20, 201, 20))
    cosv = [1 - 0.09 * np.exp(-(n - 20) / 45.0) for n in ns]
    _save(F.stability_plot(ns, cosv), "F13_preview.pdf")

    print("\nAll preview figures written to", HERE)


if __name__ == "__main__":
    main()
