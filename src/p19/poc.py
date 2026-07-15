"""Primary Objective Composite (POC) + metric-row assembly (THEORY §T7.10; PLAN §III.4, App B.8).

POC is a pre-registered mean of ORIENTED, z-scored core metrics over the dev-unit reference
distribution, with two frozen conditionals (part of the endpoint, NOT post-hoc; PREREG §4/§9):

  (i)  PSI-out 6-term variant  — if PSI fails its admission gate, drop the -z(PSI) term.
  (ii) c* anchor fallback      — c* = median Hasler-M of human-preferred pages iff >=30 exist,
                                 else median Hasler-M of the dev FULL-cell generations.

Render-failed units are EXCLUDED from POC (counted in family V). Both conditionals are
measurable pre-analysis, so the estimand is well-defined before any test is run; the branch that
fires is recorded in the manifest.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .config import judge_config
from . import metrics_dom, metrics_visual

# oriented core terms (name, sign); 7-term POC. The 6-term variant drops "psi".
POC_TERMS: list[tuple[str, int]] = [
    ("align_regularity", +1),
    ("whitespace_ratio", +1),
    ("type_scale_adherence", +1),
    ("contrast_pass_rate", +1),
    ("overflow_overlap", -1),
    ("psi", -1),
    ("colorfulness_dist", -1),
]


# --------------------------------------------------------------------------- row assembly

def assemble_row(render_result, png_path) -> dict[str, Any]:
    """Full metric vector for one generation unit (metrics schema columns).

    Merges the DOM metrics, the screenshot metrics, and the PSI composite. `poc` and
    `colorfulness_dist` are population-level (filled later by compute_poc).
    """
    row: dict[str, Any] = {}
    row.update(metrics_dom.compute(render_result))
    vis = metrics_visual.compute(png_path)
    row.update({k: v for k, v in vis.items() if k != "psi_hue"})
    psi = metrics_visual.psi_composite(
        hue=vis["psi_hue"],
        gradient=row.pop("psi_gradient"),
        inter=row.pop("psi_inter"),
        centered=row.pop("psi_centered"),
    )
    row.update(psi)
    row.setdefault("uiclip", -1.0)
    row.setdefault("clip_relevance", -1.0)
    return row


# --------------------------------------------------------------------------- conditionals

def resolve_psi_admission(psi_human_rho: float | None) -> bool:
    """Conditional (i): admit PSI iff Spearman rho(PSI, human 'AI' rating) >= gate (PREREG §9).

    None (no human data yet) -> provisionally admitted (7-term) but flagged for revisit.
    """
    if psi_human_rho is None:
        return True
    return psi_human_rho >= judge_config()["oracle_gates"]["psi_rho_min"]


def resolve_c_star(
    df: pd.DataFrame,
    n_human_preferred: int = 0,
    human_preferred_colorfulness: list[float] | None = None,
) -> tuple[float, str]:
    """Conditional (ii): (c*, branch) (PREREG §9 / THEORY T7.10).

    >=30 human-preferred pages -> median of their Hasler-M ('human'); else median Hasler-M of the
    dev FULL-cell generations ('dev_full'); if no FULL rows present (e.g. fixtures), fall back to
    the population median ('population') and label it so.
    """
    min_pages = judge_config()["oracle_gates"]["c_star_min_human_pages"]
    if n_human_preferred >= min_pages and human_preferred_colorfulness:
        return float(np.median(human_preferred_colorfulness)), "human"
    rendered = df[df["render_success"] == 1]
    if "cell_id" in df.columns and (rendered["cell_id"] == "FULL").any():
        full = rendered[rendered["cell_id"] == "FULL"]["colorfulness"]
        return float(np.median(full)), "dev_full"
    return float(np.median(rendered["colorfulness"])) if len(rendered) else 0.0, "population"


# --------------------------------------------------------------------------- POC

def _zscore(series: pd.Series, ref_mask: pd.Series) -> pd.Series:
    ref = series[ref_mask]
    mu, sd = ref.mean(), ref.std(ddof=0)
    if not np.isfinite(sd) or sd == 0:
        return pd.Series(0.0, index=series.index)
    return (series - mu) / sd


def compute_poc(
    df: pd.DataFrame,
    psi_admit: bool = True,
    c_star: float | None = None,
    c_star_kwargs: dict | None = None,
) -> dict[str, Any]:
    """Compute POC per row over the dev-unit reference (THEORY T7.10).

    Returns {"poc": pd.Series (NaN for render-failed), "c_star": float, "c_star_branch": str,
    "n_terms": int, "psi_admit": bool, "terms": [...]}. Render-failed / non-hermetic units
    (render_success==0) are excluded from POC and the z-score reference.
    """
    df = df.copy()
    ref_mask = df["render_success"] == 1

    # derived terms
    df["contrast_pass_rate"] = 1.0 - df["contrast_frac_below_4_5"]
    df["overflow_overlap"] = df["n_overflow"] + df["n_overlap"]
    if c_star is None:
        c_star, branch = resolve_c_star(df, **(c_star_kwargs or {}))
    else:
        branch = "explicit"
    df["colorfulness_dist"] = (df["colorfulness"] - c_star).abs()

    terms = [t for t in POC_TERMS if not (t[0] == "psi" and not psi_admit)]
    acc = pd.Series(0.0, index=df.index)
    for name, sign in terms:
        acc = acc + sign * _zscore(df[name], ref_mask)
    poc = acc / len(terms)
    poc = poc.where(ref_mask, other=np.nan)  # render-failed excluded
    return {
        "poc": poc,
        "c_star": c_star,
        "c_star_branch": branch,
        "n_terms": len(terms),
        "psi_admit": psi_admit,
        "terms": [t[0] for t in terms],
    }


def add_poc_column(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Return df with a filled 'poc' column (convenience wrapper)."""
    out = df.copy()
    res = compute_poc(df, **kwargs)
    out["poc"] = res["poc"].values
    return out
