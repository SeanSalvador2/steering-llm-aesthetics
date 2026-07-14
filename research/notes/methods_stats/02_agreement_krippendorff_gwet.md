# C2 — Chance-Corrected Agreement: Krippendorff's α, Gwet's AC1, and the kappa paradox

**Citations.**
- Hayes & Krippendorff 2007, *Answering the Call for a Standard Reliability Measure for Coding Data*, Communication Methods and Measures 1(1):77–89, doi:10.1080/19312450709336664.
- Gwet 2008, *Computing Inter-Rater Reliability and Its Variance in the Presence of High Agreement*, Br. J. Math. Stat. Psychol. 61(1):29–48, doi:10.1348/000711006X126600.

**TL;DR.** Raw % agreement overstates reliability; chance-corrected coefficients fix that but each has failure modes. **Krippendorff's α** is the flexible standard (any # raters, missing data, any measurement level, bootstrap CIs) but **suffers the "kappa paradox"** — it collapses toward 0 under skewed marginals even when raters nearly always agree. **Gwet's AC1** is robust to that paradox. Report **both** with bootstrap CIs; set defensible thresholds. Directly implements ADR-005's reliability gate.

## The coefficients

**General form.** $\text{coeff} = \dfrac{p_o - p_e}{1 - p_e}$ — observed agreement minus chance agreement, normalized. They differ in how $p_e$ (chance agreement) is estimated.

**Krippendorff's α.**
$$\alpha = 1 - \frac{D_o}{D_e},$$
$D_o$ = observed disagreement, $D_e$ = expected disagreement from the **overall marginal distribution** of categories; uses a distance metric matched to data level (nominal/ordinal/interval) so it handles our ordinal/binary preference labels; handles **any number of raters and missing data**; **CIs via bootstrap**. **Failure mode (kappa paradox):** when one category dominates (e.g. "A preferred" in 90% of pairs), $D_e$ is large, so even 95%+ observed agreement can give a low/near-0 α — misleadingly pessimistic under range restriction.

**Gwet's AC1.**
$$\text{AC1} = \frac{p_o - p_{e}^{\gamma}}{1 - p_{e}^{\gamma}}, \quad p_e^{\gamma} = \frac{1}{q-1}\sum_k \pi_k(1-\pi_k),$$
a chance estimator (for $q$ categories, marginal $\pi_k$) that **does not blow up under skew**, so AC1 stays stable when agreement is genuinely high but marginals are unbalanced. AC2 extends to ordinal/weighted. **This is the antidote to the paradox** and the recommended companion when our preference labels are skewed (e.g. the skill usually wins).

## The paradox, concretely
Two raters agree on 99.8% of cases but κ/α ≈ 0 because almost all cases fall in one category. Pro-κ view: "no agreement on the rare class → unreliable." Anti-κ view: "they agree on nearly everything → reliable." For our design: **the skill cell likely wins most pairs**, creating skewed marginals — so α alone could falsely fail the reliability gate. Reporting **AC1 alongside α** prevents wrongly discarding a real, reliable signal.

## Thresholds (defensible)
- Krippendorff's own convention: **α ≥ 0.80** good, **α ≥ 0.667** the lowest acceptable for tentative conclusions (ADR-005's provisional 0.67 gate).
- For AC1, use Landis–Koch-style bands as a guide (0.61–0.80 substantial, >0.80 almost perfect), acknowledging they're heuristic.
- **Policy:** pass the reliability gate if **α ≥ 0.667 OR (AC1 ≥ 0.80 with α depressed by demonstrable marginal skew)**; always report both + bootstrap 95% CIs; pre-register the rule.

## Relevance to Project 19
Implements the reliability gate for the VLM-judge-vs-human-subset agreement and for human–human agreement. Because our pairwise preferences will be **skewed** (skill usually preferred), we must use **AC1** to avoid the kappa paradox falsely nulling a real effect, while keeping **α** for comparability with the literature. Bootstrap CIs feed the power/decision rules.

## Borrow
- Compute **both α (ordinal) and Gwet AC1**, with **bootstrap 95% CIs**; pre-register the pass rule; use ordinal distance for graded preferences.
- Report marginal distributions so paradox conditions are visible.

## Avoid
- Reporting **only** Krippendorff α on skewed preference data (paradox → false fail).
- Raw % agreement as the gate (no chance correction).
- Applying nominal α to ordinal preferences (use ordinal weighting).
