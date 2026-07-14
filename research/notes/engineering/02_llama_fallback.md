# D-b — Fallback: Llama-3.1-8B-Instruct facts

**Sources.** HF Llama-3.1-8B-Instruct config (via search of NousResearch mirror + HF docs); *The Llama 3 Herd of Models* (arXiv:2407.21783).

## License (the main differentiator vs Qwen)
- **Llama 3.1 Community License** — *gated*: requires accepting Meta terms / HF access request; imposes an **acceptable-use policy** and a **700M-MAU** clause. Not OSI-open. → adds friction (access approval, redistribution constraints) and is why Qwen (Apache-2.0) is the primary. Usable for research but confirm access before depending on it.

## Architecture (from config.json)
| field | value |
|---|---|
| architectures | `LlamaForCausalLM` |
| hidden_size | **4096** |
| num_hidden_layers | **32** |
| num_attention_heads | 32 |
| num_key_value_heads | **8** (GQA) |
| intermediate_size | 14336 |
| hidden_act | silu (SwiGLU) |
| vocab_size | 128256 |
| max_position_embeddings | 131072 |
| rope_theta | 500000 + `rope_scaling` (factor 8, llama3 type) |
| torch_dtype | bfloat16 |

- Weights ≈ **16.1 GB** bf16 (8.03B). Similar Colab footprint to Qwen-Coder.
- Residual width 4096; 32 layers → mid band ~13–22.

## Interp-tooling advantage / code disadvantage
- **Public SAE suite exists: Llama Scope** (arXiv:2410.20526, 256 Top-K SAEs, 32K/128K features, all layers/sublayers of the *base* model). So if the SAE stretch goal (ADR-008/D9) were pursued, Llama-3.1-8B has infrastructure Qwen2.5-Coder lacks — a point *for* Llama as fallback. But SAEs are base-model (not instruct), and AxBench shows DiffMean ≥ SAE anyway.
- **Code/frontend ability weaker** than Qwen2.5-Coder (general model vs code specialist) → likely lower render-success and a *different* default aesthetic. Since the whole point is generating working UIs and measuring the skill's effect, the weaker code ability is the reason it's the fallback, not the primary.
- Persona Vectors (B9) validated on **both** Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct → whichever we use, the diff-in-means extraction is known-feasible.

## Verdict
Viable fallback with (a) license gating friction and (b) weaker code ability, offset by (c) a mature SAE ecosystem. Keep as recorded fallback per ADR-001; switching requires an ADR and restarts both stages. If cross-model transfer of the design direction becomes a headline (creative latitude), Llama-3.1-8B is the natural second model *for the transfer experiment* even if Qwen stays primary.
