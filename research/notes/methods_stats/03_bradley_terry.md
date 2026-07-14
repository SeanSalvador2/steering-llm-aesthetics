# C3 — Bradley-Terry Models & Chatbot Arena Style Control

**Citations.**
- Bradley & Terry 1952, *Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons*, Biometrika 39(3/4):324–345, doi:10.2307/2334029.
- Chiang, Li, Angelopoulos et al. 2024, *Does Style Matter? Disentangling Style and Substance in Chatbot Arena* (LMSYS blog, 2024-08-28).

**TL;DR.** Bradley-Terry (BT) turns pairwise win/loss data into per-item **latent strength** scores with CIs — exactly how we convert judge pairwise verdicts into **cell-level design-quality utilities**. Chatbot Arena's **style-control regression** (adding length/markdown covariates to the BT model to remove style confounds) is the direct analogue of our length-matched control done at the *analysis* level.

## BT model, in depth
Each item $i$ (here: an ablation/steering *cell*) has strength $\beta_i$. Probability $i$ beats $j$:
$$P(i \succ j) = \frac{e^{\beta_i}}{e^{\beta_i}+e^{\beta_j}} = \sigma(\beta_i - \beta_j).$$
**Estimation:** MLE by maximizing the log-likelihood over observed pairwise outcomes (logistic regression with one indicator per item; identifiability by fixing a reference $\beta_0=0$). This is the ML foundation under Arena's "Elo" (Elo is an online approximation; BT is the batched MLE).

**Ties.** Basic BT has no tie term; handle via (a) **Rao–Kupper** or **Davidson** tie extensions (add a tie parameter), or (b) split a tie as half-win/half-loss. With order-swap "tie if inconsistent," ties are informative — prefer a Davidson/Rao–Kupper term.

**Uncertainty.** CIs from the logistic Hessian (Fisher information) or, more robustly for clustered data, **cluster bootstrap** over prompts (resample prompts, refit BT) — respects that many comparisons share a prompt.

## Style control (Arena) — the key analogy
Arena augments BT with **confound covariates** so strength isn't inflated by style. They add features: **normalized response-length difference, #markdown headers, #lists**. Model:
$$P(i \succ j) = \sigma\big((\beta_i - \beta_j) + \gamma^{\top}(s_i - s_j)\big),$$
where $s$ are style features and $\gamma$ their learned coefficients. Attributing the style difference to $\gamma$ makes $\beta$ reflect **substance**, not verbosity/formatting.
**Our analogue:** include page-level style covariates — **DOM size / token length, element count, text density, colorfulness** — in the BT regression so the estimated design-quality difference between skill and neutral cells is **not** just "the skill produced a bigger/denser/more-colorful page." This complements the *design-level* length-matched neutral control (ADR-003) with an *analysis-level* adjustment (defense in depth).

## Relevance to Project 19
BT is the aggregation layer of the preference oracle: pairwise judge verdicts (both orders) → BT strengths per cell → **effect = strength difference with CI**. Style-controlled BT is how we make the ablation/steering effect robust to the exact confound (length/verbosity/colorfulness) the judge is known to be biased by (C1). It also yields a clean, publishable "design-quality utility per cell" with uncertainty, feeding the power analysis.

## Borrow
- Fit BT (Davidson tie term) on both-order pairwise verdicts; reference cell = full-skill or neutral; report strength differences + **cluster-bootstrap CIs over prompts**.
- **Style-controlled BT**: covariates = length/DOM-size, element count, colorfulness, text density — so the design effect is substance, not style.
- Use BT strengths (not raw win-rates) as the response for mixed-effects / power analysis.

## Avoid
- Plain win-rate comparisons (ignore opponent strength & pairing structure).
- BT without tie handling when we deliberately produce ties (order-inconsistent = tie).
- Naive (non-clustered) CIs — comparisons share prompts; use cluster bootstrap over prompts.
- Relying on style-controlled BT *instead of* the length-matched design control — do both (design-level + analysis-level).
