"""Multiple-comparison control: Holm (confirmatory) + BH (exploratory) (THEORY §T6.4; PREREG §4).

- Confirmatory family (Holm-Bonferroni, FWER=0.05), applied SEPARATELY to the POC family and the
  BT family: {FULL-NEUTRAL; 5x(FULL-LOO-Ci); 5x(AOI-Ci-NEUTRAL); FULL-BEAUTY1} = 12 tests.
- Everything else is exploratory (Benjamini-Hochberg, FDR=0.10): the 10 two-factor interactions,
  per-family metric scans, per-task-type breakdowns, F-cell preference edges, the MIXED cell.

Holm controls FWER under arbitrary dependence; BH controls FDR under PRDS (positively-correlated
metric families on shared renders — the sanctioned use-case).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

# The 12-test confirmatory family (PREREG §4), applied separately to POC and BT.
CONFIRMATORY_FAMILY = [
    "FULL-NEUTRAL",
    "FULL-LOO-C1", "FULL-LOO-C2", "FULL-LOO-C3", "FULL-LOO-C4", "FULL-LOO-C5",
    "AOI-C1-NEUTRAL", "AOI-C2-NEUTRAL", "AOI-C3-NEUTRAL", "AOI-C4-NEUTRAL", "AOI-C5-NEUTRAL",
    "FULL-BEAUTY1",
]

EXPLORATORY_FAMILIES = {
    "interactions_2fi": [f"2FI-{a}{b}" for a in "ABCDE" for b in "ABCDE" if a < b],  # 10 pairs
    "per_family_scan": [],   # filled at analysis time (metric-family contrasts)
    "per_task_type": [],     # filled at analysis time
    "f_cell_edges": [f"F-{t}-NEUTRAL" for t in
                     ["123", "124", "125", "134", "135", "145", "234", "235", "245", "345"]],
    "mixed_robustness": ["MIXED-FULL"],
}


@dataclass
class TestResult:
    name: str
    pvalue: float
    reject: bool
    adjusted_p: float


def holm(pvalues: Sequence[float], names: Sequence[str] | None = None,
         alpha: float = 0.05) -> list[TestResult]:
    """Holm-Bonferroni step-down (THEORY T6.4). Rejects H(k) while p(k) <= alpha/(m-k+1)."""
    m = len(pvalues)
    names = list(names) if names is not None else [f"H{i}" for i in range(m)]
    order = sorted(range(m), key=lambda i: pvalues[i])
    reject = [False] * m
    adj = [0.0] * m
    running_max = 0.0
    still_rejecting = True
    for rank, i in enumerate(order):
        thresh = alpha / (m - rank)
        a = min(1.0, pvalues[i] * (m - rank))
        running_max = max(running_max, a)  # adjusted p-values are monotone non-decreasing
        adj[i] = running_max
        if still_rejecting and pvalues[i] <= thresh:
            reject[i] = True
        else:
            still_rejecting = False
    return [TestResult(names[i], pvalues[i], reject[i], adj[i]) for i in range(m)]


def benjamini_hochberg(pvalues: Sequence[float], names: Sequence[str] | None = None,
                       q: float = 0.10) -> list[TestResult]:
    """Benjamini-Hochberg step-up FDR control (THEORY T6.4). k* = max{k: p(k) <= (k/m) q}."""
    m = len(pvalues)
    names = list(names) if names is not None else [f"H{i}" for i in range(m)]
    order = sorted(range(m), key=lambda i: pvalues[i])
    reject = [False] * m
    adj = [0.0] * m
    # find k*
    kstar = 0
    for rank, i in enumerate(order, start=1):
        if pvalues[i] <= (rank / m) * q:
            kstar = rank
    for rank, i in enumerate(order, start=1):
        reject[i] = rank <= kstar
    # BH adjusted p-values (monotone from the largest)
    prev = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        val = min(prev, pvalues[i] * m / rank)
        adj[i] = val
        prev = val
    return [TestResult(names[i], pvalues[i], reject[i], adj[i]) for i in range(m)]


def confirmatory_holm(pvalues_by_name: dict[str, float], alpha: float = 0.05) -> list[TestResult]:
    """Apply Holm over the frozen 12-test confirmatory family (PREREG §4).

    Raises if the supplied names are not exactly the confirmatory family (guards against silently
    testing a different set than was preregistered).
    """
    got = set(pvalues_by_name)
    want = set(CONFIRMATORY_FAMILY)
    if got != want:
        raise ValueError(f"confirmatory family mismatch: missing={want - got}, extra={got - want}")
    names = CONFIRMATORY_FAMILY
    return holm([pvalues_by_name[n] for n in names], names, alpha)
