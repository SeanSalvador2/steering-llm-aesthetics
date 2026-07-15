"""Stage-2 HF generation — hookable, same record schema as vLLM (PLAN §IV; ADR-002).

HF `.generate` (batched) for all Stage-2 steering/verification, with the SAME fixed sampling as
Stage-1 (PLAN §II.3) so records are schema-identical. Steering is applied by wrapping generation
in an addition hook (src/p19/hooks.py). NEVER compare a vLLM baseline to an HF steered output —
any Stage-1<->Stage-2 comparison re-generates the baseline in HF (ADR-002). Import-guarded; the
plan/dry-run is CPU; generation runs on Colab (or the tiny model in tests).
"""
from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path

import numpy as np

from .config import model_config
from .prompts import build_messages, render_chatml


def sampling_kwargs() -> dict:
    """HF generate kwargs from the frozen sampling config (PLAN §II.3)."""
    s = model_config()["sampling"]
    return dict(do_sample=True, temperature=s["temperature"], top_p=s["top_p"],
                top_k=s["top_k"], repetition_penalty=s["repetition_penalty"],
                max_new_tokens=s["max_new_tokens"])


def dry_run(arms=("unsteered", "steered", "random", "full_ref"), n_prompts: int = 18,
            n_seeds: int = 3) -> dict:
    """Validate the S2.4 arm plan without loading the model (PLAN S2.4)."""
    per_arm = n_prompts * n_seeds
    plan = {a: per_arm for a in arms}
    plan["random_draws"] = 5  # k=5 norm-matched random draws (PLAN S2.4)
    plan["total_gens"] = per_arm * len(arms) + per_arm * (plan["random_draws"] - 1) \
        if "random" in arms else per_arm * len(arms)
    plan["sampling"] = sampling_kwargs()
    return plan


def generate(model, tokenizer, cell_id: str, prompt_id: str, seed: int = 0,
             steer=None):  # pragma: no cover - GPU/Colab
    """Generate one HTML for (cell, prompt, seed), optionally steered.

    `steer` = None or {"layer": l, "vhat": np.ndarray, "alpha": float}. Returns the decoded text.
    Import-guarded; runs on the tiny model in tests via a shared path, the 7B on Colab.
    """
    import torch
    from .hooks import addition_hook

    torch.manual_seed(seed)
    messages = build_messages(cell_id, prompt_id)
    prompt = render_chatml(messages)
    enc = tokenizer(prompt, return_tensors="pt").to(model.device)

    ctx = nullcontext()
    if steer is not None:
        v = torch.as_tensor(np.asarray(steer["vhat"]))
        ctx = addition_hook(model, steer["layer"], v, steer["alpha"])

    with ctx, torch.no_grad():
        out = model.generate(**enc, **sampling_kwargs())
    return tokenizer.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
