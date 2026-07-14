# The SAE line & the 2025–26 SAE-skepticism (survey cluster) — gates ADR-008

## Foundational SAE work
- **Bricken et al. 2023, Towards Monosemanticity** (transformer-circuits.pub/2023): sparse autoencoders decompose a 1-layer transformer's activations into many **monosemantic** features via dictionary learning ($L_1$-penalized overcomplete autoencoder on residual/MLP activations).
- **Templeton et al. 2024, Scaling Monosemanticity** (transformer-circuits.pub/2024): scales SAEs to **Claude 3 Sonnet**; trains dictionaries of **~1M / 4M / 34M** features. **Feature steering demo:** *clamping* a feature (setting its activation to a fixed value) to **~10× its max observed activation** induces the concept — the "Golden Gate Bridge" feature makes the model obsess over / self-identify as the bridge. Features get *less specific* as activation weakens. Establishes clamp-based steering as the SAE control primitive.

## Open SAE suites (availability matters for D9)
- **Gemma Scope — Lieberum et al. 2024 (arXiv:2408.05147):** JumpReLU SAEs on **all layers/sublayers of Gemma-2 2B/9B** (+ select 27B). The most complete open suite; why AxBench uses Gemma.
- **Llama Scope — He et al. 2024 (arXiv:2410.20526):** 256 Top-K SAEs on **Llama-3.1-8B-Base**, 32K & 128K features per layer/sublayer.
- **Qwen-Scope — Deng et al. 2026 (arXiv:2605.11887):** SAE suite for the **Qwen3 / Qwen3.5** family (dense + MoE), with inference-time steering demos. **No public SAE suite exists for Qwen2.5-Coder-7B** — training one is out of scope on Colab. (Directly relevant to D9.)

## The skepticism (why SAEs are demoted to stretch)
- **AxBench — Wu et al. 2025 (B5):** in the largest head-to-head, **DiffMean > SAEs** for steering and detection; SAEs "not competitive." Prompting/finetuning beat all representation methods for steering.
- **Mayne et al. 2024 (arXiv:2411.08790):** SAEs **cannot faithfully decompose steering vectors** — steering vectors are off the SAE's input distribution and can have meaningful *negative* projections SAEs don't model. So you can't cleanly "explain" a diff-in-means design vector via SAE features.
- **Ronge et al. 2026 (arXiv:2601.03047), "coffee feature on coffins":** replicating Anthropic-style SAE steering on Llama-3.1 open SAEs, feature steering is **fragile** — sensitive to layer, magnitude, context; hard to distinguish thematically similar features. Recommends shifting from interpreting internals to reliably predicting/controlling outputs.
- **Partial rebuttals (honest balance):** Arad et al. 2025 (arXiv:2505.20063) get **2–3× SAE steering** by filtering for "output features" (not just input-activating ones); Jørgensen & Hansen 2026 (arXiv:2605.31183) approach LoRA on AxBench with a better supervised feature-selection pipeline. So SAEs *can* work with careful selection — but require infrastructure we don't have for our model.

## Net for Project 19 (D9)
Confirm **ADR-008**: SAE-feature steering is a **stretch**, not the primary method. Reasons compound: (1) no Qwen2.5-Coder SAE suite; (2) DiffMean out-competes SAEs by default (AxBench); (3) SAEs are fragile and don't even faithfully decompose steering vectors. If pursued at all, it would be an *optional* extension using Qwen-Scope-style tooling on a *different* Qwen model — but that breaks the "same model both stages" rule, so keep it strictly off the critical path.
