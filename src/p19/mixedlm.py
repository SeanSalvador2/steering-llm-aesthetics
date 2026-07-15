"""MixedLM wrappers + factorial design matrix (THEORY §T1-T3; PLAN §III.2/§III.6).

- `factorial_design_matrix` builds the 16x16 resolution-V model matrix [1 | A..E | 10 x 2FIs]
  from the frozen sign table and asserts rank 16 and column orthogonality (X^T X = 16 I),
  including the E = ABCD collinearity guard (never add both; THEORY T1.3).
- `alias_structure` returns the 16 alias cosets (THEORY T2.2); the parity test verifies
  every in-fraction row has product of signs = +1 (I = ABCDE) and E == ABCD.
- `fit_mixedlm` wraps statsmodels MixedLM with the preregistered convergence-fallback ladder
  (drop random slope -> REML->ML -> cluster bootstrap), recording which rung was used.
- `paired_contrast` is the within-prompt paired difference (THEORY T3.3) with a cluster bootstrap.

The factorial model (16 runs): y ~ C1+C2+C3+C4+C5 + all ten 2FIs, groups=prompt, random prompt
intercept (THEORY T3.1). NEUTRAL and the LOO cells are analyzed by direct contrast, not inside
this matrix (they are off-fraction anchors; THEORY T1.4).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from itertools import combinations
from typing import Sequence

import numpy as np
import pandas as pd

from .config import cells_config

FACTORS = ["C1", "C2", "C3", "C4", "C5"]
LETTERS = ["A", "B", "C", "D", "E"]
PAIRS = list(combinations(range(5), 2))  # 10 two-factor interactions


def factorial_cells() -> list[dict]:
    """The 16 in-fraction cells (FULL + 5 AOI + 10 F), each with its sign vector."""
    return [c for c in cells_config()["cells"] if c.get("in_fraction")]


def factorial_design_matrix() -> tuple[np.ndarray, list[str], list[str]]:
    """Build X (16x16) = [1 | xA..xE | 10 2FIs] and assert rank 16 + orthogonality (THEORY T1.3).

    Returns (X, column_names, cell_ids). Raises AssertionError on any DOE violation.
    """
    cells = factorial_cells()
    assert len(cells) == 16, f"expected 16 in-fraction cells, got {len(cells)}"
    cell_ids = [c["id"] for c in cells]
    signs = np.array([c["sign"] for c in cells], dtype=float)  # 16 x 5

    # parity: every row product = +1 (principal fraction I=ABCDE)
    assert np.allclose(signs.prod(axis=1), 1.0), "a fraction row violates I=ABCDE"
    # collinearity guard: E column == product(A,B,C,D)
    assert np.allclose(signs[:, 4], signs[:, :4].prod(axis=1)), "E != ABCD on the fraction"

    cols = [np.ones(16)]
    names = ["intercept"]
    for k in range(5):
        cols.append(signs[:, k])
        names.append(LETTERS[k])
    for (i, j) in PAIRS:
        cols.append(signs[:, i] * signs[:, j])
        names.append(LETTERS[i] + LETTERS[j])
    X = np.column_stack(cols)
    assert X.shape == (16, 16)
    rank = np.linalg.matrix_rank(X)
    assert rank == 16, f"model matrix rank {rank} != 16"
    # orthogonal saturated fraction: X^T X = 16 I
    assert np.allclose(X.T @ X, 16 * np.eye(16)), "fraction columns not orthogonal"
    return X, names, cell_ids


def alias_structure() -> dict[str, str]:
    """The 16 alias cosets via I = ABCDE (THEORY T2.2). Maps kept effect -> its alias word."""
    def _alias(word: str) -> str:
        full = set("ABCDE")
        s = set(word)
        return "".join(sorted(full ^ s)) or "I"  # multiply by ABCDE, reduce mod squares
    kept = ["I", "A", "B", "C", "D", "E"] + ["".join(p) for p in combinations("ABCDE", 2)]
    return {k: _alias(k if k != "I" else "") for k in kept}


def estimate_effects_ols(df: pd.DataFrame, metric: str) -> dict[str, float]:
    """Closed-form factorial effects via orthogonality: 2*beta = (1/8)(sum+ - sum-) (THEORY T1.5).

    df must have the metric and the sign columns C1..C5 for the 16 in-fraction cells (cell means).
    """
    X, names, cell_ids = factorial_design_matrix()
    means = df.groupby("cell_id")[metric].mean()
    y = np.array([means[c] for c in cell_ids])
    beta = (X.T @ y) / 16.0  # orthogonal LS estimate (THEORY T1.3)
    # translate DOE letters (A..E) to factor names (C1..C5) for consistency with fit_factorial
    xlate = dict(zip(LETTERS, FACTORS))

    def _name(nm: str) -> str:
        if nm == "intercept":
            return "intercept"
        return "".join(xlate[ch] for ch in nm)  # A->C1, AB->C1C2

    # report factorial "effects" = 2*beta for mains/2FIs (THEORY T1.1)
    return {_name(names[i]): (2 * beta[i] if names[i] != "intercept" else beta[i])
            for i in range(16)}


@dataclass
class MixedResult:
    estimate: float
    se: float
    pvalue: float
    rung: str
    ci: tuple[float, float]
    extra: dict = field(default_factory=dict)


def _cluster_bootstrap_contrast(df: pd.DataFrame, cellA: str, cellB: str, metric: str,
                                B: int = 2000, seed: int = 0) -> MixedResult:
    """Non-parametric floor of the ladder: cluster-bootstrap the paired within-prompt diff (T3.3)."""
    rng = np.random.default_rng(seed)
    sub = df[df["cell_id"].isin([cellA, cellB])]
    means = sub.groupby(["prompt_id", "cell_id"])[metric].mean().unstack()
    means = means.dropna(subset=[cellA, cellB]) if {cellA, cellB}.issubset(means.columns) else means
    d = (means[cellA] - means[cellB]).values
    prompts = np.arange(len(d))
    point = float(np.mean(d))
    boots = []
    for _ in range(B):
        idx = rng.choice(prompts, size=len(prompts), replace=True)
        boots.append(np.mean(d[idx]))
    boots = np.sort(boots)
    lo = float(boots[int(0.025 * len(boots))])
    hi = float(boots[min(len(boots) - 1, int(0.975 * len(boots)))])
    se = float(np.std(boots, ddof=1))
    # two-sided bootstrap p via CI inversion (fraction of boots on the other side of 0, x2)
    frac = np.mean(boots <= 0) if point > 0 else np.mean(boots >= 0)
    pval = min(1.0, 2 * frac)
    return MixedResult(point, se, pval, "cluster_bootstrap", (lo, hi))


def fit_mixedlm(df: pd.DataFrame, formula: str, groups: str,
                re_formula: str | None = "1", metric_is_binary: bool = False) -> MixedResult:
    """statsmodels MixedLM with the convergence-fallback ladder (THEORY T3.6 / PLAN §III.6).

    Ladder: (1) requested random structure -> (2) intercept-only -> (3) REML->ML. The caller uses
    paired_contrast() when even this fails (the non-parametric floor). Returns the first fixed
    effect's estimate/SE/p as a convenience for single-contrast formulas; `extra['params']` has all.
    """
    import statsmodels.formula.api as smf

    attempts = [
        ("random_slope", dict(re_formula=re_formula, reml=True)),
        ("intercept_only", dict(re_formula="1", reml=True)),
        ("intercept_ml", dict(re_formula="1", reml=False)),
    ]
    last_err = None
    for rung, kw in attempts:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                md = smf.mixedlm(formula, df, groups=df[groups], re_formula=kw["re_formula"])
                res = md.fit(reml=kw["reml"], method="lbfgs")
            fe = [n for n in res.params.index if n not in ("Intercept", "Group Var")
                  and not n.endswith("Var")]
            target = fe[0] if fe else res.params.index[0]
            est = float(res.params[target])
            se = float(res.bse[target])
            pv = float(res.pvalues[target])
            ci = res.conf_int().loc[target]
            return MixedResult(est, se, pv, rung, (float(ci[0]), float(ci[1])),
                               extra={"params": res.params.to_dict(), "target": target})
        except Exception as e:  # pragma: no cover - convergence dependent
            last_err = e
            continue
    raise RuntimeError(f"MixedLM failed all rungs: {last_err}")


def paired_contrast(df: pd.DataFrame, cellA: str, cellB: str, metric: str,
                    prefer_mixedlm: bool = True, B: int = 2000, seed: int = 0) -> MixedResult:
    """A FULL-vs-LOO / AOI-vs-NEUTRAL style contrast on a metric (THEORY T1.4/T3.3).

    Tries MixedLM (random prompt intercept) then falls back to the cluster bootstrap floor.
    """
    sub = df[df["cell_id"].isin([cellA, cellB])].copy()
    sub["is_A"] = (sub["cell_id"] == cellA).astype(int)
    if prefer_mixedlm:
        try:
            return fit_mixedlm(sub, f"{metric} ~ is_A", groups="prompt_id", re_formula="1")
        except Exception:
            pass
    return _cluster_bootstrap_contrast(df, cellA, cellB, metric, B=B, seed=seed)


def fit_factorial(df: pd.DataFrame, metric: str) -> dict:
    """Factorial model: metric ~ C1..C5 + all 10 2FIs, random prompt intercept (THEORY T1.3/T3).

    df must carry the 16 in-fraction cells with numeric sign columns C1..C5. Returns coefficient
    estimates + SEs + p-values for the 5 mains and 10 2FIs, plus the ladder rung used. Ladder
    (THEORY T3.6): MixedLM random prompt intercept -> (on convergence failure) OLS with
    prompt-clustered SEs (a valid non-parametric fallback that still respects the prompt cluster).
    """
    import statsmodels.formula.api as smf

    sub = df[df["cell_id"].isin([c["id"] for c in factorial_cells()])].copy()
    for f in FACTORS:
        sub[f] = sub[f].astype(float)
    terms = FACTORS + [f"{FACTORS[i]}:{FACTORS[j]}" for i, j in PAIRS]
    formula = f"{metric} ~ " + " + ".join(terms)

    res = None
    rung = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for opt in ("lbfgs", "bfgs", "cg", "powell"):
            try:
                res = smf.mixedlm(formula, sub, groups=sub["prompt_id"]).fit(method=opt)
                rung = f"mixedlm_{opt}"
                break
            except Exception:
                continue
    if res is None:  # fallback rung: OLS with cluster-robust (prompt) SEs
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = smf.ols(formula, sub).fit(cov_type="cluster",
                                            cov_kwds={"groups": sub["prompt_id"]})
        rung = "ols_cluster_robust"

    coefs = {}
    for t in terms:
        if t in res.params.index:
            coefs[t] = {"est": float(res.params[t]), "se": float(res.bse[t]),
                        "p": float(res.pvalues[t])}
    return {"coefs": coefs, "rung": rung, "n_obs": len(sub)}
