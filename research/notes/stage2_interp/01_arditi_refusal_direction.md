# B1 — Refusal in LLMs Is Mediated by a Single Direction (Arditi et al. 2024)

**Citation.** Arditi, Obeso, Syed, Paleka, Rimsky, Gurnee, Nanda. *Refusal in Language Models Is Mediated by a Single Direction.* NeurIPS 2024. arXiv:2406.11717.

**TL;DR.** Across 13 open chat models (up to 72B), refusal behaviour is governed by a single linear direction in the residual stream. Adding the direction forces refusal on harmless prompts; ablating (projecting out) it everywhere disables refusal. This is **the** methodological template for our Stage 2: difference-in-means extraction, systematic layer/position selection, two dual causal interventions (addition + directional ablation), and coherence checks.

## Method, in depth

**Difference-in-means direction.** For a layer $l$ and post-instruction token position $i$, collect mean residual-stream activations over a harmful set $D^{(\text{harmful})}$ and harmless set $D^{(\text{harmless})}$:
$$\mu_l^{(i)} = \frac{1}{|D_{\text{harmful}}|}\sum_{t\in D_{\text{harmful}}} x_l^{(i)}(t), \qquad \nu_l^{(i)} = \frac{1}{|D_{\text{harmless}}|}\sum_{t\in D_{\text{harmless}}} x_l^{(i)}(t),$$
$$r_l^{(i)} = \mu_l^{(i)} - \nu_l^{(i)}.$$
This "diff-in-means" isolates the concept while cancelling nuisance directions common to both sets — the paper explicitly argues it is cleaner than PCA or a trained probe because it is a *causal* mean shift, not a discriminative boundary.

**Direction selection.** They generate one candidate $r_l^{(i)}$ for every (layer, position) pair, then **select a single winner on a validation set** by which candidate, when used for both interventions, most increases refusal on harmless prompts and most bypasses refusal on harmful prompts while keeping the model coherent. In practice the winning layer is around the middle of the network (roughly 60–80% depth; e.g. layer ~12–14 of a 32-layer model region for the smaller models). Position: last few post-instruction tokens (the chat template's post-instruction region), not the raw instruction tokens.

**Intervention 1 — activation addition (elicit refusal).** Add the (unit-normalised) direction at layer $l$ across all token positions during generation:
$$x' \leftarrow x + \alpha\,\hat r_l, \quad \hat r = r/\lVert r\rVert.$$

**Intervention 2 — directional ablation / weight orthogonalization (suppress refusal).** Project the direction out of the stream at *every* layer and position:
$$x' \leftarrow x - \hat r\,\hat r^{\top} x.$$
Because this is linear, it can be baked into the weights: for every matrix $W_{\text{out}}$ writing to the residual stream (attention $W_O$, MLP $W_{\text{down}}$, embedding), replace $W_{\text{out}} \leftarrow (I - \hat r\hat r^{\top})W_{\text{out}}$. This yields a **weightorthogonalized** model that never refuses, with no inference-time hook — a "white-box jailbreak."

**Datasets/sizes.** Harmful instructions from AdvBench / harmful-instruction sets; harmless from Alpaca. Means computed over a few hundred prompts per side (order 128–512); validation/test splits held out. Evaluation: **refusal score** (substring/classifier detection of refusal phrases) and a **safety score** (does the completion actually comply with harm). Coherence checked on MMLU, ARC, GSM8K, TruthfulQA — orthogonalized models hold performance except a consistent TruthfulQA drop (that dataset overlaps safety/conspiracy content).

## Key results & numbers
- One direction, 13 models to 72B. Weight-orthogonalization attack-success comparable to GCG adversarial suffixes but with negligible capability loss.
- Adversarial suffixes (GCG) work by **suppressing propagation** of the refusal direction — attention heads redirect from the harmful instruction to the suffix.
- Coherence: MMLU/ARC essentially unchanged post-ablation; TruthfulQA drops.

## Limitations / critiques
- **Single-direction claim contested.** Wollschläger et al. 2025 (Concept Cones, arXiv:2502.17420) find *multiple* mechanistically-independent refusal directions / multi-dimensional cones; orthogonality ≠ independence under intervention. SOM-Directions (arXiv:2511.08379) likewise extract multiple directions that ablate better than one. Interpretation: diff-in-means gives *a* highly effective direction, not necessarily *the unique* one.
- Behaviour studied (refusal) is a sharp binary; our "clean design" target is graded and multi-component, so a single direction is a hypothesis to test, not assume.

## Relevance to Project 19
This is the exact recipe skeleton for Stage 2. Our contrast is **skill-present vs length-matched-neutral** (ADR-003) instead of harmful-vs-harmless, but the machinery is identical: diff-in-means over post-prompt positions, layer/position sweep with validation selection, activation addition to *induce* clean design with no prompt, and **directional ablation as the second causal arm** — projecting the design direction out *while the skill is present* to test whether the skill stops working (our "directional-ablation flip test" in D5). The weight-orthogonalization trick lets us run the flip test cheaply.

## Borrow
- Diff-in-means over last post-instruction tokens; sweep all (layer, position); **select on a held-out validation objective**, don't hand-pick.
- Two-sided causal test: addition (does the direction *cause* the behaviour with no prompt?) **and** ablation (is it *necessary* — does removing it kill the behaviour even when the skill is present?).
- Coherence gate on standard benchmarks (for us: does steering wreck HTML validity / general code ability?).
- Unit-normalise the direction; parameterise strength by $\alpha$.

## Avoid
- Don't over-claim a *unique* "design direction"; run the multi-direction robustness check (per Concept Cones) and report honestly if design is a cone, not a line.
- Don't select the direction on the test prompts (leakage); freeze selection on the dev split per our preregistration.
- Refusal is one-token-early; long code generations may carry the signal at different positions — validate position choice empirically (see D3).
