#!/usr/bin/env python3
"""BT power simulation at the frozen allocation + McNemar sizing reproduction (PLAN §III.7).

CPU-only. Validates the judgment budget pre-freeze. Run:

    python scripts/run_power_sim.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p19 import power as pw  # noqa: E402


def main() -> int:
    print("=== McNemar decisive-pair sizing (THEORY T6.2; alpha=.05, power=.80) ===")
    for ws, plan in [(0.60, 193.8), (0.65, 84.8), (0.55, 782.5)]:
        n = pw.required_decisive_pairs(ws)
        print(f"  {round(ws*100)}/{round((1-ws)*100)}  N_dec = {n:7.1f}   (PLAN {plan})")
    print(f"  mis-plug value (conditional split into two-param form) = {pw.misplug_value():.2f} "
          f"(THEORY ~93.26; guarded)")

    tie = 0.15
    print(f"\n=== BT simulation-based power at the frozen allocation (tie_rate={tie}) ===")
    print(f"  {'edge':16} {'n_judged':>8} {'win':>5} {'exp_dec':>8} {'req_dec':>8} {'power':>7}")
    for r in pw.frozen_allocation_power(tie_rate=tie, n_sims=3000):
        print(f"  {r['edge']:16} {r['n_pairs']:8d} {r['assumed_win_share']:5.2f} "
              f"{r['expected_decisive']:8.1f} {r['required_decisive']:8.1f} {r['power']:7.3f}")
    print("\n  Interpretation (PLAN §III.5): the headline FULL-NEUTRAL edge is well powered; the")
    print("  necessity/sufficiency edges are lightly powered on the PREFERENCE channel by design and")
    print("  lean on the fully-powered OBJECTIVE channel under the two-signal null rule (THEORY T6.5).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
