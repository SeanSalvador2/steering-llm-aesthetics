#!/usr/bin/env python3
"""Validate all YAML configs against PLAN/PREREG invariants + run the build-time audits.

CPU-only. Exit non-zero on any structural violation. Run:

    python scripts/make_configs_check.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p19 import config, skill_assembly  # noqa: E402


def main() -> int:
    print("=== config validation (PLAN §III.1 / PREREG §3) ===")
    rep = config.validate_all()
    print(json.dumps({k: rep[k] for k in ("cells", "prompts", "model", "steering")}, indent=2))

    print("\n=== build-time audits (PLAN §II.1) ===")
    audits = skill_assembly.run_build_audits()
    ok = True

    # (a) hard-fails on the ACTIVE method (exact tokenizer when available, else estimate); the
    # pre-freeze C5 reword put both paths in-band (see audit_token_balance regression history).
    tb = audits["token_balance"]
    print(f"(a) token balance    method={tb['method']} pass={tb['pass']} "
          f"counts={tb['counts']} band={[round(x, 1) for x in tb['band']]}")
    ok = ok and tb["pass"]

    ba = audits["filler_banned_topics"]
    print(f"(b) filler inertness pass={ba['pass']} hits={ba['hits']}")
    ok = ok and ba["pass"]

    idn = audits["filler_identity"]
    print(f"(c) filler identity  pass={idn['pass']} mismatch={idn['mismatch']}")
    ok = ok and idn["pass"]

    cid = audits["component_identity"]
    print(f"(c') component identity pass={cid['pass']} mismatch={cid['mismatch']}")
    ok = ok and cid["pass"]

    pid = audits["padding_identity"]
    print(f"(c+) padding-pool identity pass={pid['pass']} "
          f"topics={pid['n_topics']} clauses={pid['n_clauses']}")
    ok = ok and pid["pass"]

    fm = audits["filler_component_match"]
    ratios = {k: round(v["ratio"], 3) for k, v in fm["pairs"].items()}
    print(f"(c'') filler<->component match (raw) pass={fm['pass']} ratios={ratios}")
    ok = ok and fm["pass"]

    lk = audits["prompt_leakage"]
    print(f"(d) prompt leakage   pass={lk['pass']} hits={lk['hits']}")
    ok = ok and lk["pass"]

    # --- strict filler equalization + constant-mass (canonical §3 / PREREG §2) ---
    eq = skill_assembly.equalize_fillers()
    if eq.get("available"):
        print("\n=== strict filler equalization (|F_i - C_i| <= 2 exact tokens) ===")
        for k, v in eq["fillers"].items():
            print(f"  {k}: {v['tokens']:3d} (target {v['target']:3d}, delta {v['delta']:+d})  "
                  f"actions={v['actions']}")
            ok = ok and abs(v["delta"]) <= 2
        cm = skill_assembly.cell_mass_report(tol=10)
        print("\n=== per-cell system-prompt token masses (constant-mass, ±10 of FULL) ===")
        print(f"  FULL = {cm['full_mass']}  max|dev| = {cm['max_abs_deviation']}  "
              f"pass = {cm['pass']}")
        row = []
        for cell_id, mass in cm["masses"].items():
            row.append(f"{cell_id}={mass}")
            if len(row) == 6:
                print("   " + "  ".join(row))
                row = []
        if row:
            print("   " + "  ".join(row))
        print(f"  reference (not length-matched): {cm['reference_cells']}")
        ok = ok and cm["pass"]
    else:
        print("\n(strict equalization skipped: tokenizer unavailable; runs on Colab)")

    est = skill_assembly.audit_token_balance(force_estimate=True)
    print(f"\n(a') estimate-path token balance pass={est['pass']} (fallback path, PLAN §II.1.2)")
    ok = ok and est["pass"]

    print("\n=== config hashes (PREREG §11) ===")
    print(json.dumps(rep["hashes"], indent=2))

    print(f"\nRESULT: {'ALL GREEN' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
