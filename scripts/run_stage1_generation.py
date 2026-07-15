#!/usr/bin/env python3
"""Stage-1 bulk generation (vLLM) — dry-run capable (PLAN §III.1; ADR-002; compute policy).

--dry-run validates configs and prints the execution plan WITHOUT loading the model (CPU-safe).
Actual generation requires vLLM + a GPU and is run ONLY on Colab (RUNBOOK session 2-3).

    python scripts/run_stage1_generation.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p19 import generation_vllm as gv  # noqa: E402
from p19.manifest import run_manifest  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage-1 vLLM generation")
    ap.add_argument("--dry-run", action="store_true", help="validate + print plan; no model load")
    ap.add_argument("--out", default="artifacts/stage1", help="HTML output dir (Colab: Drive)")
    ap.add_argument("--manifest", default="results/stage1_manifest.jsonl")
    ap.add_argument("--split", default="all", choices=["all", "dev", "heldout"])
    args = ap.parse_args()

    plan = gv.dry_run()
    print("=== Stage-1 generation plan (PLAN §III.1) ===")
    print(json.dumps(plan, indent=2))
    print("\n=== run provenance (PREREG §11) ===")
    print(json.dumps({k: v for k, v in run_manifest(engine="vllm").items()
                      if k != "sampling"}, indent=2))

    if args.dry_run:
        print("\n[dry-run] no model loaded; plan validated. "
              f"matches_expected={plan['matches_expected']}")
        return 0 if plan["matches_expected"] else 1

    print("\n[run] launching vLLM generation (requires GPU + vLLM; Colab only) ...")
    gv.run_generation(args.out, args.manifest, split=args.split)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
