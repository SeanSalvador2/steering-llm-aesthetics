#!/usr/bin/env python3
"""Judge dry-run: MockJudge over synthetic pairs exercising both-orders/tie logic (PLAN §III.8).

CPU-only, no API calls. Run:

    python scripts/run_judge_dryrun.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p19.judge import MockJudge, PairInput  # noqa: E402


def main() -> int:
    # latent qualities: FULL best, NEUTRAL baseline, LOO/AOI intermediate, near-ties among some
    quality = {"FULL": 1.0, "NEUTRAL": 0.0, "BEAUTY1": 0.45,
               "LOO-C5": 0.35, "LOO-C1": 0.55, "AOI-C1": 0.5, "AOI-C5": 0.52}
    mj = MockJudge(quality=quality, position_bias=0.25, tie_margin=0.15, noise=0.05)

    edges = [
        ("FULL", "NEUTRAL", "FULL-NEUTRAL"),
        ("FULL", "LOO-C5", "FULL-LOO-C5"),
        ("FULL", "LOO-C1", "FULL-LOO-C1"),
        ("AOI-C1", "NEUTRAL", "AOI-C1-NEUTRAL"),
        ("AOI-C5", "AOI-C1", "AOI-near-tie"),   # near-equal -> position bias -> ties
        ("LOO-C1", "AOI-C1", "loo-aoi-near-tie"),
    ]
    pairs = []
    for a, b, edge in edges:
        for prompt in range(8):
            pairs.append(PairInput(f"brief {prompt}", "a", "b", a, b, f"p{prompt}", edge=edge))

    judgments = mj.judge_batch(pairs)
    print(f"=== MockJudge dry-run: {len(judgments)} pairs (both orders each) ===")
    by_edge: dict[str, Counter] = {}
    consistent = 0
    for j in judgments:
        by_edge.setdefault(j.edge, Counter())[j.winner] += 1
        consistent += int(j.consistent)
    print(f"{'edge':18} {'A-wins':>7} {'B-wins':>7} {'ties':>6}")
    for edge, c in by_edge.items():
        print(f"{edge:18} {c['A']:7d} {c['B']:7d} {c['tie']:6d}")
    print(f"\norder-consistent: {consistent}/{len(judgments)} "
          f"({100*consistent/len(judgments):.0f}%); "
          f"remaining resolved to tie by the position-bias control (PLAN §III.8).")
    # sanity: FULL-NEUTRAL should be a clean A-sweep; near-tie edges should produce ties
    fn = by_edge["FULL-NEUTRAL"]
    nt = by_edge["AOI-near-tie"]
    assert fn["A"] >= 7 and fn["B"] == 0, "FULL should sweep NEUTRAL"
    assert nt["tie"] >= 1, "near-tie edge should yield ties"
    print("checks: FULL sweeps NEUTRAL; near-tie edges yield ties  -> OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
