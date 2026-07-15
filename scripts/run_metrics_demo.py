#!/usr/bin/env python3
"""Metrics demo: render all fixtures, compute the full metric vector + POC, write a Parquet + table.

CPU-only (PLAN ADR-007). Verifies the oracle direction (clean > slop POC; slop PSI > clean;
overflow triggers overflow/overlap; axe nonzero where designed). Run:

    python scripts/run_metrics_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p19 import REPO_ROOT, poc  # noqa: E402
from p19.rendering import render_file  # noqa: E402

FIXTURES = ["clean_landing", "slop_landing", "overflow_broken", "minimal_valid"]


def main() -> int:
    fx_dir = REPO_ROOT / "fixtures"
    out_dir = REPO_ROOT / "results" / "demo_renders"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for name in FIXTURES:
        r = render_file(fx_dir / f"{name}.html", out_dir=out_dir, run_axe=True)
        row = poc.assemble_row(r, r.screenshots["desktop"])
        row["gen_id"] = name
        row["cell_id"] = name
        rows.append(row)
    df = pd.DataFrame(rows)
    res = poc.compute_poc(df, psi_admit=True)
    df["poc"] = res["poc"].values

    results_path = REPO_ROOT / "results" / "demo_metrics.parquet"
    df.to_parquet(results_path, index=False)

    cols = ["gen_id", "render_success", "hermetic", "n_overflow", "n_overlap", "axe_total",
            "contrast_frac_below_4_5", "align_regularity", "whitespace_ratio",
            "type_scale_adherence", "colorfulness", "psi", "poc"]
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    print("\n=== fixture metric demo (results/demo_metrics.parquet) ===")
    print(df[cols].round(3).to_string(index=False))

    d = df.set_index("gen_id")
    checks = {
        "clean POC > slop POC": bool(d.loc["clean_landing", "poc"] > d.loc["slop_landing", "poc"]),
        "slop PSI > clean PSI": bool(d.loc["slop_landing", "psi"] > d.loc["clean_landing", "psi"]),
        "overflow n_overflow>0": bool(d.loc["overflow_broken", "n_overflow"] > 0),
        "overflow n_overlap>0": bool(d.loc["overflow_broken", "n_overlap"] > 0),
        "slop axe_total>0": bool(d.loc["slop_landing", "axe_total"] > 0),
    }
    print("\n=== oracle-direction checks ===")
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print(f"\nc* branch: {res['c_star_branch']}  c*={res['c_star']:.2f}  "
          f"POC terms: {res['n_terms']}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
