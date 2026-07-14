# B2 — Contrastive Activation Addition (Rimsky 2024) + Activation Addition / ActAdd (Turner 2023)

**Citations.**
- Rimsky, Gabrieli, Schulz, Tong, Hubinger, Turner. *Steering Llama 2 via Contrastive Activation Addition (CAA).* ACL 2024. arXiv:2312.06681.
- Turner, Thiergart, Udell, Leech, Mini, MacDiarmid. *Activation Addition: Steering Language Models Without Optimization (ActAdd).* arXiv:2308.10248.

**TL;DR.** Two closely related recipes for building a steering vector from *contrastive prompt pairs* and adding it to the residual stream at inference. CAA averages the residual-stream difference over many A/B behavioural pairs at a chosen layer; ActAdd uses a single natural-language prompt pair and adds the difference at chosen positions/layer. Together they fix the concrete knobs we must set: pair construction, extraction position, layer choice, coefficient sweep, and injection positions.

## Method, in depth — CAA

**Contrastive pairs.** Each item is a multiple-choice behavioural question with a matched (A) behaviour-positive and (B) behaviour-negative answer letter, e.g. sycophantic vs non-sycophantic response to the same prompt. Behaviours: sycophancy, corrigibility, hallucination, refusal, survival-instinct, myopia (from Anthropic's Model-Written Evals). ~Hundreds of pairs per behaviour.

**Extraction position.** Activations are read at the residual stream of the token position of the **answer letter (A/B)** — a single, aligned position across the contrast pair, so only the behaviour differs. Steering vector:
$$v_l = \frac{1}{N}\sum_{k=1}^{N}\big(a_l^{+}(k) - a_l^{-}(k)\big),$$
mean over $N$ pairs of the residual difference at layer $l$.

**Layer.** For **Llama-2-7B-Chat the best layer is 13** (of 32); mid-network. Extracted once per behaviour per layer; layer swept to pick the most effective.

**Injection.** At inference $v_l$ is added to the residual stream at layer $l$ **at all token positions after the user's prompt** (i.e. every generated position), scaled by a multiplier. **Multiplier sweep: $\{-2,-1.5,-1,-0.5,0,0.5,1,1.5,2\}$** — positive amplifies the behaviour, negative suppresses it, roughly monotone in a usable band before coherence degrades.

**Evaluation.** (i) Multiple-choice: shift in $p(\text{A})$ vs $p(\text{B})$. (ii) Open-ended generation scored by GPT-4 on a behavioural rubric, both presentation orders. CAA beats few-shot prompting and is competitive with/there beyond finetuning, with small capability cost. On the 7B model, sycophantic few-shot prompting "does basically nothing" while CAA moves the behaviour strongly — evidence that activation steering can exceed prompting for some behaviours.

## Method, in depth — ActAdd
- Steering vector from **one** contrastive natural-language prompt pair (e.g. "love" − "hate"): run both, take the residual-stream **difference at a chosen layer**, add $\alpha\,\Delta$ to the forward pass on the user prompt.
- Positions: added at a chosen span of token positions (alignment by padding the shorter prompt). Demonstrated on GPT-2, GPT-J-6B, Llama-13B; controls high-level attributes (topic/sentiment) while preserving off-target perplexity.
- Much cheaper than CAA (no dataset) but noisier (single pair) — CAA's averaging is the robustness upgrade.

## Key results & numbers
- CAA best layer 13/32 (Llama-2-7B), multipliers $[-2,2]$, inject all post-prompt positions.
- Steering exceeds few-shot prompting for sycophancy on 7B; minimal MMLU degradation in the usable multiplier band.

## Limitations / critiques
- CAA's per-example effect is **highly variable** — Tan et al. 2024 (B4) show large per-input steerability variance and anti-steerable examples for CAA specifically.
- Single-position (answer-letter) extraction is tailored to A/B tasks; long free-form generation (our case) has no such canonical position — must choose (see D3).
- Multiplier band is behaviour- and model-specific; too large a coefficient breaks fluency (see Taimeskhanov 2026 on non-monotonic strength).

## Relevance to Project 19
CAA is our operational template for *building and injecting* the design steering vector once the layer is located (Arditi provides the selection discipline; CAA provides the mean-difference-over-pairs + inject-all-positions mechanics). The multiplier sweep $[-2,2]$ and "all positions after the prompt" injection are directly adoptable defaults. ActAdd motivates the length-matched-neutral control: because a steering vector can be *implicitly specified by a prompt pair*, our skill-vs-neutral pair is a principled ActAdd-style contrast whose difference should encode "design guidance content."

## Borrow
- Mean-difference over many contrastive pairs (CAA averaging), not a single pair.
- Inject at all generated positions; sweep coefficient over a symmetric band around 0; report the coherence-preserving range.
- Evaluate with both A/B (objective, cheap) and open-ended (judge, both orders) — mirrors our two-signal oracle.

## Avoid
- Don't rely on a single contrast pair (ActAdd-style) for the headline vector — too noisy; use averaged diff-in-means.
- Don't assume one global multiplier transfers across prompts — Tan (B4) shows per-example variance; report distributions and the anti-steerable fraction.
