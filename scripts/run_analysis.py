#!/usr/bin/env python3
"""Analysis pipeline (CPU): MixedLM + BT + agreement + multiplicity (PLAN §III.6).

On Colab this consumes results/metrics.parquet + results/judgments.parquet. Here, --demo runs the
full stats stack END-TO-END on synthetic data to prove the wiring (no real generations exist yet).

    python scripts/run_analysis.py --demo
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p19 import mixedlm as ml, bt_model as bt, agreement as ag, multiplicity as mp  # noqa: E402


def _sim_metrics(seed=0):
    rng = np.random.default_rng(seed)
    true = {"C1": 0.4, "C2": 0.25, "C3": 0.1, "C4": 0.05, "C5": 0.6}
    rows = []
    for c in ml.factorial_cells():
        sign = dict(zip(ml.FACTORS, c["sign"]))
        mu = 1.0 + sum(true[f] * sign[f] for f in ml.FACTORS)
        for pr in range(40):
            u = rng.normal(0, 0.3)
            for s in range(3):
                r = {"cell_id": c["id"], "prompt_id": f"p{pr}", "seed": s,
                     "poc": mu + u + rng.normal(0, 0.4)}
                r.update({f: sign[f] for f in ml.FACTORS})
                rows.append(r)
    return pd.DataFrame(rows), true


def _sim_judgments(seed=0):
    rng = np.random.default_rng(seed)
    strengths = {"NEUTRAL": 0.0, "FULL": 1.4, "LOO-C5": 0.6}
    edges = [("FULL", "NEUTRAL"), ("FULL", "LOO-C5"), ("NEUTRAL", "LOO-C5")]
    J = []
    for pr in range(40):
        for _ in range(4):
            for a, b in edges:
                mi, mj = strengths[a], strengths[b]
                eA, eB, et = math.exp(mi), math.exp(mj), 0.3 * math.exp((mi + mj) / 2)
                D = eA + eB + et
                J.append(bt.Judgment(a, b, f"p{pr}",
                                     ["A", "B", "tie"][rng.choice(3, p=[eA/D, eB/D, et/D])]))
    return J


def main() -> int:
    ap = argparse.ArgumentParser(description="Analysis pipeline")
    ap.add_argument("--demo", action="store_true", help="run on synthetic data (CPU)")
    args = ap.parse_args()
    if not args.demo:
        print("Provide --demo (no real generations in the CPU env). On Colab this reads "
              "results/metrics.parquet + results/judgments.parquet (RUNBOOK).")
        return 0

    print("=== objective: factorial MixedLM on POC (THEORY T1/T3) ===")
    df, true = _sim_metrics()
    fac = ml.fit_factorial(df, "poc")
    print(f"  ladder rung: {fac['rung']}")
    for f in ml.FACTORS:
        print(f"    {f}: est={fac['coefs'][f]['est']:+.3f} (true {true[f]:+.2f}) "
              f"p={fac['coefs'][f]['p']:.2e}")

    print("\n=== necessity contrasts + Holm over the POC family (PREREG §4) ===")
    pvals = {}
    for i in range(1, 6):
        pc = ml.paired_contrast(df, "FULL", f"AOI-C{i}", "poc")  # stand-in for LOO here (synthetic)
        pvals[f"FULL-LOO-C{i}"] = pc.pvalue
    # fill the rest of the 12-family with placeholder large p's for the demo
    pvals["FULL-NEUTRAL"] = 1e-6
    for i in range(1, 6):
        pvals[f"AOI-C{i}-NEUTRAL"] = 0.5
    pvals["FULL-BEAUTY1"] = 0.2
    holm = mp.confirmatory_holm(pvals)
    n_rej = sum(r.reject for r in holm)
    print(f"  Holm rejections in the 12-test family: {n_rej}")

    print("\n=== preference: style-controlled BT (THEORY T5) ===")
    J = _sim_judgments()
    bt.require_connected(J)
    ci = bt.cluster_bootstrap_ci(J, [("FULL", "NEUTRAL"), ("FULL", "LOO-C5")], B=300)
    for k, v in ci.items():
        print(f"  {k[0]}-{k[1]}: Δβ={v['point']:+.3f} CI=({v['lo']:+.2f},{v['hi']:+.2f}) "
              f"excl0={v['excludes_zero']}")

    print("\n=== reliability gate on a synthetic judge-vs-human panel (THEORY T4) ===")
    panel = [{"j": 1, "h": 1}] * 82 + [{"j": 0, "h": 0}] * 6 + \
            [{"j": 1, "h": 0}] * 6 + [{"j": 0, "h": 1}] * 6
    gate = ag.reliability_gate(panel, [0, 1])
    print(f"  alpha_K={gate['alpha_K']:.3f} AC1={gate['AC1']:.3f} pi_max={gate['pi_max']:.2f} "
          f"-> pass={gate['pass']} (rung: {gate['rung']})")
    print("\nRESULT: analysis pipeline wired end-to-end (synthetic).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
