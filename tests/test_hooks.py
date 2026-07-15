"""Hook-mechanics tests on a REAL tiny Qwen2 stand-in (THEORY §T8; ADR-002).

Verifies against a manual forward computation: capture == hidden_states; addition shifts the
target layer output by exactly alpha*v_hat; ablation zeroes the v_hat-component of writes;
weight-orthogonalization equals runtime projection-after-every-write (THEORY T8.8). Uses a
randomly-initialized Qwen2 (hidden=64, 3 layers) — NEVER the 7B weights (compute policy).
"""
import copy

import pytest

torch = pytest.importorskip("torch")
from p19 import hooks  # noqa: E402


def _layer_output(model, ids, layer):
    store = {}
    h = model.model.layers[layer].register_forward_hook(
        lambda m, i, o: store.__setitem__("h", hooks.get_hidden(o).detach().clone()))
    with torch.no_grad():
        model(ids)
    h.remove()
    return store["h"]


def test_capture_equals_manual_hidden_states(tiny_qwen2):
    """Running-mean capture equals the manual mean over response-token hidden states (THEORY T8.1)."""
    ids = torch.randint(0, 200, (1, 10))
    with torch.no_grad():
        hs = tiny_qwen2(ids, output_hidden_states=True).hidden_states  # len = n_layers + 1
    caps = hooks.capture_means(tiny_qwen2, ids, layers=[0, 1, 2], response_start=6)
    manual_resp = hs[2][0, 6:, :].mean(0)      # layer-1 output = hidden_states[2]
    assert torch.allclose(caps[1]["mean_response"], manual_resp, atol=1e-5)
    assert torch.allclose(caps[1]["last_prompt_token"], hs[2][0, 5, :], atol=1e-5)


def test_addition_shifts_output_by_alpha_vhat(tiny_qwen2):
    """h <- h + alpha*v_hat shifts the target layer output by exactly alpha*v_hat (THEORY T8.4)."""
    ids = torch.randint(0, 200, (1, 8))
    v = torch.randn(64)
    alpha = 2.5
    base = _layer_output(tiny_qwen2, ids, 1)
    with hooks.addition_hook(tiny_qwen2, 1, v, alpha):
        steered = _layer_output(tiny_qwen2, ids, 1)
    vhat = v / v.norm()
    assert torch.allclose(steered - base, (alpha * vhat).expand_as(base), atol=1e-5)


def test_ablation_zeroes_vhat_component(tiny_qwen2):
    """Directional ablation zeroes the v_hat-component of the layer output (THEORY T8.7)."""
    ids = torch.randint(0, 200, (1, 8))
    v = torch.randn(64)
    with hooks.ablation_hook(tiny_qwen2, v, layers=[1]):
        abl = _layer_output(tiny_qwen2, ids, 1)
    vhat = v / v.norm()
    comp = torch.einsum("bsd,d->bs", abl, vhat)
    assert torch.allclose(comp, torch.zeros_like(comp), atol=1e-5)


def test_weight_orth_equals_runtime_projection(tiny_qwen2):
    """Weight-orthogonalization == runtime project-every-write, on logits (THEORY T8.8)."""
    ids = torch.randint(0, 200, (1, 8))
    v = torch.randn(64)
    m_orth = copy.deepcopy(tiny_qwen2)
    hooks.orthogonalize_weights(m_orth, v)
    with torch.no_grad():
        logits_w = m_orth(ids).logits
    with hooks.ablate_everywhere_runtime(tiny_qwen2, v):
        with torch.no_grad():
            logits_r = tiny_qwen2(ids).logits
    assert torch.allclose(logits_w, logits_r, atol=1e-4)


def test_tuple_output_handling(tiny_qwen2):
    """get_hidden/set_hidden preserve the layer's tuple output (04_generation_hooks_tooling)."""
    out = (torch.zeros(1, 3, 64), "kv")
    assert hooks.get_hidden(out).shape == (1, 3, 64)
    new = hooks.set_hidden(out, torch.ones(1, 3, 64))
    assert isinstance(new, tuple) and new[1] == "kv" and new[0].sum() == 192
