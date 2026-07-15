"""p19 — Anatomy of a Design Skill (Project 19).

Supporting-code layer for a two-stage study on Qwen/Qwen2.5-Coder-7B-Instruct:
Stage 1 (black-box factorial ablation of a frontend-design skill) and Stage 2
(white-box mechanistic interpretability + causal steering).

Governance: CLAUDE.md (model lock, compute policy, oracle, commit policy).
Authoritative plan: PLAN.md. Derivations: THEORY.md. Freeze: PREREGISTRATION.md.

Layout follows PLAN §VI.1. CPU-safe modules run and are tested in this environment;
GPU-phase modules (generation_vllm, generation_hf, hooks, activations, steering,
patching, probes) import heavy deps lazily and are exercised via mocks / a tiny
randomly-initialized Qwen2 stand-in — NEVER the 7B weights (compute policy).
"""

from pathlib import Path

__version__ = "0.1.0"

# Repo root = three levels up from this file (src/p19/__init__.py -> repo/).
REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
VENDOR_DIR = Path(__file__).resolve().parent / "vendor"

__all__ = ["__version__", "REPO_ROOT", "CONFIG_DIR", "VENDOR_DIR"]
