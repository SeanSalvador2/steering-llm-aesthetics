#!/usr/bin/env python3
"""Judging (API phase P3) — dry-run capable (PLAN §III.5/§III.8).

--dry-run prints the comparison-graph edge plan and runs the MockJudge (no API). Real judging uses
Gemini 2.5 Flash (primary) + GPT-4o (15% audit) on Colab/API (RUNBOOK session 5).

    python scripts/run_judging.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# comparison graph (dev confirmatory edges), PLAN §III.5
COMPARISON_GRAPH = [
    ("FULL", "NEUTRAL", 40, 5, 200, "headline skill effect"),
    ("FULL", "LOO-Ci (x5)", 40, 3, 600, "necessity (RQ1)"),
    ("FULL", "NOSYS", 40, 3, 120, "skill vs bare"),
    ("FULL", "BEAUTY1", 40, 3, 120, "content vs nudge (RQ4)"),
    ("NEUTRAL", "AOI-Ci (x5)", 40, 2, 400, "sufficiency (RQ2)"),
    ("NEUTRAL", "NOSYS", 40, 2, 80, "prompt-mass effect"),
    ("BEAUTY1", "NEUTRAL", 40, 2, 80, "nudge vs neutral"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Pairwise VLM judging")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("=== comparison graph (dev confirmatory edges; PLAN §III.5) ===")
    total = 0
    print(f"  {'edge':22} {'prompts':>7} {'seed-pairs':>10} {'judgments':>9}  rationale")
    for a, b, pr, sp, j, why in COMPARISON_GRAPH:
        total += j
        print(f"  {a+' - '+b:22} {pr:7d} {sp:10d} {j:9d}  {why}")
    print(f"  dev confirmatory subtotal: {total} judgments (~{2*total} both-order calls)")
    print("  reliability gate: alpha_K>=0.667 OR (AC1>=0.80 under demonstrable skew) (PREREG §5)")

    if args.dry_run:
        from p19.judge import MockJudge, PairInput
        mj = MockJudge(quality={"FULL": 1.0, "NEUTRAL": 0.0}, position_bias=0.1)
        js = mj.judge_batch([PairInput("b", "a", "b", "FULL", "NEUTRAL", "p1", edge="FULL-NEUTRAL")])
        print(f"\n[dry-run] MockJudge sample: winner={js[0].winner} "
              f"consistent={js[0].consistent} (no API calls)")
        return 0

    print("\n[run] requires the 'judge' extra + API keys (Colab/API); see RUNBOOK.md session 5.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
