"""Denoising activation patching + logit-diff proxy (PLAN §IV S2.1c; THEORY §T8.6).

Denoising: run the NEUTRAL (corrupted) prompt, patch in the FULL-side (clean) mean-response
residual at a (layer, position) site, and measure how much of the design behavior is restored via
the design-token logit-difference proxy or the probe-projection proxy. Reports % of the
clean-corrupted gap recovered. The % formula is CPU-tested; the model-driven patch is import-guarded.

Denoising (not noising) is robust to self-repair / the hydra effect (THEORY T8.6).
"""
from __future__ import annotations

import numpy as np


def percent_recovered(m_patched: float, m_corrupt: float, m_clean: float) -> float:
    """% of the clean-corrupted gap recovered by a patch (THEORY T8.6).

    %rec = (m_patched - m_corrupt) / (m_clean - m_corrupt) * 100.
    """
    denom = m_clean - m_corrupt
    if denom == 0:
        return float("nan")
    return 100.0 * (m_patched - m_corrupt) / denom


def probe_projection(activation: np.ndarray, vhat: np.ndarray) -> float:
    """Projection of an activation onto the unit design direction (probe-projection proxy; S2.1c)."""
    v = np.asarray(vhat, float)
    n = np.linalg.norm(v)
    if n > 0:
        v = v / n
    return float(np.dot(np.asarray(activation, float), v))


def projection_recovery(patched_act: np.ndarray, corrupt_act: np.ndarray, clean_act: np.ndarray,
                        vhat: np.ndarray) -> float:
    """% recovery measured by movement of the v_hat-projection toward the clean value (S2.1c)."""
    return percent_recovered(
        probe_projection(patched_act, vhat),
        probe_projection(corrupt_act, vhat),
        probe_projection(clean_act, vhat),
    )


# --------------------------------------------------------------------------- model-driven patch (GPU)

def design_token_logit_diff(logits, tok_plus: int, tok_minus: int, position: int = -1) -> float:
    """Delta = logit(t+) - logit(t-) at a response position (THEORY T8.6, design-token proxy).

    t+ = a non-default style token (e.g. a non-'Inter' font-family token, a non-purple hex digit);
    t- = the default. `logits` is [batch, seq, vocab] or [seq, vocab].
    """
    import torch

    L = logits if logits.dim() == 2 else logits[0]
    return float(L[position, tok_plus] - L[position, tok_minus])


def denoising_patch(model, corrupt_ids, clean_vector, layer: int, position: int,
                    metric_fn):  # pragma: no cover - GPU/Colab
    """Patch `clean_vector` into the NEUTRAL run at (layer, position); return metric_fn(logits).

    metric_fn maps the steered logits to a scalar (e.g. a design-token logit diff). Import-guarded;
    the % recovery is computed by the caller against clean/corrupt baselines (S2.1c).
    """
    import torch
    from .hooks import get_hidden, set_hidden, _decoder_layers

    cv = torch.as_tensor(np.asarray(clean_vector))

    def hook(module, inp, output):
        h = get_hidden(output).clone()
        h[:, position, :] = cv.to(h.dtype).to(h.device)
        return set_hidden(output, h)

    handle = _decoder_layers(model)[layer].register_forward_hook(hook)
    try:
        with torch.no_grad():
            logits = model(corrupt_ids).logits
        return metric_fn(logits)
    finally:
        handle.remove()
