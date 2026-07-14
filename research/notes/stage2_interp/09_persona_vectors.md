# B9 — Persona Vectors: Monitoring and Controlling Character Traits (Chen et al. 2025, Anthropic)

**Citation.** Chen, Arditi, Sleight, Evans, Lindsey. *Persona Vectors: Monitoring and Controlling Character Traits in Language Models.* arXiv:2507.21509 (Anthropic, 2025).

**TL;DR.** An **automated** pipeline that, from only a natural-language *trait description*, builds contrastive prompts, elicits opposing behaviours, and extracts a trait direction by **difference-in-means of response activations**. The vector then (a) *monitors* trait expression by projection, (b) *steers* it, and (c) supports **preventative steering** during finetuning. Crucially, it is validated on **Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct** — our exact subject-model family — making it the closest methodological cousin and a strong feasibility signal.

## Method, in depth

**Automated extraction pipeline.** Given a trait description $T$ (e.g. "evil", "sycophantic", "hallucinating"): an LLM auto-generates (i) a contrastive system-prompt pair (trait-eliciting vs trait-suppressing) and (ii) evaluation questions. The model generates responses under each side. Activations are collected over the **response tokens** (mean over generated tokens) and the persona vector is the **difference of mean activations between trait-expressing and non-expressing responses** at a layer $l$:
$$v_T = \overline{h_l}^{\,(\text{trait})} - \overline{h_l}^{\,(\text{no-trait})}.$$
This is diff-in-means over *response* activations (not prompt tokens) — the right statistic for behaviour that manifests in the output, exactly our situation.

**Layer.** Middle layers are the sweet spot (reported ~layers 12–16 region for these ~7–8B models); the vector is extracted per layer and the effective one chosen mid-network.

**Monitoring.** Project the activation at the **final prompt token** onto $v_T$ *before generation*; this projection **predicts the behavioural shift** with correlations ≈ **0.75–0.83** across prompt conditions. I.e. you can forecast whether the model will express the trait from a single dot product.

**Steering (control).** Add $\alpha v_T$ during generation to induce/suppress the trait; effect scales with $\alpha$ (usual coherence trade-off at large $\alpha$).

**Preventative steering (training-time).** During finetuning that would otherwise induce an unwanted trait, *add* the persona vector during training so the model doesn't need to *learn* the trait to fit the data — inoculation that limits the unwanted personality shift while preserving capability. They also use persona projection to **flag training data** likely to induce trait shifts, at dataset and per-sample level.

## Key results & numbers
- Fully automated from a text description; applied to traits (evil, sycophancy, hallucination) on **Qwen2.5-7B-Instruct** and **Llama-3.1-8B-Instruct**.
- Pre-generation projection predicts behaviour, r ≈ 0.75–0.83.
- Finetuning-induced (intended and unintended) personality changes correlate strongly with shifts along the relevant persona vector; preventative steering mitigates them.

## Limitations / critiques
- Traits are still relatively unitary (evil/sycophancy); "clean design" is a bundle of sub-behaviours (color/layout/type) — may be several directions, not one (test with our LOO components ↔ directions correspondence).
- Auto-generated contrast prompts can encode spurious cues; same control discipline needed.

## Relevance to Project 19
This is the **strongest de-risking evidence** for Stage 2: the *identical* extraction method (auto contrastive prompts → diff-in-means over response activations → mid-layer vector → project-to-monitor / add-to-steer) already works on **Qwen2.5-7B-Instruct**. Our "clean-design vector" is a persona-vector-style trait, and our length-matched-neutral control is the trait-suppressing side done rigorously. Their **monitoring-by-projection** gives us a cheap pre-render quality predictor; their **preventative-steering** framing hints at an optional extension (inoculate against "AI slop" at train time). The r≈0.8 projection-predicts-behaviour result sets a concrete target for our "does the design projection predict rendered quality?" analysis.

## Borrow
- Diff-in-means over **response** tokens, mid layers (~12–16 of 28 for our 28-layer Qwen-Coder → scan ~40–70% depth).
- **Projection-at-final-prompt-token as a pre-generation quality monitor**; report its correlation with rendered objective/preference scores.
- Automated contrastive-prompt construction — but for us the contrast is fixed (skill vs neutral), reducing spurious-cue risk.
- Same-family precedent means our hooking/extraction on Qwen2.5 is known-feasible.

## Avoid
- Assuming one "design vector" suffices — probe for multiple (color/layout/type) sub-directions, mirroring Stage-1 components.
- Over-reading the monitoring correlation as causation — still run the steer-with-no-prompt causal test (our hard bar).
