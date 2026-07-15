"""Synthetic-data generators with KNOWN ground truth (PLAN §V.3 dry-runs; CLAUDE.md analysis discipline).

The executed notebooks cannot run the subject model (compute policy), so the not-yet-runnable parts
are validated by SYNTHETIC DRY-RUNS: generate results with a *planted* ground truth, then push them
through the FULL real analysis pipeline (POC → MixedLM → BT → Holm/BH → figures; diff-in-means →
probes → patching → steering verification) and confirm the pipeline recovers the plant. Every number
these functions emit is simulated; on Colab the real generations/activations replace them (RUNBOOK).

The plants are internally consistent with the theory:
  * Stage-1 uses one multilinear factorial model on a latent quality (THEORY T1.1), so necessity,
    sufficiency, mains and 2FIs all fall out of ONE coefficient vector and satisfy the T1.7 identity.
  * The latent is expressed through the seven POC input metrics so `poc.compute_poc` recovers it.
  * Stage-2 plants a single mid-band direction (THEORY T8.2) that diff-in-means/probes/patching find,
    a non-monotone dose-response (H7), a four-arm verification with a known reproduction fraction, and
    near-orthogonal component sub-vectors (H8).

Nothing here is heavy: pure numpy + pandas, deterministic under `seed`. It is unit-tested
(tests/test_synthetic.py) against the real pipeline so the dry-runs the notebooks show are trustworthy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Sequence

import numpy as np
import pandas as pd

from .config import cells_config, prompts_config
from .bt_model import Judgment

FACTORS = ["C1", "C2", "C3", "C4", "C5"]


# =========================================================================== Stage-1 planted plant

# Regression COEFFICIENTS β (THEORY T1.1; factorial main effect = 2β, 2FI = 2β_ij). Planted priors
# from SYNTHESIS §1.9: C5 (negatives) largest, C1 (color) second, C4 (patterns) ≈ null; one positive
# C1×C5 synergy ("negatives help more once a palette is set") and a mild negative C2×C3.
DEFAULT_BETA = {"C1": 0.21, "C2": 0.15, "C3": 0.11, "C4": 0.0, "C5": 0.30}  # C4 = planted null
DEFAULT_BETA2 = {("C1", "C5"): 0.12, ("C2", "C3"): -0.05}

# The seven oriented POC terms (poc.POC_TERMS) and how each is generated from the latent quality L.
# sign = +1 higher-better, -1 lower-better (compute_poc applies the orientation).


@dataclass
class Stage1Truth:
    beta: dict
    beta2: dict
    main_effects: dict            # 2β per component (factorial main effect, POC units)
    twofi: dict                   # 2β_ij per pair (POC units)
    cell_quality_raw: dict        # latent q_c per cell (pre-standardization)
    cell_quality_poc: dict        # q_c expressed in recovered-POC units (÷ sd of latent over dev ref)
    necessity: dict               # Nec_i = q_FULL - q_LOO-Ci  (POC units)
    sufficiency: dict             # Suff_i = q_AOI-Ci - q_NEUTRAL (POC units)
    full_neutral_gap: float
    beauty_frac: float
    null_component: str
    sd_latent: float


def _cell_quality(sign: list[int] | None, beta: dict, beta2: dict) -> float:
    """Evaluate the multilinear factorial model q(x)=Σβᵢxᵢ+Σβᵢⱼxᵢxⱼ at a sign vector (THEORY T1.1)."""
    if sign is None:
        return 0.0
    q = 0.0
    for i, f in enumerate(FACTORS):
        q += beta[f] * sign[i]
    for (a, b), c in beta2.items():
        ia, ib = FACTORS.index(a), FACTORS.index(b)
        q += c * sign[ia] * sign[ib]
    return q


def stage1_dataset(
    n_prompts: int = 40, seed: int = 0, beta: dict | None = None, beta2: dict | None = None,
    sigma_prompt: float = 0.28, sigma_seed: float = 0.42, render_fail_rate: float = 0.03,
    beauty_frac: float = 0.45,
) -> tuple[pd.DataFrame, Stage1Truth]:
    """Planted Stage-1 metric table + ground truth (PLAN §III; feeds notebook 05).

    Builds a latent quality q_c per cell from ONE factorial coefficient vector, adds a random prompt
    intercept and seed noise (THEORY T3.1), and renders the seven POC input metrics so
    `poc.compute_poc` recovers the latent. Returns (metrics_df, truth). C4 is the planted null; the
    C1×C5 2FI is the planted interaction. Dev prompts only (the factorial + LOO + AOI live on dev).
    """
    beta = dict(beta or DEFAULT_BETA)
    beta2 = dict(beta2 or DEFAULT_BETA2)
    rng = np.random.default_rng(seed)

    cells = cells_config()["cells"]
    # dev prompt ids (frozen) — use the first n_prompts
    dev_ids = prompts_config()["split_freeze"]["dev"][:n_prompts]

    # latent per-cell quality
    q_raw: dict[str, float] = {}
    for c in cells:
        q_raw[c["id"]] = _cell_quality(c.get("sign"), beta, beta2)
    gap = q_raw["FULL"] - q_raw["NEUTRAL"]
    # controls without factor slots: place BEAUTY1 between, NOSYS just below NEUTRAL (RQ4 order)
    q_raw["BEAUTY1"] = q_raw["NEUTRAL"] + beauty_frac * gap
    q_raw["NOSYS"] = q_raw["NEUTRAL"] - 0.10 * gap

    # prompt random intercepts (shared across cells within a prompt — the pairing structure T3.3)
    u_p = {pid: rng.normal(0, sigma_prompt) for pid in dev_ids}

    rows = []
    latent_ref = []  # latent values over would-be dev-reference units (render_success==1) for sd
    for c in cells:
        cid = c["id"]
        seeds = list(range(c["seeds"]))
        for pid in dev_ids:
            for s in seeds:
                L = q_raw[cid] + u_p[pid] + rng.normal(0, sigma_seed)
                render_success = int(rng.random() > render_fail_rate)
                rows.append({"cell_id": cid, "prompt_id": pid, "seed": s, "split": "dev",
                             "render_success": render_success, "_latent": L})
                if render_success:
                    latent_ref.append(L)
    sd_latent = float(np.std(latent_ref, ddof=0)) or 1.0

    # render the latent into the 7 oriented POC metrics (+ a few extra family metrics for the BH scan)
    df = pd.DataFrame(rows)
    L = df["_latent"].values
    tiny = lambda scale: rng.normal(0, scale, len(df))  # noqa: E731  per-term idiosyncratic noise
    # higher-better
    df["align_regularity"] = 0.20 + 0.15 * L + tiny(0.03)
    df["whitespace_ratio"] = np.clip(0.45 + 0.10 * L + tiny(0.03), 0, 1)
    df["type_scale_adherence"] = np.clip(0.60 + 0.12 * L + tiny(0.03), 0, 1)
    contrast_pass = np.clip(0.82 + 0.14 * L + tiny(0.03), 0, 1)
    df["contrast_frac_below_4_5"] = 1.0 - contrast_pass
    # lower-better counts (Poisson mean shrinks with quality; floored at 0 as real counts are)
    df["n_overflow"] = rng.poisson(np.clip(0.9 - 0.5 * L, 0.02, None))
    df["n_overlap"] = rng.poisson(np.clip(0.8 - 0.45 * L, 0.02, None))
    # lower-better PSI
    df["psi"] = np.clip(0.34 - 0.12 * L + tiny(0.02), 0, 1)
    df["psi_hue"] = np.clip(0.10 - 0.05 * L + tiny(0.01), 0, 1)
    # colorfulness: moderate-optimum, LINEAR in quality. FULL centers at c*; worse cells drift
    # garish (higher M), so |M - c*| is (near-)linear decreasing in quality across cells.
    qfull = q_raw["FULL"]
    df["colorfulness"] = 18.0 + 7.0 * (qfull - L) + tiny(0.6)
    # extra family metrics (family L / T / C) for the per-family concordance scan (BH)
    df["ngo_balance"] = np.clip(0.55 + 0.10 * L + tiny(0.04), 0, 1)
    df["n_font_families"] = np.clip(np.round(3.0 - 0.4 * L + tiny(0.2)), 1, 8).astype(int)
    df["figure_ground"] = np.clip(0.40 + 0.08 * L + tiny(0.03), 0, 1)

    df = df.drop(columns=["_latent"])

    main = {f: 2 * beta[f] / sd_latent for f in FACTORS}
    twofi = {p: 2 * v / sd_latent for p, v in beta2.items()}
    q_poc = {k: v / sd_latent for k, v in q_raw.items()}
    nec = {f: (q_raw["FULL"] - q_raw[f"LOO-{f}"]) / sd_latent for f in FACTORS}
    suff = {f: (q_raw[f"AOI-{f}"] - q_raw["NEUTRAL"]) / sd_latent for f in FACTORS}
    null_component = min(main, key=lambda k: abs(main[k]))

    truth = Stage1Truth(
        beta=beta, beta2=beta2, main_effects=main, twofi=twofi, cell_quality_raw=q_raw,
        cell_quality_poc=q_poc, necessity=nec, sufficiency=suff, full_neutral_gap=gap / sd_latent,
        beauty_frac=beauty_frac, null_component=null_component, sd_latent=sd_latent,
    )
    return df, truth


def add_factor_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Attach numeric ±1 sign columns C1..C5 (needed by mixedlm.fit_factorial) from cells.yaml."""
    from .config import cells_by_id
    cbi = cells_by_id()
    out = df.copy()
    for i, f in enumerate(FACTORS):
        out[f] = out["cell_id"].map(lambda cid, i=i: (cbi[cid].get("sign") or [np.nan] * 5)[i])
    return out


# =========================================================================== oracle-validation previews

def metric_correlation_preview(n: int = 600, seed: int = 0) -> tuple[np.ndarray, list[str], list[int]]:
    """Planted metric table with FAMILY-BLOCK correlation structure (F4 preview; PLAN §III.3.1).

    Twelve objective metrics across the six families share a weak global quality latent (cross-family
    correlation) plus a strong per-family latent (within-family redundancy). Returns (Spearman corr
    matrix, labels, family_bounds) so figures.metric_correlation_matrix draws the block structure the
    real F4 exposes on 4,630 renders — redundant metrics cluster; families stay distinguishable.
    """
    from scipy.stats import spearmanr
    rng = np.random.default_rng(seed)
    families = {
        "V": ["overflow", "overlap"], "A": ["contrast_frac", "contrast_min"],
        "L": ["ngo_balance", "align_reg", "whitespace"], "T": ["n_sizes", "type_scale"],
        "C": ["colorfulness", "psi"], "X": ["visual_complexity"],
    }
    labels, cols, bounds, cum = [], [], [], 0
    g = rng.standard_normal(n)  # global quality latent
    for fam, mets in families.items():
        fl = rng.standard_normal(n)  # family latent
        for m in mets:
            x = 0.30 * g + 0.80 * fl + 0.45 * rng.standard_normal(n)
            cols.append(x)
            labels.append(f"{fam}:{m}")
        cum += len(mets)
        bounds.append(cum)
    X = np.column_stack(cols)
    corr, _ = spearmanr(X)
    return np.asarray(corr), labels, bounds[:-1]


def psi_validation_preview(n: int = 120, rho: float = 0.55, seed: int = 0) -> tuple:
    """Planted (PSI, human 'AI-generated' rating) pairs for the F10 oracle gate (PLAN §III.3.1).

    Human rating is 1–5; PSI ∈ [0,1] is generated to correlate at ≈`rho` (Spearman), above the 0.40
    admission gate. Returns (human_rating, psi, realized_spearman). On Colab the real pairs come from
    the human-labeled subset.
    """
    from scipy.stats import spearmanr
    rng = np.random.default_rng(seed)
    latent = rng.standard_normal(n)
    human = np.clip(np.round(3 + 1.2 * latent + rng.normal(0, 0.6, n)), 1, 5)
    noise = rng.standard_normal(n)
    psi = np.clip(0.35 + 0.18 * latent + 0.16 * noise, 0, 1)
    realized = spearmanr(human, psi).statistic
    return human, psi, float(realized)


# =========================================================================== agreement / reliability

def agreement_panels() -> dict[str, list[dict]]:
    """THEORY §T4.3 exact kappa-paradox micro-example (N=100 binary items, p_o=0.90).

    Returns {"skewed": units, "balanced": units} where a unit is {"r1": cat, "r2": cat}. The skewed
    panel yields α_K≈0.444 / AC1≈0.878; the balanced panel yields α_K=AC1=0.80 (F11 exemplar).
    """
    def _panel(both1, both0, a_only, b_only):
        units = []
        units += [{"r1": 1, "r2": 1} for _ in range(both1)]
        units += [{"r1": 0, "r2": 0} for _ in range(both0)]
        units += [{"r1": 1, "r2": 0} for _ in range(a_only)]
        units += [{"r1": 0, "r2": 1} for _ in range(b_only)]
        return units
    return {
        "skewed": _panel(85, 5, 5, 5),      # π1=0.90 → α_K=0.444, AC1=0.878
        "balanced": _panel(45, 45, 5, 5),   # π1=0.50 → α_K=AC1=0.80
    }


def reliability_labels(n: int = 100, agreement: float = 0.82, skew: float = 0.88,
                       seed: int = 0) -> list[dict]:
    """Synthetic judge-vs-human paired labels over an ordinal preference scale (PREREG §5; F11).

    Each unit = {"judge": cat, "human": cat} on categories [-2,-1,0,1,2] (A≫..tie..B≫). A fraction
    `skew` of items are the SAME dominant outcome (the skill usually wins → +2), the rest spread over
    the other levels; judge and human agree on a fraction `agreement`, disagreements land on an
    adjacent level. Tuned so π_max ≳ 0.80 depresses α_K below the 0.667 gate while AC1 clears 0.80 —
    the disjunctive-gate rescue path (THEORY T4.4 demonstrable-skew branch).
    """
    rng = np.random.default_rng(seed)
    units = []
    for _ in range(n):
        # dominant outcome under skew is a single category (a decisive A-win) → true kappa-paradox skew
        human = 2 if rng.random() < skew else int(rng.choice([-2, -1, 0, 1]))
        if rng.random() < agreement:
            judge = human
        else:
            # 30% of disagreements land two levels away → depresses the ordinal α_K further, while
            # AC1's skew-robust chance model holds (the rescue the disjunctive gate is designed for)
            step = int(rng.choice([-1, 1])) * (2 if rng.random() < 0.30 else 1)
            judge = int(np.clip(human + step, -2, 2))
        units.append({"judge": judge, "human": human})
    return units


# =========================================================================== preference judgments

def judgments_from_scores(scores: dict[str, float], edges: Sequence[tuple[str, str]],
                          prompts: Sequence[str], k: float = 1.0, tie_margin: float = 0.25,
                          style: dict[str, dict] | None = None, seed: int = 0,
                          reference: str = "NEUTRAL", style_sigma: float = 0.0,
                          style_bias: dict[str, float] | None = None) -> list[Judgment]:
    """Sample Bradley-Terry-consistent pairwise judgments from latent cell scores (THEORY T5.1/T5.4).

    For each (edge, prompt): P(A≻B)=σ(k·(sᴬ−sᴮ) + Σγ_bias·(styleᴬ−styleᴮ)); a |Δquality|<tie_margin
    band produces ties (the Davidson tie mass). `style` maps cell→covariate MEANS. With
    `style_sigma>0` each judgment draws per-page style around those means (within-cell variation, so a
    style-controlled BT can *identify* γ). `style_bias` maps covariate→the weight the JUDGE applies —
    a pure bias channel (e.g. verbosity) the style-controlled BT should subtract (THEORY T5.5).
    Used by notebook 03 (BT utilities), 05 (style control), 07a (steering preference).
    """
    rng = np.random.default_rng(seed)
    style = style or {}
    style_bias = style_bias or {}
    covs = sorted({c for d in style.values() for c in d} | set(style_bias))
    out: list[Judgment] = []
    for (a, b) in edges:
        for pid in prompts:
            sA = {c: style.get(a, {}).get(c, 0.0) + (rng.normal(0, style_sigma) if style_sigma else 0.0)
                  for c in covs}
            sB = {c: style.get(b, {}).get(c, 0.0) + (rng.normal(0, style_sigma) if style_sigma else 0.0)
                  for c in covs}
            dq = scores.get(a, 0.0) - scores.get(b, 0.0)
            dstyle = sum(style_bias.get(c, 0.0) * (sA[c] - sB[c]) for c in covs)
            if abs(dq) < tie_margin and rng.random() < 0.5:
                outcome = "tie"
            else:
                p_a = 1.0 / (1.0 + np.exp(-(k * dq + dstyle)))
                outcome = "A" if rng.random() < p_a else "B"
            out.append(Judgment(cellA=a, cellB=b, prompt=pid, outcome=outcome, styleA=sA, styleB=sB))
    return out


# =========================================================================== Stage-2 locate/extract

@dataclass
class Stage2LocateTruth:
    v_star: np.ndarray
    band: tuple
    peak_layer: int
    strengths: dict            # layer -> planted signal strength
    d: int
    n_layers: int


def stage2_activations(d: int = 256, n_layers: int = 28, n_per_side: int = 100,
                       band: tuple = (11, 20), peak: int = 15, strength: float = 4.0,
                       sigma: float = 0.9, prompt_sigma: float = 1.2,
                       seed: int = 0) -> tuple[dict, dict, np.ndarray, np.ndarray, Stage2LocateTruth]:
    """Planted mid-band design direction in synthetic residuals (THEORY T8.2; feeds notebook 06a).

    NOTE: small d for CPU speed; the real model is d=3584, L=28 (explicit in the notebook). Each of
    `n_per_side` prompts contributes one FULL and one NEUTRAL mean-response vector per layer. The
    planted unit direction v* is injected at layer ℓ with a Gaussian-in-depth strength peaking at
    `peak` (≈0 outside `band`); a per-prompt nuisance vector (shared FULL/NEUTRAL) is the "writing
    HTML" content diff-in-means cancels. Returns:
      full[l], neutral[l]  : [n_per_side, d] arrays
      groups               : [2*n_per_side] prompt ids (FULL block then NEUTRAL block)
      labels               : [2*n_per_side] 1=FULL, 0=NEUTRAL
      truth                : Stage2LocateTruth
    """
    rng = np.random.default_rng(seed)
    v_star = rng.standard_normal(d)
    v_star /= np.linalg.norm(v_star)
    lo, hi = band

    def _strength(l: int) -> float:
        # flat-top plateau across the band [lo, hi] with a quick Gaussian taper outside, so the
        # signal is decodable across a CONTIGUOUS mid-band (H5), not a single sharp peak.
        if lo <= l <= hi:
            return strength
        dist = (lo - l) if l < lo else (l - hi)
        return float(strength * np.exp(-(dist ** 2) / (2 * 1.2 ** 2)))

    strengths = {l: _strength(l) for l in range(n_layers)}
    # per-prompt shared nuisance direction (cancels in FULL-NEUTRAL)
    prompt_vecs = rng.standard_normal((n_per_side, d)) * prompt_sigma

    full: dict[int, np.ndarray] = {}
    neutral: dict[int, np.ndarray] = {}
    for l in range(n_layers):
        s = strengths[l]
        base_f = prompt_vecs + rng.standard_normal((n_per_side, d)) * sigma
        base_n = prompt_vecs + rng.standard_normal((n_per_side, d)) * sigma
        full[l] = base_f + s * v_star  # FULL side carries the planted concept
        neutral[l] = base_n
    groups = np.array(list(range(n_per_side)) + list(range(n_per_side)))
    labels = np.array([1] * n_per_side + [0] * n_per_side)
    truth = Stage2LocateTruth(v_star=v_star, band=band, peak_layer=peak, strengths=strengths,
                              d=d, n_layers=n_layers)
    return full, neutral, groups, labels, truth


def stage2_patching(strengths: dict, seed: int = 0, base: float = 1.0,
                    recover_scale: float = 0.9) -> dict[int, dict]:
    """Planted denoising-patch scalars per layer (THEORY T8.6; feeds notebook 06a patching demo).

    Returns layer -> {m_clean, m_corrupt, m_patched} such that patching.percent_recovered tracks the
    per-layer signal strength (≥25% inside the band, ≈0 outside). The design-token logit-diff proxy
    is what these scalars stand in for on Colab.
    """
    rng = np.random.default_rng(seed)
    mx = max(strengths.values()) or 1.0
    out = {}
    for l, s in strengths.items():
        frac = recover_scale * (s / mx)
        noise = rng.normal(0, 0.02)
        m_corrupt = base
        m_clean = base + 1.0
        m_patched = base + max(0.0, frac + noise)
        out[l] = {"m_clean": m_clean, "m_corrupt": m_corrupt, "m_patched": m_patched}
    return out


# =========================================================================== Stage-2 steer / verify

def stage2_sweep(layers: Sequence[int], rhos: Sequence[float], opt_layer: int = 15,
                 opt_rho: float = 0.3, seed: int = 0) -> list[dict]:
    """Planted dev sweep grid over (layer, ρ) with a guardrail-satisfying optimum (PLAN S2.3; F6/F7).

    Each row: {layer, rho, poc_gain, mean_kl, render_success}. POC-gain rises to `opt_rho` then breaks
    down (non-monotone, H7); KL grows with ρ; render-success falls below the 0.90 floor at high ρ.
    steering.select_operating_point should recover (opt_layer, opt_rho).
    """
    rng = np.random.default_rng(seed)
    rows = []
    for L in layers:
        layer_fac = np.exp(-((L - opt_layer) ** 2) / (2 * 3.0 ** 2))  # depth tuning
        for r in rhos:
            rise = (r / opt_rho) * np.exp(1 - r / opt_rho)             # peaks at opt_rho, →0
            breakdown = 4.0 * max(0.0, r - 0.6) ** 2                   # high-ρ collapse
            gain = 0.6 * layer_fac * rise - breakdown + rng.normal(0, 0.01)
            mean_kl = 0.5 * r ** 1.4 + rng.normal(0, 0.005)
            render = float(np.clip(1.0 - 1.6 * max(0.0, r - 0.5) ** 2, 0, 1))
            rows.append({"layer": int(L), "rho": float(r), "poc_gain": float(gain),
                         "mean_kl": float(max(0.0, mean_kl)), "render_success": render})
    return rows


@dataclass
class Stage2ArmsTruth:
    skill_gap: float
    reproduce_frac: float
    reproduce_frac_seen: float
    reproduce_frac_unseen: float
    task_types: dict
    anti_steerable_by_type: dict


def stage2_arms(reproduce_frac: float = 0.6, skill_gap: float = 0.9, sigma_prompt: float = 0.30,
                sigma_seed: float = 0.30, n_seed: int = 6, seed: int = 0,
                random_k: int = 5) -> tuple[pd.DataFrame, Stage2ArmsTruth]:
    """Planted four-arm held-out verification (PLAN S2.4; feeds notebook 07a; F8/F12).

    Uses the frozen held-out prompt ids (8 seen-type + 10 unseen-type). Arms per (prompt, seed):
      unsteered ≈ base ; steered ≈ base + reproduce_frac·skill_gap ; FULL ≈ base + skill_gap ;
      random×k ≈ base (norm-matched control, no gain). Unseen (OOD) types get a wider anti-steerable
      tail (H7), with one type pushed above the 50% brittleness line. Returns (long_df, truth).
    """
    rng = np.random.default_rng(seed)
    pcfg = prompts_config()
    seen = pcfg["split_freeze"]["heldout_seen"]
    unseen = pcfg["split_freeze"]["heldout_unseen"]
    by_id = {p["id"]: p for p in pcfg["prompts"]}
    prompts = seen + unseen

    # OOD types steer less reliably (H7). Admin-data-tables are the hardest — data-dense layouts
    # unlike the marketing-oriented dev types — steering barely helps and tips them just over the
    # 50% brittleness line (the honest failure map), while settings partially resists. Seen types
    # and the overall held-out gain stay clearly positive (RQ6 success + RQ7 caveat coexist).
    type_rf = {"admin-table": -0.03, "settings": 0.50}

    rows = []
    task_types = {}
    for pid in prompts:
        ptype = by_id[pid]["type"]
        is_unseen = pid in unseen
        task_types[pid] = ptype
        u_p = rng.normal(0, sigma_prompt)
        # OOD prompts steer less reliably: lower effective reproduce fraction + heavier tail
        eff_rf = reproduce_frac * (type_rf.get(ptype, 0.55) if is_unseen else 1.0)
        tail = 0.45 if is_unseen else 0.28
        for s in range(n_seed):
            base = u_p + rng.normal(0, sigma_seed)
            unsteered = base
            full = base + skill_gap + rng.normal(0, sigma_seed)
            steered = base + eff_rf * skill_gap + rng.normal(0, tail)
            rows.append({"prompt_id": pid, "seed": s, "arm": "unsteered", "poc": unsteered,
                         "task_type": ptype, "split": "unseen" if is_unseen else "seen"})
            rows.append({"prompt_id": pid, "seed": s, "arm": "steered", "poc": steered,
                         "task_type": ptype, "split": "unseen" if is_unseen else "seen"})
            rows.append({"prompt_id": pid, "seed": s, "arm": "full_ref", "poc": full,
                         "task_type": ptype, "split": "unseen" if is_unseen else "seen"})
            for kk in range(random_k):
                rnd = base + rng.normal(0, 0.12)
                rows.append({"prompt_id": pid, "seed": s, "arm": "random", "poc": rnd,
                             "task_type": ptype, "split": "unseen" if is_unseen else "seen",
                             "random_idx": kk})
    df = pd.DataFrame(rows)

    # anti-steerable fraction by type (steered POC < unsteered POC), from the realized draws
    anti = {}
    piv = df[df["arm"].isin(["steered", "unsteered"])].pivot_table(
        index=["prompt_id", "seed"], columns="arm", values="poc")
    piv = piv.reset_index()
    piv["type"] = piv["prompt_id"].map(task_types)
    for t, g in piv.groupby("type"):
        anti[t] = float((g["steered"] < g["unsteered"]).mean())

    # realized reproduction fraction per split (partial OOD generalization, H7/RQ7)
    def _rf(split):
        sub = df[(df.split == split) & df.arm.isin(["steered", "unsteered", "full_ref"])]
        p = sub.pivot_table(index=["prompt_id", "seed"], columns="arm", values="poc")
        denom = p["full_ref"].mean() - p["unsteered"].mean()
        return float("nan") if denom == 0 else 100.0 * (p["steered"].mean() - p["unsteered"].mean()) / denom
    truth = Stage2ArmsTruth(
        skill_gap=skill_gap, reproduce_frac=reproduce_frac,
        reproduce_frac_seen=_rf("seen"), reproduce_frac_unseen=_rf("unseen"),
        task_types=task_types, anti_steerable_by_type=anti)
    return df, truth


def stage2_correspondence(seed: int = 0, off_diag: float = 0.18, match_strength: float = 0.75,
                          d: int = 256) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """Planted RQ8 correspondence: near-orthogonal component sub-vectors + a diagonal signature grid.

    Returns (cos_matrix 6×6 over {v_C1..v_C5, v_full}, signature_grid 5×5 steer×ablation family,
    labels, family_labels). Off-diagonal cosines ~ `off_diag` (<0.3 near-orthogonal); the signature
    grid is diagonally dominant (≥3/5 argmax on the diagonal → "correspondence found").
    """
    rng = np.random.default_rng(seed)
    # 5 nearly-orthogonal unit sub-vectors: start orthonormal, add small shared drift
    Q, _ = np.linalg.qr(rng.standard_normal((d, 5)))
    subs = Q[:, :5].T.copy()
    drift = rng.standard_normal(d)
    drift /= np.linalg.norm(drift)
    subs = subs + off_diag * drift  # inject a shared component → off-diagonal cosine ≈ off_diag
    subs = np.array([v / np.linalg.norm(v) for v in subs])
    v_full = subs.mean(axis=0)
    v_full /= np.linalg.norm(v_full)
    allv = np.vstack([subs, v_full])
    cos = allv @ allv.T
    labels = ["v_C1", "v_C2", "v_C3", "v_C4", "v_C5", "v_full"]

    # signature grid: component i steers family i most (diagonal), with noise; C4 (null) weaker
    fam_labels = ["color", "layout", "typography", "patterns", "restraint"]
    grid = rng.uniform(0.05, 0.30, (5, 5))
    for i in range(5):
        grid[i, i] = match_strength * (0.5 if i == 3 else 1.0) + rng.uniform(0, 0.1)
    grid = np.clip(grid, 0, 1)
    return cos, grid, labels, fam_labels
