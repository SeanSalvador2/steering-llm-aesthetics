# B4 — Analysing the Generalisation and Reliability of Steering Vectors (Tan et al. 2024)

**Citation.** Tan, Chanin, Lynch, Kanoulas, Paige, Garriga-Alonso, Kirk. *Analysing the Generalisation and Reliability of Steering Vectors.* NeurIPS 2024. arXiv:2407.12404.

**TL;DR.** A rigorous audit of CAA-style steering vectors showing they are **unreliable in-distribution** (per-input steerability varies wildly; some concepts have ~50% *anti-steerable* examples where steering flips the wrong way) and sometimes **brittle out-of-distribution** (fail under reasonable prompt changes). This paper defines the metrics and cautionary framing for our Stage-2 failure-surface analysis and directly informs how we must report steering effects (distributions, not means).

## Method, in depth

**Setup.** Extract CAA diff-in-means vectors on Anthropic Model-Written-Evals behaviours; measure not just mean effect but the **per-example distribution** of steering effect.

**Per-sample steerability.** For each input, define steerability as the (signed) change in target-behaviour logit/probability per unit steering coefficient — effectively the slope of behaviour vs coefficient. Aggregate the distribution across inputs.

**Key diagnostics.**
- **Steerability variance:** the per-input slope varies enormously within a dataset; the mean hides a heavy-tailed distribution.
- **Anti-steerable fraction:** for several concepts, a large fraction of inputs (up to ~50%) move *opposite* to the intended direction — steering makes them worse.
- **Spurious cues:** in-distribution steerability can be driven by spurious features correlated with the concept in the extraction set, not the concept itself; discriminability along the diff-in-means line correlates with steerability (a usable pre-screen).
- **OOD:** vectors often generalise across paraphrase, but for some concepts break under modest prompt reformulation.

## Key results & numbers
- High within-dataset variance in per-sample steerability across concepts.
- Up to ~50% anti-steerable inputs for some concepts — a mean effect near zero can hide huge, canceling per-item effects.
- Correlation between separation (discriminability) on the diff-in-means axis and downstream steerability — a cheap reliability predictor.

## Limitations / critiques
- Studies A/B behavioural concepts, not long-form generation quality; our effect sizes/variances may differ but the *phenomenon* (heterogeneous steerability) is the warning.
- Focuses on CAA; other extraction methods may be more/less reliable (later work e.g. bi-directional preference optimization tries to reduce this).

## Relevance to Project 19
This paper is why the brief demands an **honest failure surface** and why our oracle reports **null unless an effect moves a signal**. Concretely, for our design steering we must: (1) report the *distribution* of per-prompt quality deltas, not just the mean; (2) quantify the **anti-steerable fraction** (prompts where steering *lowers* objective/preference quality); (3) pre-screen the extracted direction by its class separation/discriminability before spending judge budget; (4) test OOD by holding out unseen task *types* (D11) — exactly the brittleness axis Tan flags.

## Borrow
- Per-example steerability distribution + anti-steerable fraction as first-class reported metrics (not just cell means).
- Use diff-in-means class-separation (e.g. AUC of the projection separating skill vs neutral) as a cheap predictor of whether steering will work, before running the judge.
- Explicit in-distribution vs OOD (unseen task type) split for the generalisation claim.

## Avoid
- Reporting only mean steering effect — it can be ~0 while half the prompts move each way.
- Assuming a vector that works on landing pages transfers to dashboards/forms without an OOD test.
- Treating a strong average as "the mechanism found" — pair with the necessity (ablation) test from B1.
