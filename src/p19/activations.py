"""Extraction corpus runner + running-mean storage/stability (PLAN §IV S2.0; THEORY §T8.1).

Reuses the Stage-1 FULL/NEUTRAL dev generations (200/side) as the extraction corpus: a teacher-
forced HF forward over [prompt || response] captures the mean-response residual per layer
(hooks.capture_means). The corpus runner is import-guarded (GPU on Colab). The running-mean
accumulation + cosine-plateau stability check (PLAN S2.0) is pure numpy and CPU-tested.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np

from .steering import running_mean_cosine_stability


def accumulate_running_means(vectors: Sequence[np.ndarray]) -> list[np.ndarray]:
    """Running mean after each example: rm[i] = mean(vectors[:i+1]) (PLAN S2.0)."""
    out = []
    acc = None
    for i, v in enumerate(vectors):
        v = np.asarray(v, float)
        acc = v.copy() if acc is None else acc + v
        out.append(acc / (i + 1))
    return out


def stability_report(per_example_layer_vectors: dict[int, list[np.ndarray]]) -> dict[int, dict]:
    """Cosine-plateau report per layer over the extraction corpus (PLAN S2.0 / F13).

    per_example_layer_vectors[l] = list of per-example mean-response vectors (in corpus order).
    """
    report = {}
    for l, vecs in per_example_layer_vectors.items():
        rms = accumulate_running_means(vecs)
        report[l] = running_mean_cosine_stability(rms)
    return report


def save_means(path: str | Path, means: dict[int, np.ndarray]) -> None:
    """Persist per-layer mean vectors as a compressed .npz shard (PLAN S2.0 storage)."""
    np.savez_compressed(path, **{f"layer_{l}": np.asarray(v) for l, v in means.items()})


def load_means(path: str | Path) -> dict[int, np.ndarray]:
    data = np.load(path)
    return {int(k.split("_")[1]): data[k] for k in data.files}


# --------------------------------------------------------------------------- corpus runner (GPU)

def extract_example(model, input_ids, layers, response_start: int, first_k: int = 64) -> dict:
    """Per-layer {mean_response, last_prompt_token, first_k} for one teacher-forced example (S2.0).

    Import-guarded via hooks; runs on the tiny Qwen2 model in tests, the 7B on Colab.
    """
    from .hooks import capture_means

    return capture_means(model, input_ids, layers, response_start=response_start, first_k=first_k)


def extract_corpus(model, examples: list[dict], layers, tokenizer=None,
                   first_k: int = 64) -> dict:  # pragma: no cover - GPU/Colab
    """Run the FULL/NEUTRAL extraction corpus (S2.0). Each example = {input_ids, response_start, side}.

    Returns per-side per-layer lists of mean-response vectors (for diff-in-means + stability). This
    is the Colab entrypoint; unit tests exercise `extract_example` on the tiny model directly.
    """
    sides = {"FULL": {l: [] for l in layers}, "NEUTRAL": {l: [] for l in layers}}
    for ex in examples:
        caps = extract_example(model, ex["input_ids"], layers, ex["response_start"], first_k)
        for l in layers:
            mr = caps[l]["mean_response"]
            sides[ex["side"]][l].append(mr.detach().cpu().numpy() if mr is not None else None)
    return sides
