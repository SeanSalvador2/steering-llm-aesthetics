#!/usr/bin/env python3
"""Stage-2 extraction + locate (HF) — dry-run capable (PLAN §IV S2.0-S2.2; ADR-002).

--dry-run prints the extraction/probing plan without loading the model (CPU-safe). Actual
extraction requires torch + transformers + a GPU and runs on Colab (RUNBOOK session 6).

    python scripts/run_stage2_extraction.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p19.config import model_config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage-2 extraction/locate")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    mc = model_config()
    plan = {
        "corpus": "Stage-1 FULL/NEUTRAL dev generations: 40 prompts x 5 seeds = 200/side (S2.0)",
        "capture": "teacher-forced HF forward; mean-response + last-prompt + first-k=64 per layer",
        "layers": mc["focus_band"],
        "stability": "running-mean cosine plateau; require dcos<0.01 over last 20% (S2.0)",
        "probes": "per-layer logistic, 5-fold CV by prompt, + control-task selectivity (S2.1a)",
        "diff_in_means": "v_l = mean_FULL - mean_NEUTRAL; unit-norm; PCA/LAT cross-check (S2.2)",
        "patching": "denoising neutral->skill; design-token logit-diff proxy; %-recovered (S2.1c)",
        "band_rule": "AUC>=0.80 AND selectivity>=0.15 AND patch>=25% contiguous (RQ5)",
        "model": mc["model"]["name"],
        "compute_estimate": "~0.5 A100-h (S2.0) + ~0.5 A100-h patching",
    }
    print("=== Stage-2 extraction/locate plan (PLAN §IV S2.0-S2.2) ===")
    print(json.dumps(plan, indent=2))

    if args.dry_run:
        print("\n[dry-run] no model loaded; plan validated.")
        return 0
    print("\n[run] requires torch+transformers+GPU (Colab only); see RUNBOOK.md session 6.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
