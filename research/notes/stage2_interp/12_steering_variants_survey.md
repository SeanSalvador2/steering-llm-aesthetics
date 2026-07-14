# Steering variants, strength control, conditional steering, code-steering (survey cluster)

## Conditional / clamped steering
- **CAST — Lee et al. 2024 (arXiv:2409.05907, ICLR 2025 spotlight):** *Conditional Activation Steering.* Extract two vectors — a **behavior vector** and a **condition vector**. At inference, compute cosine similarity between the current hidden state and the condition vector; **only if it exceeds a threshold** is the behavior vector added. Enables rules like "if input is X, steer; else don't." **Relevance:** our design steering could be gated to *fire only on UI-generation prompts* — avoids polluting non-UI generations and is a clean way to bound side-effects. Also a template for measuring *where* steering should/shouldn't fire (our failure-surface map).

## Strength control & guardrails
- **Taimeskhanov et al. 2026, Towards Understanding Steering Strength (arXiv:2602.02712):** first theory of steering *magnitude*; derives qualitative laws for next-token prob, concept presence, cross-entropy vs coefficient — including **non-monotonic** effects (more steering isn't monotonically more concept). **Relevance:** justifies a careful $\alpha$ sweep with a **coherence/KL guardrail**, not a fixed large $\alpha$; expect a sweet spot.
- **Norm-relative $\alpha$:** common practice (and implied by Style Vectors/persona) is to scale $\alpha$ relative to the **per-layer residual-stream norm** so the same nominal strength transfers across layers/positions. We should parameterize $\alpha$ as a fraction of $\lVert x_l\rVert$ (relative) in addition to absolute, and report both.
- **KL / fluency gate:** cap steering where KL divergence from the unsteered next-token distribution (or a fluency/perplexity proxy) exceeds a threshold — operationalizes "don't steer into gibberish."

## Reliability / geometry cautions (beyond Tan B4)
- **Da Silva et al. 2025, Steering off Course (arXiv:2504.04635):** across 36 models/14 families (1.5B–70B), DoLa/function-vector/task-vector steering is *highly variable* — many models show no improvement or degradation. Assumptions behind these methods are fragile at scale.
- **Wollschläger et al. 2025, Concept Cones (arXiv:2502.17420):** refusal is mediated by **multiple independent directions / multi-dimensional cones**, not one — cross-check for our single-design-direction claim.
- **Understanding-Steering-Strength / non-identifiability (arXiv:2602.06801):** under single-layer white-box access, many behaviorally-equivalent steering vectors exist (large null-space equivalence classes) — so "we found *the* direction" is over-strong; frame as "a causally sufficient direction." Motivates our **norm-matched random-vector control** (a random direction of equal norm should *not* reproduce the effect).

## Steering skills / code specifically (novelty check for D12)
- **van der Weij et al. 2024, Extending Activation Steering to Broad Skills (arXiv:2403.05767):** steer *broad* capabilities including **coding ability** (general vs Python-specific); combining several behavior vectors into one is largely unsuccessful, but **injecting several vectors at different layers simultaneously is promising**. Closest prior on *steering code models*, but targets capability up/down, **not visual/aesthetic quality of generated UIs**.
- **Textual steering vectors improve MLLM visual understanding (arXiv:2505.14071):** mean-shift text-derived vectors boost multimodal spatial/counting accuracy — steering can touch *visual* competence, but not aesthetic code generation.
- **Broad search result:** activation steering has been applied to text, code, music, chain-of-thought — but **no located work steers the visual/aesthetic quality of frontend/UI code generation.** This is our novelty (see DECISIONS_INPUT D12).

## Net for Project 19
- Adopt a principled $\alpha$ sweep with **norm-relative** parameterization and a **KL/coherence guardrail** (expect non-monotonicity).
- Include the **norm-matched random-direction control** (non-identifiability) and the **directional-ablation flip test** (necessity) as the two causal guards.
- Consider **CAST-style conditional gating** so design steering fires only on UI prompts (bounds side effects; cleaner failure-surface story).
- Multi-vector-at-different-layers (van der Weij) is the fallback if a single design vector under-steers.
