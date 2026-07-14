# B8 — Representation Engineering: A Top-Down Approach to AI Transparency (Zou et al. 2023)

**Citation.** Zou, Phan, Chen, Campbell, Guo, Ren, Pan, Yin, et al. *Representation Engineering: A Top-Down Approach to AI Transparency (RepE).* arXiv:2310.01405.

**TL;DR.** Frames a whole research program around reading and controlling **population-level representations** (directions) rather than neurons/circuits. Introduces **Linear Artificial Tomography (LAT)** for *reading* a concept direction from contrastive stimuli, and representation *control* (adding/projecting the direction) for steering — applied to honesty, harmlessness, power-seeking, emotion, fairness. RepE is the conceptual umbrella under which our diff-in-means design-direction sits, and LAT is an alternative reading method to compare against.

## Method, in depth

**LAT (reading).** (1) Design a stimulus set that elicits a concept along a contrast (e.g. honest vs dishonest framings of the same statement). (2) Collect residual-stream activations at a chosen token position (often the last token of the stimulus) across the set. (3) Take **differences of paired stimuli**, then run **PCA** on those difference vectors; the top principal component is the concept **reading vector** for that layer. (This differs from plain diff-in-means: PCA-on-differences vs mean-of-differences — related but LAT can capture a dominant axis when pairs are noisy.)

**Reading (monitoring).** Project activations onto the reading vector to *monitor* the concept during generation (e.g. a "lie detector" for honesty). Correlates with behaviour and can predict it before output — the same projection-monitoring idea persona vectors later operationalize.

**Control (steering).** Add the reading vector to activations (like ActAdd/CAA) or use "contrast vector" / low-rank representation control to push the concept up or down at inference. Demonstrated to increase honesty, reduce harmfulness, control emotion, etc., across layers (typically a band of middle layers).

## Key results & numbers
- LAT reading vectors detect and steer high-level concepts across many behaviours on 7B–13B chat models.
- Reading-vector projection is a usable *monitor* (predictive of downstream behaviour) — precursor to persona-vector monitoring.
- Control via representations competitive with prompting/finetuning for the studied concepts.

## Limitations / critiques
- LAT's PCA-on-differences vs simple diff-in-means: AxBench (B5) found plain **DiffMean** best among representation methods, and Tan (B4) audits reliability — so RepE's reading vectors inherit the same per-example variance concerns.
- Stimulus design is bespoke and can inject spurious structure; requires the same control-task discipline as probing.

## Relevance to Project 19
RepE provides (a) the vocabulary ("reading vector," "representation control," monitoring-by-projection) our paper will use, and (b) **LAT as a second extraction method** to sanity-check diff-in-means: extract the design direction both ways and confirm they agree (high cosine similarity). RepE's monitoring idea supports a nice auxiliary result — *project generations onto the design direction to predict, before rendering, whether an output will score well* (cheap pre-screen echoing Tan's discriminability finding).

## Borrow
- LAT (PCA-on-paired-differences) as a robustness cross-check for the diff-in-means design vector.
- Projection-based monitoring: use the design direction as a pre-render quality predictor.
- Contrastive-stimulus discipline (matched pairs differing only in the concept) — our skill vs length-matched-neutral pairs already satisfy this.

## Avoid
- Treating LAT's top-PC as automatically "the concept" — validate causally (steer/ablate) and against DiffMean; don't assume PCA axis = design axis.
- Bespoke stimulus sets that leak prompt identity; keep the only difference = presence of design guidance.
