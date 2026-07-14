# B6 — Activation Patching Best Practices (Zhang & Nanda 2024; Heimersheim & Nanda 2024)

**Citations.**
- Zhang, Nanda. *Towards Best Practices of Activation Patching in Language Models: Metrics and Methods.* ICLR 2024. arXiv:2309.16042.
- Heimersheim, Nanda. *How to Use and Interpret Activation Patching.* arXiv:2404.15255.

**TL;DR.** Activation patching (a.k.a. causal tracing / interchange intervention) localizes which components/positions carry a behaviour by swapping activations between a "clean" and "corrupted" run and measuring the effect. These two papers give the methodological rules: **denoising vs noising**, **which metric** (logit difference, not probability/accuracy), and the pitfalls (backup/self-repair, corruption choice). This is our Stage-2 *localization* tool, complementing diff-in-means/probing.

## Method, in depth

**Two directions of patching.**
- **Denoising (noising→clean patch):** run on a corrupted/neutral prompt, patch in a *clean* (skill-present) activation at one site, see if the target behaviour is *restored*. Answers "is this site **sufficient**?"
- **Noising (clean→corrupted patch):** run clean, patch in a corrupted activation, see if behaviour *breaks*. Answers "is this site **necessary**?"
The two can disagree; report which you ran and interpret accordingly.

**Metric choice.** Prefer **logit difference** between the correct/target and a contrast completion, $\Delta = \text{logit}(t^{+}) - \text{logit}(t^{-})$, over probability or accuracy: logit-diff is smoother, more linear, and less prone to saturation/threshold artifacts. Report the patched metric as a fraction of the clean–corrupted gap (a normalized "% recovered").

**Corruption design.** The corrupted run must differ from clean *only* in the concept of interest (analogous to our length-matched neutral control). Gaussian-noising embeddings is discouraged (off-distribution, unstable); prefer a *symmetric counterfactual* prompt.

**Pitfalls (Heimersheim & Nanda).**
- **Backup / self-repair (the hydra effect):** ablating one component causes others to compensate, so a *necessary* component can look unnecessary under noising. Denoising is less affected.
- Patching shows *where information is used for this metric*, not a full circuit; a site mattering under one metric may not under another.
- Subspace patching can be **illusory** (Makelov, Lange, Nanda 2023): a subspace intervention can change behaviour via a dormant parallel pathway, not the studied feature — demand extra faithfulness evidence.
- Granularity matters: residual stream vs attention-out vs MLP-out give different pictures; sweep positions and layers.

## Key results & numbers
- Logit-diff recommended over prob/accuracy across localization and circuit-discovery settings; hyperparameter choices materially change conclusions.
- Denoising generally more robust than noising for locating sufficient components (given self-repair).

## Limitations / critiques
- Patching is designed for *token-level*, metric-specific tasks (IOI, factual recall). Our target is a *diffuse quality* over a long generation with no single "answer token" — patching is best used here to localize *where the skill first changes the trajectory* (e.g., patch the skill-present residual at layer $l$, position $i$, into the neutral run and see if early design tokens change), not to recover a crisp circuit.
- Attribution patching (gradient approximation) scales better but has false negatives (Kramár et al. AtP*); use for triage, verify with real patching.

## Relevance to Project 19
Localization arm of Stage 2 (brief: "which layers/positions carry the signal — activation diffing, probing, patching"). Use **denoising**: patch skill-present activations into the length-matched-neutral run, site by site, to find the earliest/most-sufficient (layer, position) where design behaviour is recoverable — this both localizes and cross-validates the layer chosen for diff-in-means steering. Use **logit-diff-style** contrast on a design-discriminating token proxy (e.g., probability the model opens a non-default palette / non-Inter font-family token) rather than a fuzzy quality score.

## Borrow
- Denoising patch (neutral→skill) for sufficiency; noising (skill→neutral) for necessity; report both.
- Logit-difference metric on a concrete design-token contrast; report % of clean–corrupted gap recovered.
- Counterfactual corruption = our length-matched neutral prompt (already the design's confound control).
- Cross-check the diff-in-means steering layer against the patching-localized layer.

## Avoid
- Gaussian noising of embeddings; use symmetric counterfactual prompts.
- Trusting a single subspace-patch result (interpretability-illusion risk) — corroborate with steering + probing.
- Over-reading necessity under noising given self-repair; prefer denoising for "where does the skill act."
