# B7 — Linear Probing: Alain & Bengio 2016; Hewitt & Liang 2019 (control tasks / selectivity)

**Citations.**
- Alain, Bengio. *Understanding Intermediate Layers Using Linear Classifier Probes.* ICLR Workshop 2017. arXiv:1610.01644.
- Hewitt, Liang. *Designing and Interpreting Probes with Control Tasks.* EMNLP-IJCNLP 2019, pp. 2733–2743. doi:10.18653/v1/D19-1275.

**TL;DR.** Probing = train a simple (linear) classifier on frozen activations to test whether a property is *linearly decodable* at a layer. Alain & Bengio establish the method and layer-wise reading. Hewitt & Liang show probes can *memorize*, so decodability alone is weak evidence; they introduce **control tasks** and **selectivity** to separate "the representation encodes it" from "the probe learned it." This gives Stage-2 localization its rigor and its honesty guardrail.

## Method, in depth

**Linear probe (Alain & Bengio).** For each layer $l$, fit a linear classifier $g(x_l)=\text{softmax}(Wx_l+b)$ to predict a property; the probe *accuracy per layer* traces where/when the property becomes linearly available. Probes are trained with the base model frozen (no gradient into the model). Finding: linear separability of useful features increases with depth; probes are a cheap diagnostic, not a modification.

**Control tasks & selectivity (Hewitt & Liang).** A **control task** maps each input to a *random* output (fixed per word-type) with the same structure as the real task. A trustworthy probe should get **high real-task accuracy but low control-task accuracy**. Define
$$\text{Selectivity} = \text{Acc}_{\text{real}} - \text{Acc}_{\text{control}}.$$
High accuracy with high control accuracy ⇒ the probe is just memorizing, not reading structure. Result: **linear and bilinear probes are far more selective than MLP probes** — so for interpretability claims, prefer the simplest probe with acceptable accuracy, and always report selectivity.

## Key results & numbers
- Linear/bilinear probes >> MLP probes in selectivity; MLP probes can memorize random control labels.
- Probe accuracy is layer-dependent; the layer of peak decodability is informative but must be paired with selectivity.

## Limitations / critiques
- Decodability ≠ use: a property can be linearly present but not causally used by the model. Probing must be paired with a **causal** test (patching/steering) — probing localizes *candidate* layers; steering/ablation proves the model *uses* the direction. (This is exactly the brief's "correlate vs cause" bar.)
- Probe can pick up spurious correlates (cf. Tan B4); control-task selectivity is the mitigation.

## Relevance to Project 19
Stage-2 localization: train **linear probes to detect "skill-present vs length-matched-neutral"** from residual activations at each layer/position, giving a per-layer decodability curve — the cheap first pass that tells us *where* the design signal is linearly available, before spending on patching/steering. **Selectivity via a control task is mandatory** for our honesty bar: build a control task (random skill/neutral labels per prompt) so a high-accuracy probe can't just be memorizing prompt identity. The probe direction (its weight vector, or the class-mean difference) is also a candidate steering vector to compare against diff-in-means.

## Borrow
- Per-layer linear-probe accuracy curve for skill-present vs neutral → pick candidate layers.
- Report **selectivity** against a random-label control task; use linear (not MLP) probes for interpretability claims.
- Compare probe-derived direction vs diff-in-means direction (should be similar if the signal is linear).

## Avoid
- Claiming "the model represents design here" from probe accuracy alone — always follow with a causal steer/ablate at that layer.
- MLP probes for the interpretability claim (low selectivity, memorization risk).
- Probing on the same prompts used to extract the steering vector (leakage) — hold out.
