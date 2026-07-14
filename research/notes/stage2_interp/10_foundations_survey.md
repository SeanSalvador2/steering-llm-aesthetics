# Stage-2 Foundations (survey cluster)

Why linear directions / diff-in-means are a principled choice, and the caveats.

## Linear Representation Hypothesis — Park, Choe, Veitch 2023 (arXiv:2311.03658) + Park et al. 2024 geometry (arXiv:2406.01506)
- **Claim.** High-level concepts are encoded (approximately) as linear **directions** in representation space; "linear representation" is formalized via counterfactual pairs, and connects to **linear probing** (output space) and **model steering** (input space). A *causal inner product* unifies cosine/projection notions so probes and steering vectors can be built from counterfactual pairs.
- **Geometry paper.** Categorical concepts are represented as **simplices**; hierarchically related concepts are **orthogonal**; complex concepts are polytopes (direct sums of simplices). Validated on Gemma over 957 WordNet concepts.
- **Implication for us.** Justifies diff-in-means (a counterfactual-pair difference) as a legitimate estimator of a concept direction, and predicts that *distinct design sub-concepts* (color vs layout vs type) could be roughly orthogonal directions — testable against our Stage-1 components (the paper's "creative latitude" multi-direction hypothesis).

## Not All Features Are Linear — Engels et al. 2024 (arXiv:2405.14860)
- Some features are irreducibly **multi-dimensional** (e.g. circular day-of-week/month features). Linear steering can miss these.
- **Implication.** Our "clean design" may be a low-dim manifold, not a single line — if single-direction steering underperforms, test a 2–4D subspace (PCA of per-component diff-in-means), and report honestly if design is non-linear/distributed (a legitimate null per the brief).

## Superposition — Elhage et al. 2022, Toy Models of Superposition (arXiv:2209.10652)
- Networks pack more features than neurons via **superposition**, causing polysemantic neurons; motivates dictionary learning / SAEs and explains why *directions*, not neurons, are the right unit of analysis.
- **Implication.** Reinforces population-level (direction) analysis over neuron-level; also warns that a single design direction may interfere with other features (the coherence trade-off we must measure).

## Function Vectors — Todd et al. 2023 (arXiv:2310.15213) & Task Vectors — Hendel et al. 2023 (arXiv:2310.15916)
- **Function vectors:** a small set of attention heads transport a compact vector encoding an ICL task; adding it triggers the task **zero-shot** in unrelated contexts; strong causal effects at **middle layers**. Extracted via causal mediation.
- **Task vectors:** ICL compresses a demonstration set into a single vector $\theta(S)$ that modulates the transformer to perform the task — a prompt's *effect* is summarizable as one added vector.
- **Implication.** Direct precedent that "the effect of an instruction/prompt = a single addable vector at a mid layer." Our claim "the design skill's effect ≈ one steering vector" is the same shape of result, one abstraction level up (a style/quality skill rather than an ICL task). Middle-layer causal locus matches CAA/persona findings.

## One-line lenses
- **Logit lens / tuned lens:** project intermediate residuals through the unembedding to read the model's "current guess" per layer; tuned lens learns an affine correction. Useful to visualize *when* design-relevant tokens (font-family, color hex) become probable across depth. (Referenced as standard tooling; see Zhang & Nanda B6 ecosystem.)

**Net:** the linear-direction program is well-founded and the middle-layer, diff-in-means, add-a-vector recipe is repeatedly the effective one — but linearity is an approximation; keep the multi-dimensional/distributed null on the table.
