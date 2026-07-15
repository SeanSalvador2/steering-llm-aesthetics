"""Paired-preference power: McNemar sizing + BT simulation power (THEORY §T6; PLAN §III.7).

- `required_decisive_pairs` is the canonical one-sample split test (THEORY T6.2) and reproduces
  193.8 / 84.8 / 782.5 decisive pairs for 60/40, 65/35, 55/45 (alpha=.05, power=.80).
- `required_total_pairs_two_param` is the two-parameter McNemar form (THEORY T6.1) with the
  MIS-PLUG GUARD: it warns when p_d < 1 (the regime where a conditional split is wrongly plugged
  as the marginal gap) and raises when |delta| > p_d (an impossible marginal).
- `bt_power_simulation` is the simulation-based BT power check (PLAN §III.7), run here on synthetic
  effect sizes to validate the judgment budget pre-freeze.

Power is used ONLY as an admissibility screen on the preference channel (THEORY T6.3), never as
post-hoc evidence about the truth of an effect.
"""
from __future__ import annotations

import math
import warnings
from typing import Callable

import numpy as np
from scipy import stats

Z_ALPHA_2 = stats.norm.ppf(0.975)   # 1.95996 (two-sided alpha=0.05)
Z_POWER_80 = stats.norm.ppf(0.80)   # 0.84162 (power=0.80)


def required_decisive_pairs(win_share: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """N_dec for a one-sample split test theta1 vs 1/2 among DECISIVE pairs (THEORY T6.2).

    Reproduces PLAN's 193.8 (60/40), 84.8 (65/35), 782.5 (55/45).
    """
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    theta0 = 0.5
    num = (z_a * math.sqrt(theta0 * (1 - theta0)) + z_b * math.sqrt(win_share * (1 - win_share))) ** 2
    return num / (win_share - theta0) ** 2


def required_total_pairs_two_param(delta: float, p_d: float, alpha: float = 0.05,
                                   power: float = 0.80, _guard: bool = True) -> float:
    """N (TOTAL pairs) from the two-parameter McNemar form (THEORY T6.1).

    `delta` MUST be the *marginal* signed gap pi_b - pi_c over ALL pairs; `p_d` the decisive rate.
    MIS-PLUG GUARD (THEORY T6.2): raises if |delta| > p_d (impossible marginal), and warns when
    p_d < 1 because that is where a conditional split (e.g. 0.60-0.40 = 0.2) is commonly mis-passed
    as the marginal gap (which would be p_d*(2*win_share-1) = 0.1, not 0.2), yielding ~93 -- neither
    reading. Prefer `required_decisive_pairs` for the canonical answer.
    """
    if not (0 < p_d <= 1):
        raise ValueError(f"p_d must be in (0,1], got {p_d}")
    if abs(delta) > p_d + 1e-12:
        raise ValueError(
            f"|delta|={abs(delta)} > p_d={p_d}: delta must be the MARGINAL gap pi_b-pi_c "
            f"(|delta| <= p_d always). You likely passed a conditional split difference "
            f"(2*(win_share-0.5)); convert via delta = p_d*(2*win_share-1) or use "
            f"required_decisive_pairs()."
        )
    if _guard and p_d < 1:
        warnings.warn(
            "two-parameter McNemar with p_d<1 is mis-plug-prone: `delta` must be the marginal "
            "gap pi_b-pi_c, NOT the conditional split difference. See THEORY T6.2; "
            "required_decisive_pairs() is the canonical path.",
            stacklevel=2,
        )
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    num = (z_a * math.sqrt(p_d) + z_b * math.sqrt(p_d - delta ** 2 / p_d)) ** 2
    return num / delta ** 2


def misplug_value(alpha: float = 0.05, power: float = 0.80) -> float:
    """The documented WRONG answer (~93.26): conditional split 0.2 plugged with p_d=0.5 (THEORY T6.2)."""
    return required_total_pairs_two_param(0.2, 0.5, alpha, power, _guard=False)


def reconcile_decisive(win_share: float, p_d: float, alpha: float = 0.05,
                       power: float = 0.80) -> dict:
    """Cross-check: N_total (T6.1, marginal delta) * p_d == N_decisive (T6.2) (THEORY T6.2)."""
    delta_marginal = p_d * (2 * win_share - 1)
    n_total = required_total_pairs_two_param(delta_marginal, p_d, alpha, power, _guard=False)
    return {
        "win_share": win_share, "p_d": p_d, "delta_marginal": delta_marginal,
        "n_total": n_total, "n_total_x_pd": n_total * p_d,
        "n_decisive_direct": required_decisive_pairs(win_share, alpha, power),
    }


def achieved_n_check(observed_win_share: float, n_decisive: int, alpha: float = 0.05,
                     power: float = 0.80) -> dict:
    """Post-hoc admissibility screen (THEORY T6.3): required n at the OBSERVED split vs achieved."""
    win = max(observed_win_share, 1 - observed_win_share)  # required-n depends on |split|
    req = required_decisive_pairs(win, alpha, power) if win != 0.5 else float("inf")
    return {"required_decisive": req, "achieved_decisive": n_decisive,
            "underpowered": n_decisive < req}


def bt_power_simulation(n_pairs: int, win_share: float, tie_rate: float = 0.2,
                        n_sims: int = 2000, alpha: float = 0.05, seed: int = 0) -> dict:
    """Simulation-based power for a paired preference contrast (PLAN §III.7).

    Simulate `n_pairs` judged pairs: each is a tie w.p. `tie_rate`; a decisive pair is an A-win
    w.p. `win_share`. Test H0: among decisive pairs the winner is a fair coin (two-sided binomial).
    Returns empirical power = fraction of sims that reject at `alpha`, plus mean decisive count.
    """
    rng = np.random.default_rng(seed)
    rejections = 0
    dec_counts = []
    for _ in range(n_sims):
        is_tie = rng.random(n_pairs) < tie_rate
        dec = ~is_tie
        n_dec = int(dec.sum())
        dec_counts.append(n_dec)
        if n_dec == 0:
            continue
        a_wins = int((rng.random(n_dec) < win_share).sum())
        # exact two-sided binomial test H0: p=0.5
        p = stats.binomtest(a_wins, n_dec, 0.5, alternative="two-sided").pvalue
        if p < alpha:
            rejections += 1
    return {
        "n_pairs": n_pairs, "win_share": win_share, "tie_rate": tie_rate,
        "power": rejections / n_sims, "mean_decisive": float(np.mean(dec_counts)),
    }


# frozen allocation (PREREG §6 / PLAN §III.5) for the achieved-power table
FROZEN_ALLOCATION = [
    ("FULL-NEUTRAL", 200, 0.60),
    ("FULL-LOO-Ci", 120, 0.60),
    ("AOI-Ci-NEUTRAL", 80, 0.65),
    ("FULL-BEAUTY1", 120, 0.60),
]


def frozen_allocation_power(tie_rate: float = 0.15, n_sims: int = 2000, seed: int = 0) -> list[dict]:
    """Run the BT power simulation at the frozen allocation on synthetic effect sizes (PLAN §III.7).

    Between well-separated cells ties are uncommon (THEORY T6.2), so a modest tie_rate is the
    planning assumption; each row also carries the analytic required decisive N (T6.2) and the
    expected decisive count = (1 - tie_rate) * n_judged, so under/over-power is transparent.
    """
    out = []
    for name, n, win in FROZEN_ALLOCATION:
        res = bt_power_simulation(n, win, tie_rate=tie_rate, n_sims=n_sims, seed=seed)
        res["edge"] = name
        res["assumed_win_share"] = win
        res["required_decisive"] = required_decisive_pairs(win)
        res["expected_decisive"] = (1 - tie_rate) * n
        out.append(res)
    return out
