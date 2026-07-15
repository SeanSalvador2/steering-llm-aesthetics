"""Config loading, validation, and freeze-hashing (PLAN §VI.1 `src/config`, §VI.2).

Loads the frozen YAML configs, exposes typed accessors, and hashes any config blob for the
manifest (PREREG §11 "engine+version+sampling+config hashes recorded per row"). Hashing is
canonical (sorted-key JSON) so an unchanged config reproduces an identical hash.
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from . import CONFIG_DIR


def load_yaml(path: str | Path) -> dict:
    """Load a YAML file into a dict."""
    p = Path(path)
    if not p.is_absolute():
        p = CONFIG_DIR / p
    with open(p, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=None)
def _cached(name: str) -> dict:
    return load_yaml(f"{name}.yaml")


def model_config() -> dict:
    return _cached("model")


def skill_config() -> dict:
    return _cached("skill")


def cells_config() -> dict:
    return _cached("cells")


def prompts_config() -> dict:
    return _cached("prompts")


def render_config() -> dict:
    return _cached("render")


def judge_config() -> dict:
    return _cached("judge")


def steering_grids_config() -> dict:
    return _cached("steering_grids")


def steering_frozen_config() -> dict:
    return _cached("steering_frozen")


def noncode_probe_config() -> dict:
    return _cached("noncode_probe")


def config_hash(blob: Any) -> str:
    """Canonical SHA-256 of any JSON-serializable config blob.

    Keys are sorted and whitespace normalized so semantically-identical configs hash equal.
    """
    payload = json.dumps(blob, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sampling_hash() -> str:
    """Hash of the frozen sampling config (stamped into every generation row, PREREG §11)."""
    return config_hash(model_config()["sampling"])


def cells_by_id() -> dict[str, dict]:
    """Map cell_id -> cell dict."""
    return {c["id"]: c for c in cells_config()["cells"]}


def prompts_by_id() -> dict[str, dict]:
    """Map prompt_id -> prompt dict."""
    return {p["id"]: p for p in prompts_config()["prompts"]}


def validate_all() -> dict[str, Any]:
    """Cross-check the YAML configs against PLAN/PREREG invariants.

    Returns a report dict (used by scripts/make_configs_check.py). Raises AssertionError on
    any structural violation so a broken config never reaches a GPU run.
    """
    report: dict[str, Any] = {}

    # -- cells (PREREG §3) --
    cells = cells_config()["cells"]
    ids = [c["id"] for c in cells]
    assert len(ids) == 24, f"expected 24 cells, got {len(ids)}"
    assert len(set(ids)) == 24, "duplicate cell ids"
    factorial = [c for c in cells if c.get("in_fraction")]
    assert len(factorial) == 16, f"16-run fraction expected, got {len(factorial)}"
    # every in-fraction cell has even #minus (product of signs = +1); PREREG §3 / THEORY T1.
    for c in factorial:
        sign = c["sign"]
        prod = 1
        for s in sign:
            prod *= s
        assert prod == 1, f"{c['id']} not in principal fraction (prod signs != +1)"
    # LOO + NEUTRAL are off-fraction (odd #minus).
    for cid in ["NEUTRAL", "LOO-C1", "LOO-C2", "LOO-C3", "LOO-C4", "LOO-C5"]:
        sign = next(c for c in cells if c["id"] == cid)["sign"]
        prod = 1
        for s in sign:
            prod *= s
        assert prod == -1, f"{cid} should be off-fraction (odd #minus)"
    # seed allocation
    for c in cells:
        exp = 5 if c["tier"] in ("control", "loo", "aoi") else 3
        assert c["seeds"] == exp, f"{c['id']} seeds {c['seeds']} != {exp}"
    report["cells"] = {"n": len(ids), "n_fraction": len(factorial)}

    # -- prompts (PLAN §II.2.1) --
    pcfg = prompts_config()
    prompts = pcfg["prompts"]
    assert len(prompts) == 58, f"expected 58 prompts, got {len(prompts)}"
    splits = {"dev": 0, "heldout_seen": 0, "heldout_unseen": 0}
    for p in prompts:
        splits[p["split"]] += 1
    assert splits == {"dev": 40, "heldout_seen": 8, "heldout_unseen": 10}, splits
    # frozen id lists match the corpus
    fz = pcfg["split_freeze"]
    assert set(fz["dev"]) == {p["id"] for p in prompts if p["split"] == "dev"}
    assert set(fz["heldout_seen"]) == {p["id"] for p in prompts if p["split"] == "heldout_seen"}
    assert set(fz["heldout_unseen"]) == {p["id"] for p in prompts if p["split"] == "heldout_unseen"}
    report["prompts"] = {"n": len(prompts), "splits": splits}

    # -- model lock (CLAUDE.md / ADR-001) --
    mc = model_config()
    assert mc["model"]["name"] == "Qwen/Qwen2.5-Coder-7B-Instruct", "model lock violated"
    assert mc["model"]["d_model"] == 3584 and mc["model"]["n_layers"] == 28
    assert mc["sampling"]["seeds"] == [0, 1, 2, 3, 4]
    report["model"] = mc["model"]["name"]

    # -- steering guardrails (PLAN S2.3) --
    sg = steering_grids_config()
    assert sg["kl_threshold"] == 0.30 and sg["render_min"] == 0.90
    report["steering"] = {"kl": sg["kl_threshold"], "render_min": sg["render_min"]}

    report["hashes"] = {
        "sampling": sampling_hash(),
        "cells": config_hash(cells_config()),
        "prompts": config_hash(prompts_config()),
    }
    return report
