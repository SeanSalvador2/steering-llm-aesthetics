"""Stage-1 bulk generation (vLLM) — plan builder + import-guarded runner (PLAN §III.1; ADR-002).

The generation-plan builder is pure-config and CPU-tested (it must reproduce dev 4,000 + held-out
630 = 4,630 units, PLAN §III.1 / PREREG §3). The vLLM runner is import-guarded and resume-safe
(skips units already in the manifest); it is NEVER executed in the CPU env (compute policy).
A --dry-run validates configs and prints the plan without loading the model.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from .config import (cells_config, cells_by_id, prompts_config, model_config,
                     sampling_hash, load_yaml)
from .prompts import build_messages, split_ids


@dataclass
class GenUnit:
    cell_id: str
    prompt_id: str
    seed: int
    split: str

    @property
    def gen_id(self) -> str:
        raw = f"{self.cell_id}|{self.prompt_id}|{self.seed}|{self.split}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _seed_list(n: int) -> list[int]:
    return list(range(n))


def build_generation_plan(split: str = "all") -> list[GenUnit]:
    """Enumerate (cell, prompt, seed) units (PLAN §III.1).

    Dev: all 24 cells x 40 dev prompts, seeds per cell tier (headline/LOO/AOI=5, interaction=3).
    Held-out: reduced set {4 controls @5 + 5 LOO @3} x 18 held-out prompts.
    """
    cells = cells_config()["cells"]
    cfg = cells_config()
    dev_ids = split_ids("dev")
    held_ids = split_ids("heldout_seen") + split_ids("heldout_unseen")
    units: list[GenUnit] = []

    if split in ("all", "dev"):
        for c in cells:
            seeds = _seed_list(c["seeds"])
            for pid in dev_ids:
                for s in seeds:
                    units.append(GenUnit(c["id"], pid, s, "dev"))

    if split in ("all", "heldout"):
        held_cells = cfg["heldout_cells"]
        held_loo_seeds = cfg["heldout_loo_seeds"]
        cbi = cells_by_id()
        for cid in held_cells:
            tier = cbi[cid]["tier"]
            seeds = held_loo_seeds if tier == "loo" else _seed_list(cbi[cid]["seeds"])
            for pid in held_ids:
                for s in seeds:
                    units.append(GenUnit(cid, pid, s, "heldout"))

    return units


def plan_summary(units: list[GenUnit]) -> dict:
    """Counts by split (for the dry-run acceptance check; PLAN §III.1)."""
    dev = [u for u in units if u.split == "dev"]
    held = [u for u in units if u.split == "heldout"]
    return {"total": len(units), "dev": len(dev), "heldout": len(held),
            "expected": {"dev": 4000, "heldout": 630, "total": 4630}}


def dry_run() -> dict:
    """Validate configs and print/return the execution plan WITHOUT loading the model (ADR-002)."""
    units = build_generation_plan("all")
    s = plan_summary(units)
    s["sampling_hash"] = sampling_hash()
    s["model"] = model_config()["model"]["name"]
    s["matches_expected"] = (s["dev"] == 4000 and s["heldout"] == 630 and s["total"] == 4630)
    # strict filler equalization: per-filler final counts recorded with every run (canonical §3)
    from .skill_assembly import equalize_fillers

    eq = equalize_fillers()
    if eq.get("available"):
        s["skill_equalization"] = {
            k: {"tokens": v["tokens"], "target": v["target"], "actions": v["actions"]}
            for k, v in eq["fillers"].items()
        }
    else:  # pragma: no cover - tokenizer-less env
        s["skill_equalization"] = {"available": False, "note": eq.get("reason", "")}
    return s


def prompt_for_unit(unit: GenUnit) -> list[dict]:
    """ChatML messages for a unit (system per cell, user = brief + output constraint)."""
    return build_messages(unit.cell_id, unit.prompt_id)


# --------------------------------------------------------------------------- runner (GPU, Colab)

def run_generation(out_dir, manifest_path, resume: bool = True,
                   split: str = "all"):  # pragma: no cover - GPU/Colab
    """vLLM bulk generation (Stage-1). Import-guarded; resume-safe via the manifest. Colab only."""
    try:
        from vllm import LLM, SamplingParams
    except ImportError as e:
        raise ImportError("run_generation requires vLLM (extra 'vllm'); runs on Colab.") from e

    from .prompts import render_chatml  # tokenizer chat template
    mc = model_config()
    samp = mc["sampling"]
    units = build_generation_plan(split)
    done: set[str] = set()
    if resume and Path(manifest_path).exists():
        from .manifest import Manifest
        done = {r.path for r in Manifest.load_jsonl(manifest_path).records}

    llm = LLM(model=mc["model"]["name"], dtype=mc["model"]["dtype"])
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for unit in units:
        html_path = str(Path(out_dir) / f"{unit.gen_id}.html")
        if html_path in done:
            continue
        prompt = render_chatml(prompt_for_unit(unit))
        sp = SamplingParams(temperature=samp["temperature"], top_p=samp["top_p"],
                            top_k=samp["top_k"], repetition_penalty=samp["repetition_penalty"],
                            max_tokens=samp["max_new_tokens"], seed=unit.seed)
        out = llm.generate([prompt], sp)[0]
        Path(html_path).write_text(out.outputs[0].text, encoding="utf-8")
    return {"generated": len(units)}
