"""Residual-stream hooks: capture, addition, ablation, weight-orthogonalization (THEORY §T8; ADR-002).

All operations target `model.model.layers[i]` output `[0]` (shape [batch, seq, d]), with explicit
tuple-output handling and per-decode-step firing (seq_len==1 at decode) per 04_generation_hooks_tooling.
Heavy deps are import-guarded so the module imports without torch; functions raise a clear error.

Operations:
  capture      running-mean over response tokens / last-prompt-token / first-k (activations corpus)
  addition     h <- h + alpha * v_hat,  alpha = rho * mean||h||  (norm-relative) or m * ||v||  (abs)
  ablation     h <- h - v_hat v_hat^T h = P h    (directional ablation; flip test)
  weight-orth  bake P into every residual-writing matrix (equivalent to runtime ablation; T8.7/T8.8)

The tiny-model unit tests (tests/test_hooks.py) verify each against a manual forward computation on a
randomly-initialized Qwen2 stand-in (hidden~64, 2-4 layers) — NEVER the 7B weights.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Callable

try:  # import-guarded (GPU-phase dependency)
    import torch
    import torch.nn as nn
    _HAS_TORCH = True
except Exception:  # pragma: no cover
    torch = None
    nn = None
    _HAS_TORCH = False


def _require_torch():
    if not _HAS_TORCH:
        raise ImportError("p19.hooks requires torch (extra 'gpu'); runs on Colab.")


def get_hidden(output):
    """Layer output -> hidden state tensor (handles tuple or bare-tensor returns)."""
    return output[0] if isinstance(output, tuple) else output


def set_hidden(output, new_hidden):
    """Rebuild a layer output with `new_hidden` as [0], preserving the rest of the tuple."""
    if isinstance(output, tuple):
        return (new_hidden,) + tuple(output[1:])
    return new_hidden


def _decoder_layers(model):
    """The list of Qwen2DecoderLayer modules (model.model.layers)."""
    return model.model.layers


# --------------------------------------------------------------------------- capture

class RunningMeanCapture:
    """Accumulate per-layer residual statistics over a forward pass (THEORY T8.1 sites).

    For each hooked layer collects: running sum over the RESPONSE token positions (mean_response),
    the last-prompt-token vector, and the first-k response tokens' running sum. `response_start`
    is the index of the first response token in the (single) sequence; during incremental decode
    the hook fires with seq_len==1 (a new token) and each such token is a response token.
    """

    def __init__(self, model, layers, response_start: int = 0, first_k: int = 64):
        _require_torch()
        self.model = model
        self.layers = list(layers)
        self.response_start = response_start
        self.first_k = first_k
        self._handles = []
        self.sum_resp = {li: None for li in self.layers}
        self.count_resp = {li: 0 for li in self.layers}
        self.last_prompt = {li: None for li in self.layers}
        self.sum_firstk = {li: None for li in self.layers}
        self.count_firstk = {li: 0 for li in self.layers}
        self._seen = 0  # tokens consumed across incremental steps

    def _make_hook(self, li):
        def hook(module, inp, output):
            h = get_hidden(output)  # [batch, seq, d]
            b, seq, d = h.shape
            # prefill (seq == full prompt+...) vs decode (seq == 1)
            for t in range(seq):
                global_pos = self._seen + t if seq == 1 else t
                vec = h[:, t, :].detach().mean(dim=0)  # mean over batch
                if seq > 1 and t == self.response_start - 1:
                    self.last_prompt[li] = vec.clone()
                is_response = (global_pos >= self.response_start) if seq > 1 else True
                if is_response:
                    self.sum_resp[li] = vec.clone() if self.sum_resp[li] is None else self.sum_resp[li] + vec
                    self.count_resp[li] += 1
                    rk = self.count_resp[li] - 1
                    if rk < self.first_k:
                        self.sum_firstk[li] = vec.clone() if self.sum_firstk[li] is None else self.sum_firstk[li] + vec
                        self.count_firstk[li] += 1
            return output
        return hook

    def __enter__(self):
        layers = _decoder_layers(self.model)
        for li in self.layers:
            self._handles.append(layers[li].register_forward_hook(self._make_hook(li)))
        return self

    def note_step(self, n_new_tokens: int):
        """Advance the global-position counter after an incremental decode step."""
        self._seen += n_new_tokens

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []

    def mean_response(self, li):
        return None if self.sum_resp[li] is None else self.sum_resp[li] / max(1, self.count_resp[li])

    def mean_first_k(self, li):
        return None if self.sum_firstk[li] is None else self.sum_firstk[li] / max(1, self.count_firstk[li])


def capture_means(model, input_ids, layers, response_start: int = 0, first_k: int = 64) -> dict:
    """Single teacher-forced forward pass -> per-layer {mean_response, last_prompt_token, first_k}."""
    _require_torch()
    with torch.no_grad(), RunningMeanCapture(model, layers, response_start, first_k) as cap:
        model(input_ids)
        out = {}
        for li in layers:
            out[li] = {
                "mean_response": cap.mean_response(li),
                "last_prompt_token": cap.last_prompt[li],
                "first_k": cap.mean_first_k(li),
            }
    return out


# --------------------------------------------------------------------------- addition (steering)

def _unit(v):
    return v / (v.norm() + 1e-12)


@contextmanager
def addition_hook(model, layer: int, vector, alpha: float, normalize: bool = True):
    """Add alpha * v_hat to a layer's output at all positions (THEORY T8.4). Context-managed."""
    _require_torch()
    v = _unit(vector) if normalize else vector
    add = alpha * v

    def hook(module, inp, output):
        h = get_hidden(output)
        return set_hidden(output, h + add.to(h.dtype).to(h.device))

    handle = _decoder_layers(model)[layer].register_forward_hook(hook)
    try:
        yield
    finally:
        handle.remove()


def norm_relative_alpha(mean_norm: float, rho: float) -> float:
    """alpha = rho * mean||h_l||  (norm-relative parameterization; THEORY T8.4)."""
    return rho * mean_norm


def absolute_alpha(v_norm: float, m: float) -> float:
    """alpha = m * ||v_l||  (absolute parameterization; THEORY T8.4)."""
    return m * v_norm


# --------------------------------------------------------------------------- ablation (flip test)

@contextmanager
def ablation_hook(model, vector, layers=None):
    """Project v_hat OUT of the residual stream at the given layers' outputs (THEORY T8.7).

    h <- h - v_hat (v_hat^T h) = P h, P = I - v_hat v_hat^T. If layers is None, all layers.
    """
    _require_torch()
    v = _unit(vector)
    handles = []
    layer_list = _decoder_layers(model)
    idxs = range(len(layer_list)) if layers is None else layers

    def make_hook():
        def hook(module, inp, output):
            h = get_hidden(output)
            vv = v.to(h.dtype).to(h.device)
            coef = torch.einsum("...d,d->...", h, vv).unsqueeze(-1)
            return set_hidden(output, h - coef * vv)
        return hook

    for i in idxs:
        handles.append(layer_list[i].register_forward_hook(make_hook()))
    try:
        yield
    finally:
        for hd in handles:
            hd.remove()


def project_out(h, vector):
    """Utility: P h = h - v_hat (v_hat^T h) (THEORY T8.7). Used in probes/patching."""
    _require_torch()
    v = _unit(vector).to(h.dtype).to(h.device)
    coef = torch.einsum("...d,d->...", h, v).unsqueeze(-1)
    return h - coef * v


# --------------------------------------------------------------------------- weight orthogonalization

def orthogonalize_weights(model, vector, layers=None, include_embedding: bool = True) -> None:
    """Bake P = I - v_hat v_hat^T into every residual-writing matrix (THEORY T8.7/T8.8).

    Projects the token embedding and each layer's attn o_proj + mlp down_proj (the residual writes),
    so no site can re-introduce v_hat — a static ablated model needing no inference hook. Modifies
    the model IN PLACE (clone first if you need the original). `layers=None` -> all layers.
    """
    _require_torch()
    v = _unit(vector).detach()
    d = v.shape[0]
    P = (torch.eye(d, dtype=v.dtype, device=v.device) - torch.outer(v, v))

    with torch.no_grad():
        if include_embedding:
            emb = model.model.embed_tokens.weight  # [vocab, d]; each row is a residual write
            emb.copy_((emb.to(P.dtype) @ P).to(emb.dtype))
        layer_list = _decoder_layers(model)
        idxs = range(len(layer_list)) if layers is None else layers
        for i in idxs:
            layer = layer_list[i]
            # attn output projection: y = x Wo^T ; project output -> Wo <- P Wo
            wo = layer.self_attn.o_proj
            wo.weight.copy_((P @ wo.weight.to(P.dtype)).to(wo.weight.dtype))
            if getattr(wo, "bias", None) is not None:
                wo.bias.copy_((P @ wo.bias.to(P.dtype)).to(wo.bias.dtype))
            # mlp down projection: writes to residual -> project output
            wd = layer.mlp.down_proj
            wd.weight.copy_((P @ wd.weight.to(P.dtype)).to(wd.weight.dtype))
            if getattr(wd, "bias", None) is not None:
                wd.bias.copy_((P @ wd.bias.to(P.dtype)).to(wd.bias.dtype))


@contextmanager
def ablate_everywhere_runtime(model, vector):
    """Runtime counterpart of weight-orth: project EVERY residual write (THEORY T8.8).

    Projects the token-embedding output, each attention sub-block output (the o_proj write), and
    each MLP sub-block output (the down_proj write) — the exact set orthogonalize_weights bakes in.
    Projecting only the layer output would differ, because the post-attention norm must read the
    already-projected attention write; used in the equivalence unit test.
    """
    _require_torch()
    v = _unit(vector)
    handles = []

    def emb_hook(module, inp, output):
        return project_out(output, v)

    def attn_hook(module, inp, output):
        h = get_hidden(output)
        return set_hidden(output, project_out(h, v))

    def mlp_hook(module, inp, output):
        return project_out(output, v)  # mlp returns a bare tensor (down_proj write)

    handles.append(model.model.embed_tokens.register_forward_hook(emb_hook))
    for layer in _decoder_layers(model):
        handles.append(layer.self_attn.register_forward_hook(attn_hook))
        handles.append(layer.mlp.register_forward_hook(mlp_hook))
    try:
        yield
    finally:
        for hd in handles:
            hd.remove()
