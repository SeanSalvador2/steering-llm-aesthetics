# D-a — Qwen2.5-Coder-7B-Instruct: verified facts (config, license, tooling)

**Sources.** HF model card `Qwen/Qwen2.5-Coder-7B-Instruct` + its `config.json` (fetched); Qwen2.5-Coder Technical Report (arXiv:2409.12186); Qwen2 Technical Report (arXiv:2407.10671).

## License & provenance
- **License: Apache-2.0** (per model card tags). No gating. ✅ satisfies open-weights + redistributable requirement for both stages. (Contrast: Llama-3.1 is gated community license — D-b.)
- 7.62B params; base `Qwen2.5-Coder-7B` → instruct finetune; family 0.5/1.5/3/7/14/32B; continued-pretrained on **5.5T tokens** of code-heavy data on the Qwen2.5 architecture; SOTA on 10+ code benchmarks per the tech report.
- Model-card references: arXiv:2409.12186 (Coder report), 2407.10671 (Qwen2), 2309.00071 (YaRN long-context).

## Exact architecture (from config.json — needed for hooks/steering)
| field | value |
|---|---|
| architectures | `Qwen2ForCausalLM` |
| hidden_size ($d_{model}$) | **3584** |
| num_hidden_layers | **28** |
| num_attention_heads | 28 |
| num_key_value_heads | **4** (grouped-query attention) |
| head_dim | 128 (=3584/28) |
| intermediate_size (MLP) | 18944 |
| hidden_act | silu (SwiGLU MLP) |
| vocab_size | 152064 |
| max_position_embeddings | 32768 |
| rope_theta | 1,000,000 |
| sliding_window | 131072 (config field; effectively no SWA at 32k ctx) |
| rms_norm_eps | 1e-6 |
| tie_word_embeddings | **false** |
| torch_dtype | bfloat16 |

**Consequences for Stage 2.**
- Residual stream width **3584**; steering/probe vectors live in $\mathbb{R}^{3584}$ per layer.
- **28 decoder layers** → mid-network band ~layers **11–20** (40–70% depth) is the primary scan range (matches CAA layer 13/32, persona layers 12–16 — see below scaling).
- Hook target modules: `model.model.layers[i]` (each a `Qwen2DecoderLayer`); residual stream = the layer's output hidden state (tuple[0]).
- GQA (4 KV heads) doesn't affect residual-stream capture/injection (we hook the block output/input, not attention internals).

## Memory (bf16)
- Weights ≈ **15.2 GB** bf16 (7.62B × 2 bytes). Fits **A100-40GB** comfortably, **L4-24GB** workable (leaves ~8GB for KV cache/activations), **T4-16GB** only via 4-bit (generation-only; not for activation work). 4-bit ≈ 5–6 GB.
- Capturing per-layer **means** (one 3584-vector/layer) is negligible; capturing **full sequences** ×28 layers for long HTML (2–4k tokens) is the memory driver — 3584×4000×28×2 bytes ≈ **0.8 GB/example** in bf16 → capture selectively (chosen layers, or running mean over response tokens).

## Chat template & default-styling tendency
- Uses the Qwen2 ChatML template: `<|im_start|>system\n…<|im_end|>\n<|im_start|>user\n…<|im_end|>\n<|im_start|>assistant\n`. Apply via `tokenizer.apply_chat_template(...)`. **The steering "post-instruction position" = tokens after the user turn / at the assistant-start region** — locate empirically (D3).
- **Default aesthetic:** as a code specialist trained on GitHub/Tailwind-heavy data, it is widely reported to default to generic bootstrap/utility-class styling — the "AI slop" the skill moves (A5). Good subject: strong enough to *apply* a multi-part skill, weak enough (aesthetically) to have room to move. Instruction-following is solid (instruct finetune) though below frontier API models — acceptable since we measure *deltas*, not absolute SOTA.

## Verdict (feeds D1)
Apache-2.0, standard `Qwen2ForCausalLM` (fully HF-hookable), fits Colab L4/A100 in bf16, same family as Persona Vectors' validated Qwen2.5-7B-Instruct. **Confirms ADR-001** as feasible; no license or hookability blocker. Only caveat: it's a *code* model (weaker general instruction-following than chat models) — fine for our delta-measurement design, and it maximizes render-success (the point of a code specialist).
