"""Synthetic-dry-run generators: the planted ground truth must be recovered by the REAL pipeline.

These tests are the guarantee behind the executed notebooks (05, 06a, 07a): if the pipeline recovers
a KNOWN plant here, the same pipeline applied to the real GPU-phase data is trustworthy (PLAN §V.3).
Sizes are kept small for speed; the notebooks use the fuller defaults.
"""
import numpy as np
import pandas as pd

from p19 import synthetic as syn
from p19 import poc, mixedlm, multiplicity, agreement, bt_model, steering, probes, patching, activations


# --------------------------------------------------------------------------- Stage-1
def _stage1_poc(seed=0, n_prompts=24):
    df, truth = syn.stage1_dataset(n_prompts=n_prompts, seed=seed)
    res = poc.compute_poc(df)
    df["poc"] = res["poc"].values
    df = df.dropna(subset=["poc"]).reset_index(drop=True)  # render-failed excluded (POC semantics)
    return df, truth, res


def test_stage1_poc_recovers_planted_cell_quality():
    df, truth, res = _stage1_poc()
    assert res["c_star_branch"] == "dev_full"      # FULL cells present → dev-FULL c* branch
    cell_poc = df.groupby("cell_id")["poc"].mean()
    common = [c for c in cell_poc.index if c in truth.cell_quality_poc]
    r = np.corrcoef([cell_poc[c] for c in common],
                    [truth.cell_quality_poc[c] for c in common])[0, 1]
    assert r > 0.95, f"per-cell POC vs planted corr {r:.3f}"


def test_stage1_necessity_ranking_and_null():
    df, truth, _ = _stage1_poc()
    nec = {f: mixedlm.paired_contrast(df, "FULL", f"LOO-{f}", "poc") for f in syn.FACTORS}
    # C5 (negatives) and C1 (color) are the largest necessity effects (SYNTHESIS §1.9 prior)
    assert nec["C5"].estimate > nec["C1"].estimate > nec["C2"].estimate
    assert nec["C5"].pvalue < 0.01 and nec["C1"].pvalue < 0.01
    # C4 is the planted null → necessity not significant, estimate near 0
    assert nec["C4"].pvalue > 0.05 and abs(nec["C4"].estimate) < 0.12


def test_stage1_confirmatory_holm_recovers_decisions():
    df, truth, _ = _stage1_poc()
    pv = {"FULL-NEUTRAL": mixedlm.paired_contrast(df, "FULL", "NEUTRAL", "poc").pvalue,
          "FULL-BEAUTY1": mixedlm.paired_contrast(df, "FULL", "BEAUTY1", "poc").pvalue}
    for f in syn.FACTORS:
        pv[f"FULL-LOO-{f}"] = mixedlm.paired_contrast(df, "FULL", f"LOO-{f}", "poc").pvalue
        pv[f"AOI-{f}-NEUTRAL"] = mixedlm.paired_contrast(df, f"AOI-{f}", "NEUTRAL", "poc").pvalue
    res = {t.name: t.reject for t in multiplicity.confirmatory_holm(pv)}
    assert res["FULL-NEUTRAL"] and res["FULL-BEAUTY1"]
    assert res["FULL-LOO-C5"] and res["FULL-LOO-C1"]
    assert not res["FULL-LOO-C4"] and not res["AOI-C4-NEUTRAL"]   # planted null reported null


def test_stage1_factorial_recovers_interaction():
    df, truth, _ = _stage1_poc()
    dff = syn.add_factor_columns(df)
    fac = mixedlm.fit_factorial(dff, "poc")
    assert fac["rung"]
    # the planted C1×C5 synergy and C2×C3 sub-additivity are recovered with the right sign
    assert fac["coefs"]["C1:C5"]["est"] > 0 and fac["coefs"]["C1:C5"]["p"] < 0.05
    assert fac["coefs"]["C2:C3"]["est"] < 0


# --------------------------------------------------------------------------- oracle-validation previews
def test_metric_correlation_preview_has_family_blocks():
    corr, labels, bounds = syn.metric_correlation_preview(n=400, seed=0)
    assert corr.shape == (len(labels), len(labels))
    assert np.allclose(np.diag(corr), 1.0, atol=1e-6)
    # within-family pairs (first two, same 'V' family) more correlated than a cross-family pair
    within = corr[0, 1]
    cross = corr[0, labels.index("C:psi")]
    assert within > cross


def test_psi_validation_preview_clears_gate():
    human, psi, rho = syn.psi_validation_preview(n=200, rho=0.55, seed=0)
    assert len(human) == len(psi) == 200
    assert rho >= 0.40                       # admits PSI (PREREG §9 gate)


# --------------------------------------------------------------------------- agreement / reliability
def test_agreement_panels_reproduce_theory_T43():
    panels = syn.agreement_panels()
    a_sk = agreement.krippendorff_alpha(panels["skewed"], "ordinal", categories=[0, 1])
    ac_sk = agreement.gwet_ac1(panels["skewed"], categories=[0, 1])
    a_bal = agreement.krippendorff_alpha(panels["balanced"], "ordinal", categories=[0, 1])
    assert abs(a_sk - 0.444) < 0.02      # THEORY T4.3 skewed α_K
    assert abs(ac_sk - 0.878) < 0.02     # THEORY T4.3 skewed AC1
    assert abs(a_bal - 0.80) < 0.02      # THEORY T4.3 balanced α_K = AC1


def test_reliability_gate_passes_and_skew_rescue():
    units = syn.reliability_labels(seed=1)
    gate = agreement.reliability_gate(units, categories=[-2, -1, 0, 1, 2])
    assert gate["pass"] and gate["pi_max"] > 0.80
    # the T4.3 skewed panel passes specifically via the AC1-under-skew rescue rung
    sk = agreement.reliability_gate(syn.agreement_panels()["skewed"], categories=[0, 1])
    assert sk["pass"] and sk["rung"] == "ac1_skew"


def test_judgments_bt_recovers_order():
    df, truth, _ = _stage1_poc()
    scores = {"NEUTRAL": 0.0, "FULL": 1.4, "BEAUTY1": 0.6}
    prompts = list(df["prompt_id"].unique())
    J = syn.judgments_from_scores(scores, [("FULL", "NEUTRAL"), ("FULL", "BEAUTY1"),
                                           ("BEAUTY1", "NEUTRAL")], prompts, k=1.0, seed=3)
    assert bt_model.comparison_graph_connected(J)["connected"]
    fit = bt_model.fit_bt(J, reference="NEUTRAL")
    assert fit.beta["FULL"] > fit.beta["BEAUTY1"] > 0


def test_style_controlled_bt_subtracts_verbosity_bias():
    # skill-on cells are longer; the judge rewards length (pure bias) → plain BT over-credits FULL,
    # style-controlled BT subtracts it and recovers γ>0 (THEORY T5.5).
    scores = {"NEUTRAL": 0.0, "FULL": 1.3, "BEAUTY1": 0.6}
    means = {c: {"log_tok": 0.8 * s} for c, s in scores.items()}
    prompts = [f"P{i}" for i in range(40)]
    J = syn.judgments_from_scores(scores, [("FULL", "NEUTRAL"), ("FULL", "BEAUTY1"),
                                           ("BEAUTY1", "NEUTRAL")], prompts, k=1.3, style=means,
                                  style_sigma=0.5, style_bias={"log_tok": 0.6}, seed=5)
    plain = bt_model.fit_bt(J, reference="NEUTRAL")
    ctrl = bt_model.fit_bt(J, reference="NEUTRAL", style_cols=["log_tok"])
    assert plain.beta["FULL"] > ctrl.beta["FULL"] > 0     # control pulls the inflated utility down
    assert ctrl.gamma["log_tok"] > 0                       # recovers the positive length bias


# --------------------------------------------------------------------------- Stage-2 locate/extract
def test_stage2_diff_in_means_and_probes_localize():
    full, neutral, groups, labels, t2 = syn.stage2_activations(d=64, n_per_side=120, seed=0)
    peak = t2.peak_layer
    v_peak = steering.diff_in_means(full[peak].mean(0), neutral[peak].mean(0))
    assert steering.cosine(v_peak, t2.v_star) > 0.85           # in-band recovery
    v_off = steering.diff_in_means(full[0].mean(0), neutral[0].mean(0))
    assert abs(steering.cosine(v_off, t2.v_star)) < 0.4        # off-band ≈ orthogonal
    stats = probes.probe_all_layers({l: np.vstack([full[l], neutral[l]]) for l in range(28)},
                                    labels, groups, seed=0)
    assert stats[peak]["auc"] > 0.80 and stats[peak]["selectivity"] > 0.15
    assert stats[0]["auc"] < 0.65


def test_stage2_choose_band_and_stability():
    full, neutral, groups, labels, t2 = syn.stage2_activations(d=64, n_per_side=150, seed=0)
    stats = probes.probe_all_layers({l: np.vstack([full[l], neutral[l]]) for l in range(28)},
                                    labels, groups, seed=0)
    patch = syn.stage2_patching(t2.strengths)
    prec = {l: patching.percent_recovered(patch[l]["m_patched"], patch[l]["m_corrupt"],
                                          patch[l]["m_clean"]) / 100 for l in patch}
    band = probes.choose_band(stats, prec)
    assert not band["diffuse"] and t2.peak_layer in band["band"]
    diffs = [full[t2.peak_layer][i] - neutral[t2.peak_layer][i] for i in range(150)]
    stab = steering.running_mean_cosine_stability(activations.accumulate_running_means(diffs))
    assert stab["plateaued"]


# --------------------------------------------------------------------------- Stage-2 steer/verify
def test_stage2_sweep_operating_point():
    rows = syn.stage2_sweep([11, 13, 15, 17, 20], [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0])
    op = steering.select_operating_point(rows)
    assert op and op["layer"] == 15 and abs(op["rho"] - 0.3) < 1e-9
    assert op["mean_kl"] <= 0.30 and op["render_success"] >= 0.90


def test_stage2_arms_success_with_brittle_ood():
    arms, at = syn.stage2_arms(seed=0)
    al = arms[arms.arm.isin(["steered", "unsteered"])].rename(columns={"arm": "cell_id"})
    mr = mixedlm.paired_contrast(al, "steered", "unsteered", "poc")
    assert mr.estimate > 0 and mr.ci[0] > 0                    # RQ6 held-out gain, CI excludes 0
    piv = arms[arms.arm.isin(["steered", "unsteered"])].pivot_table(
        index=["prompt_id", "seed"], columns="arm", values="poc")
    overall_anti = float((piv["steered"] < piv["unsteered"]).mean())
    assert overall_anti < 0.50                                # generalizes on average (RQ7)
    assert at.anti_steerable_by_type["admin-table"] > 0.50    # one OOD type brittle (H7)


def test_stage2_correspondence_near_orthogonal_and_diagonal():
    cos, grid, labels, fams = syn.stage2_correspondence(seed=0)
    off = cos[:5, :5][~np.eye(5, dtype=bool)]
    assert np.abs(off).mean() < 0.30                           # near-orthogonal sub-vectors (H8)
    matches = sum(grid[i].argmax() == i for i in range(5))
    assert matches >= 3                                        # ≥3/5 signature match → found
