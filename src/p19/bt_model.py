"""Style-controlled Bradley-Terry with Davidson ties (THEORY §T5; PLAN §III.5).

Per-page merit m = beta_cell + gamma^T s_page (style covariates s remove the judge's
length/verbosity/colorfulness biases; THEORY T5.4). Davidson tie term nu (THEORY T5.2):

    P(A>B) = e^{mA} / D,  P(tie) = nu e^{(mA+mB)/2} / D,  P(B>A) = e^{mB} / D,
    D = e^{mA} + e^{mB} + nu e^{(mA+mB)/2}.

Reference cell NEUTRAL has beta=0 (identifiability, THEORY T5.3). Estimation = convex MLE.
CIs by cluster bootstrap over prompts (THEORY T3.5). A connectivity checker enforces Ford's
condition (THEORY T5.3) so the MLE exists (the hub graph guarantees it, PLAN §III.5).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
from scipy.optimize import minimize

REFERENCE_CELL = "NEUTRAL"


@dataclass
class Judgment:
    cellA: str
    cellB: str
    prompt: str
    outcome: str  # "A" | "B" | "tie"
    styleA: dict = field(default_factory=dict)
    styleB: dict = field(default_factory=dict)


@dataclass
class BTFit:
    beta: dict[str, float]           # cell -> strength (reference = 0)
    gamma: dict[str, float]          # style covariate -> coefficient
    nu: float                        # Davidson tie parameter
    cells: list[str]
    style_cols: list[str]
    loglik: float
    converged: bool

    def utility(self, cell: str) -> float:
        return self.beta.get(cell, 0.0)

    def contrast(self, cell_i: str, cell_j: str) -> float:
        return self.utility(cell_i) - self.utility(cell_j)


def _prep(judgments: Sequence[Judgment], reference: str, style_cols: Sequence[str]):
    cells = sorted({j.cellA for j in judgments} | {j.cellB for j in judgments})
    if reference in cells:
        cells = [reference] + [c for c in cells if c != reference]
    free_cells = [c for c in cells if c != reference]
    cidx = {c: i for i, c in enumerate(free_cells)}  # index into beta params (reference excluded)
    p = len(style_cols)

    A_idx, B_idx = [], []
    SA = np.zeros((len(judgments), p))
    SB = np.zeros((len(judgments), p))
    outcome = np.zeros(len(judgments), dtype=np.int8)  # 0=A,1=B,2=tie
    for r, j in enumerate(judgments):
        A_idx.append(cidx.get(j.cellA, -1))
        B_idx.append(cidx.get(j.cellB, -1))
        for k, sc in enumerate(style_cols):
            SA[r, k] = j.styleA.get(sc, 0.0)
            SB[r, k] = j.styleB.get(sc, 0.0)
        outcome[r] = {"A": 0, "B": 1, "tie": 2}[j.outcome]
    return cells, free_cells, np.array(A_idx), np.array(B_idx), SA, SB, outcome


def fit_bt(judgments: Sequence[Judgment], reference: str = REFERENCE_CELL,
           style_cols: Sequence[str] | None = None) -> BTFit:
    """MLE fit of the style-controlled Davidson BT model (THEORY T5)."""
    style_cols = list(style_cols or [])
    cells, free_cells, A_idx, B_idx, SA, SB, outcome = _prep(judgments, reference, style_cols)
    n_free = len(free_cells)
    p = len(style_cols)

    def merits(theta):
        beta = theta[:n_free]
        gamma = theta[n_free:n_free + p]
        log_nu = theta[-1]
        mA = np.where(A_idx >= 0, beta[np.clip(A_idx, 0, None)], 0.0) + SA @ gamma
        mB = np.where(B_idx >= 0, beta[np.clip(B_idx, 0, None)], 0.0) + SB @ gamma
        # zero out reference contributions (A_idx==-1 -> beta 0)
        mA = np.where(A_idx >= 0, mA, SA @ gamma)
        mB = np.where(B_idx >= 0, mB, SB @ gamma)
        return mA, mB, log_nu

    def nll(theta):
        mA, mB, log_nu = merits(theta)
        nu = math.exp(log_nu)
        # stable log-sum-exp of {mA, mB, log_nu + (mA+mB)/2}
        t = log_nu + 0.5 * (mA + mB)
        M = np.maximum(np.maximum(mA, mB), t)
        logD = M + np.log(np.exp(mA - M) + np.exp(mB - M) + np.exp(t - M))
        ll = np.where(outcome == 0, mA - logD,
                      np.where(outcome == 1, mB - logD, t - logD))
        return -np.sum(ll)

    theta0 = np.zeros(n_free + p + 1)
    res = minimize(nll, theta0, method="L-BFGS-B")
    theta = res.x
    beta = {reference: 0.0}
    for c, i in zip(free_cells, range(n_free)):
        beta[c] = float(theta[i])
    gamma = {sc: float(theta[n_free + k]) for k, sc in enumerate(style_cols)}
    nu = float(math.exp(theta[-1]))
    return BTFit(beta=beta, gamma=gamma, nu=nu, cells=cells, style_cols=style_cols,
                 loglik=float(-res.fun), converged=bool(res.success))


def comparison_graph_connected(judgments: Sequence[Judgment]) -> dict:
    """Strong-connectivity check of the win digraph (Ford's condition; THEORY T5.3).

    Arc i->j when i beats j at least once (ties contribute both directions weakly). Returns
    {connected, n_cells, n_components}. A disconnected graph -> BT MLE may diverge.
    """
    cells = sorted({j.cellA for j in judgments} | {j.cellB for j in judgments})
    idx = {c: i for i, c in enumerate(cells)}
    n = len(cells)
    adj = [set() for _ in range(n)]
    for j in judgments:
        a, b = idx[j.cellA], idx[j.cellB]
        if j.outcome == "A":
            adj[a].add(b)
        elif j.outcome == "B":
            adj[b].add(a)
        else:  # tie -> weak both-direction connectivity
            adj[a].add(b)
            adj[b].add(a)

    def _reachable(start, graph):
        seen = {start}
        stack = [start]
        while stack:
            u = stack.pop()
            for v in graph[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        return seen

    radj = [set() for _ in range(n)]
    for u in range(n):
        for v in adj[u]:
            radj[v].add(u)
    if n == 0:
        return {"connected": False, "n_cells": 0, "n_components": 0}
    fwd = _reachable(0, adj)
    bwd = _reachable(0, radj)
    connected = len(fwd) == n and len(bwd) == n
    return {"connected": connected, "n_cells": n,
            "n_components": 1 if connected else 2}


def require_connected(judgments: Sequence[Judgment]) -> None:
    """Raise if the comparison graph is not strongly connected (guards the MLE, THEORY T5.3)."""
    info = comparison_graph_connected(judgments)
    if not info["connected"]:
        raise ValueError(
            f"comparison graph not strongly connected (n_cells={info['n_cells']}): BT MLE may "
            f"diverge. Add hub edges through FULL/NEUTRAL (PLAN §III.5)."
        )


def cluster_bootstrap_ci(judgments: Sequence[Judgment], contrasts: Sequence[tuple[str, str]],
                         reference: str = REFERENCE_CELL, style_cols: Sequence[str] | None = None,
                         B: int = 2000, seed: int = 0, alpha: float = 0.05) -> dict:
    """Cluster-bootstrap CIs over prompts for BT contrasts (THEORY T3.5 / T5.4)."""
    rng = np.random.default_rng(seed)
    by_prompt: dict[str, list[Judgment]] = {}
    for j in judgments:
        by_prompt.setdefault(j.prompt, []).append(j)
    prompts = list(by_prompt)
    point = fit_bt(judgments, reference, style_cols)
    samples: dict[tuple[str, str], list[float]] = {c: [] for c in contrasts}
    for _ in range(B):
        pick = rng.choice(len(prompts), size=len(prompts), replace=True)
        boot = [j for pi in pick for j in by_prompt[prompts[pi]]]
        try:
            fit = fit_bt(boot, reference, style_cols)
        except Exception:
            continue
        for (ci, cj) in contrasts:
            samples[(ci, cj)].append(fit.contrast(ci, cj))
    out = {}
    for (ci, cj) in contrasts:
        arr = np.sort(np.array(samples[(ci, cj)]))
        if arr.size == 0:
            out[(ci, cj)] = {"point": point.contrast(ci, cj), "lo": float("nan"), "hi": float("nan")}
            continue
        lo = float(arr[int((alpha / 2) * arr.size)])
        hi = float(arr[min(arr.size - 1, int((1 - alpha / 2) * arr.size))])
        out[(ci, cj)] = {"point": point.contrast(ci, cj), "lo": lo, "hi": hi,
                         "excludes_zero": (lo > 0) or (hi < 0)}
    return out
