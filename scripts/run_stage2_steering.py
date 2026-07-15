#!/usr/bin/env python3
"""Stage-2 steering: dev sweep + held-out verification (HF) — dry-run capable (PLAN §IV S2.3-S2.7).

--dry-run enumerates the sweep grid + S2.4 arms without loading the model (CPU-safe). Actual
steering requires torch + transformers + a GPU and runs on Colab (RUNBOOK sessions 7-8).

    python scripts/run_stage2_steering.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p19 import steering as st  # noqa: E402
from p19 import generation_hf as gh  # noqa: E402
from p19.config import steering_grids_config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage-2 steering sweep + verify")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    g = steering_grids_config()
    coarse = st.sweep_configs("coarse")
    print("=== S2.3 dev sweep (PLAN §IV S2.3) ===")
    print(f"coarse configs: {len(coarse)} (layers x rho x mean-response)")
    print(f"grid: layers={g['coarse']['layers']} rho={g['coarse']['rho_grid']}")
    print(f"guardrails: mean-KL <= {g['kl_threshold']} nats AND render-success >= {g['render_min']}")
    print("selection: argmax dev POC-gain s.t. guardrails; ties -> lower KL; write "
          "config/steering_frozen.yaml; git-tag steer-frozen BEFORE held-out (PREREG §7)")

    print("\n=== S2.4 held-out verification arms (PLAN §IV S2.4) ===")
    print(json.dumps({k: v for k, v in gh.dry_run().items() if k != "sampling"}, indent=2))
    print("success criterion: steered>unsteered on >=1 objective family after Holm AND gated BT "
          "CI>0 AND random(k=5) fails both AND flip test attenuates (PREREG §7)")

    if args.dry_run:
        print("\n[dry-run] no model loaded; grid + arms validated.")
        return 0
    print("\n[run] requires torch+transformers+GPU (Colab only); see RUNBOOK.md sessions 7-8.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
