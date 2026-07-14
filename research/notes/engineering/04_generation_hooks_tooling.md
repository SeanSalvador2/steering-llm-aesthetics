# D-d / D-e — Generation throughput + hook mechanics (vLLM vs HF; TransformerLens/nnsight)

**Sources.** vLLM docs + vllm-lens (UKGovernmentBEIS) + vLLM issue #36998; HF `transformers` hook API; TransformerLens & nnsight (arXiv:2407.14561) docs.

## Throughput: vLLM vs HF generate (7B bf16)
- **vLLM:** paged-attention + continuous batching → **high throughput** (order 1–2k+ tok/s aggregate with batching on L4/A100); ideal for **Stage-1 bulk generation** (thousands of pages).
- **HF `.generate()`:** ~**30–60 tok/s** single-stream (much lower); acceptable for the smaller **Stage-2 steering-generation** set (held-out prompts only).
- **Determinism caveat (mixing engines):** vLLM and HF can produce **different tokenizations/samples even at the same seed** (different kernels, batching, sampling order). **Policy:** (a) fix sampling config (temperature, top_p, seed) and record engine+version; (b) do **all Stage-1 cells with the same engine** (vLLM) so ablation comparisons are within-engine; (c) do **all Stage-2 steering with HF** (needed for hooks) — and, if any Stage-1↔Stage-2 numeric comparison is made, **re-generate the relevant baseline in HF** so steering deltas are within-engine. Never compare a vLLM baseline directly to an HF steered output.

## Why steering must use HF, not vLLM
- vLLM **does not easily support mid-generation activation mutation**: hooks are **disabled during decode** to preserve CUDA-graph execution; returning an `activation_delta` to edit hidden states in-flight is **explicitly deferred** (latency/stream-blocking risk) per vLLM's own RFC. vllm-lens can *extract* residual activations but steering-injection during generation is not first-class.
- ⇒ **Stage-2 steering (add vector every generated token) uses HF forward hooks.** Confirms **ADR-002**.

## HF hook mechanics on Qwen2 (`Qwen2ForCausalLM`)
- Modules: `model.model.layers[i]` (`Qwen2DecoderLayer`), `i=0..27`. Residual stream = the **layer output hidden state**.
- **Capture (read):** `layer.register_forward_hook(fn)`; the layer returns a **tuple** — hidden state is `output[0]` (shape `[batch, seq, 3584]`). Handle the tuple explicitly.
- **Steering (write):** register a `forward_hook` that returns a modified tuple: `hs = output[0]; hs = hs + alpha * v; return (hs,) + output[1:]`. To inject at the **input** side (pre-block residual), use `register_forward_pre_hook` on the next layer, or hook the residual add point. Both work; pick one and document.
- **KV-cache interaction during generation:** at decode the hook fires **once per generated token** with `seq_len==1` (only the new token's hidden state passes through, since past tokens are cached). So "add to all generated positions" = "add on every decode step" — the hook naturally applies to each new token. For the **prompt/prefill** step the hook sees the full prompt (`seq_len==prompt_len`); decide whether to steer prompt positions too (usually steer generated positions only for our "no-prompt" causal test — but here there's *no design prompt anyway*, so steer all positions of the generated response).
- **Memory:** capturing per-layer **means** (accumulate a running sum over response tokens) is negligible; capturing **full sequences** across 28 layers for 2–4k-token pages is the cost (~0.8 GB/example bf16) → capture only chosen layers or running means.

## TransformerLens / nnsight / baukit
- **TransformerLens:** supports Qwen2-class models via `HookedTransformer.from_pretrained`, clean `run_with_hooks`/`cache`, but **~doubles load memory** (keeps an extra copy / its own weight processing) and a heavier KV path → on Colab memory this is a real cost for a 7B. Good for **exploratory** analysis, **not the critical path** (ADR-002).
- **nnsight** (arXiv:2407.14561): trace-based interventions on stock HF models with low overhead; a solid alternative for probing/patching without TL's memory hit. Reasonable for exploratory patching.
- **baukit** (`TraceDict`): thin wrapper over PyTorch hooks; essentially the minimal custom-hook approach with nicer ergonomics.

## Verdict (feeds D2)
- **Confirm ADR-002:** primary = **plain `transformers` + small custom hook module** (~200 lines, auditable, memory-light, quantization-compatible). Use **vLLM for Stage-1 bulk generation** only. TransformerLens/nnsight = exploratory side-tools, off critical path.
- **Gotchas to encode in `src/hooks/`:** tuple-output handling; per-decode-step firing (seq_len==1); prefill vs decode position handling; capture running means not full sequences by default; record engine+version+seed for determinism; never cross-compare vLLM vs HF outputs.
