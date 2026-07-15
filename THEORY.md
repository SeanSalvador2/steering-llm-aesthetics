# THEORY.md — Mathematical backbone (Project 19: Anatomy of a Design Skill)

This is the derivations appendix for the whole project. It has two duties. **(a) Rigor:** every
statistical and interpretability claim the paper makes points to a derivation here — assumptions
stated, algebra shown, no "it can be shown." **(b) Pedagogy:** a strong statistics MS student can
follow every step. Notation is shared **symbol-for-symbol** with `PLAN.md` Part VII; `PREREGISTRATION.md`
freezes the decision rules these derivations justify; governance is `CLAUDE.md`; ADRs are
`docs/DECISIONS.md`. Citations are BibTeX keys in `research/refs.bib`.

Sections **T1–T9** map to the Part-VII hooks (§T1 DOE, §T2 aliasing, §T3 MixedLM, §T4 agreement,
§T5 BT, §T6 power, §T7 metrics, §T8 diff-in-means/`do`-calculus, §T9 SAE). Each section closes with a
**Used in:** line naming the exact PLAN sections / RQs / notebook stages that consume it. The most
load-bearing equations are flagged inline (some flags bundle a two-display pair) and consolidated to
**14 headline entries** in the PAPER-EQ index at the end:

> PAPER-EQ (candidate): `<one-line reason>`

---

## T0 — Shared notation (and the three overloaded symbols)

Three letters are overloaded in the literature this project draws on; PLAN inherits the overloads.
We **scope them by section** and state the scope wherever ambiguity is possible.

| symbol | meaning | scope |
|---|---|---|
| $A,B,C,D,E$ | the five design factors $=C_1,\dots,C_5$ (color, layout, typography, patterns, negatives) | T1–T2 |
| $x=(x_A,\dots,x_E)\in\{\pm1\}^5$ | a cell's sign vector; $+1$ = real component, $-1$ = matched filler | T1–T2 |
| $\tau_c$ | fixed effect of cell $c$ (cell-level mean shift) | T2, T6 |
| $u_p,\;v_{cp},\;\epsilon_{cps}$ | random prompt intercept; random cell$\times$prompt slope; residual | T2 |
| $y_{cps}$ | a continuous endpoint (POC or a family metric) for (cell $c$, prompt $p$, seed $s$) | T2, T6, T7 |
| $\rho_{\mathrm{ICC}}$ | intraclass correlation (seed-within-prompt) | T2 |
| $\alpha$ **(stats)** | test significance level (FWER target $0.05$) | T2, T5, T6 |
| $\alpha_K$ | **Krippendorff's** $\alpha$ (agreement) — always written $\alpha_K$ | T3 |
| $D_o,D_e$ | observed / expected disagreement (Krippendorff) | T3 |
| $\pi_k$ | pooled marginal probability of category $k$; $q$ categories | T3 |
| $\beta_i$ | Bradley–Terry latent strength of cell $i$; reference $\beta_{\text{NEUTRAL}}=0$ | T4 |
| $s_i,\;\gamma$ | per-page style covariate vector; its BT coefficient vector | T4 |
| $p_d,\;\delta$ | P(discordant/decisive pair); signed preference gap | T5 |
| $h_\ell(t)$ | residual-stream state at layer $\ell$, token $t$; model width $d=3584$, $L=28$ | T8–T10 |
| $\bar h_\ell^{(\text{FULL})},\bar h_\ell^{(\text{NEUTRAL})}$ | mean-over-response-token residual, skill / neutral side | T8 |
| $v_\ell=\bar h_\ell^{(\text{FULL})}-\bar h_\ell^{(\text{NEUTRAL})}$ | per-layer **diff-in-means**; $\hat v_\ell=v_\ell/\lVert v_\ell\rVert$ | T8–T10 |
| $\ell^\*,\rho^\*,\text{variant}^\*$ | frozen steering operating point (dev-selected, then git-tagged) | T9–T10 |
| $\alpha$ **(interp)** $=\rho\cdot\overline{\lVert h_\ell\rVert}$ | steering addition coefficient; $\rho$ = norm-relative fraction (primary axis) | T9 |
| $P=I-\hat v\hat v^\top$ | orthogonal projector for directional ablation | T9 |
| $Q$ | scalar UI-quality outcome (POC or a preference utility) | T10 |
| $\mathrm{do}(\cdot)$ | Pearl intervention operator on an activation node | T10 |

**Rule for the two $\alpha$'s.** In T2/T5/T6 (frequentist inference) $\alpha$ is the significance
level. In T8–T10 (steering) $\alpha$ is the addition coefficient, and its *primary* parameterization
is the norm-relative $\rho$ (so we mostly write $\rho,\rho^\*$). Krippendorff's is always $\alpha_K$.

---

## T1 — Experimental design: the $2^5$ factorial, the resolution-V fraction, and the LOO/AOI corners

### T1.1 The effects model and the $\pm1$ parameterization

Five two-level factors $A,\dots,E=C_1,\dots,C_5$. A cell is a corner of the hypercube, coded
$x\in\{\pm1\}^5$ ($+1$ real component, $-1$ token-matched filler; PLAN §II.1.3). The **effects
(orthogonal, $\pm1$) parameterization** of the full $2^5$ writes the expected response at corner $x$
as a multilinear polynomial:

$$
\mathbb{E}[y(x)] \;=\; \beta_0 \;+\; \sum_{i} \beta_i\,x_i \;+\; \sum_{i<j}\beta_{ij}\,x_i x_j
\;+\; \sum_{i<j<k}\beta_{ijk}\,x_i x_j x_k \;+\;\cdots\;+\;\beta_{ABCDE}\,x_A x_B x_C x_D x_E .
\tag{T1.1}
$$

There are $2^5=32$ coefficients for $32$ corners — saturated. Each $\beta$ is (half) the corresponding
**factorial effect**: because every column $x_S=\prod_{i\in S}x_i$ takes values $\pm1$ and the columns
are mutually orthogonal over the full design ($\sum_{x}x_S x_{S'} = 32\,\mathbb{1}[S=S']$), the
least-squares estimate is the simple contrast

$$
\hat\beta_S \;=\; \frac{1}{32}\sum_{x\in\{\pm1\}^5} x_S\, \bar y(x),
\tag{T1.2}
$$

i.e. the mean response at corners where $x_S=+1$ minus the mean where $x_S=-1$, halved. The
*factorial main effect* of $C_i$ is $2\beta_i$; the two-factor interaction (2FI) of $(C_i,C_j)$ is
$2\beta_{ij}$. We adopt the coefficient $\beta$'s as the parameters and translate to "effects" ($2\beta$)
where the paper reports them.

> **Assumptions box (T1.1).** (i) Additivity of the multilinear form on the latent scale of $y$
> (POC is built to be roughly interval-scaled, T7). (ii) Homoscedastic, independent errors *conditional
> on* the random-effect structure of T2 (the DOE algebra here is the fixed-effects skeleton; T2 supplies
> the correct SEs). (iii) Two levels per factor suffice because each component is either its real text
> or its render-inert filler — there is no dose within a component.

### T1.2 The $2^{5-1}$ resolution-V fraction: construction and the 24-cell dedup

Running all 32 corners $\times$ 40 prompts $\times$ seeds is wasteful (ADR-004). We take the **principal
half-fraction** with **generator $E=ABCD$**, i.e. we keep exactly the corners satisfying

$$
x_A x_B x_C x_D x_E \;=\; +1 \quad\Longleftrightarrow\quad \text{defining relation } I=ABCDE .
\tag{T1.3}
$$

The kept set has $16$ runs. **Which 16?** A corner satisfies $\prod_i x_i=+1$ iff it has an **even
number of $-1$'s**. Counting by number of minus signs:

$$
\underbrace{\binom{5}{0}}_{1}+\underbrace{\binom{5}{2}}_{10}+\underbrace{\binom{5}{4}}_{5}=16 .
$$

Enumerating (verified in `scratchpad`; reproduced below):

- **0 minus (all $+$): 1 run** $=(+,+,+,+,+)$. This *is* **FULL**.
- **4 minus (single $+$): 5 runs**, e.g. $(+,-,-,-,-)$. These are exactly the five **AOI-$C_i$** cells
  (only component $i$ present).
- **2 minus (three $+$): 10 runs**, e.g. $(+,+,+,-,-)$. These are the ten **F-cells** (three components
  present) — the interaction block.

So the fraction is $\{$FULL, AOI-$C_1$…AOI-$C_5$, F-123…F-345$\}$. Six of its sixteen runs coincide with
already-named control/AOI cells; it therefore contributes **10 new** three-component cells. With the
four controls (FULL, NEUTRAL, BEAUTY1, NOSYS) and the five LOO cells, the deduplicated design has

$$
\underbrace{4}_{\text{controls}}+\underbrace{5}_{\text{LOO}}+\underbrace{5}_{\text{AOI}}+\underbrace{10}_{\text{F}}=\mathbf{24}\ \text{distinct cells},
$$

matching PREREG §3 exactly (FULL is counted once, in "controls"; AOI/F come from the fraction).

**Why LOO and NEUTRAL are *not* in the fraction (parity proof).** A cell lies in the principal
fraction iff $\prod_i x_i=+1$ (even \#minus). The LOO-$C_i$ cells have exactly **one** $-1$ (odd) →
$\prod_i x_i=-1$; NEUTRAL $=(-,-,-,-,-)$ has **five** $-1$'s (odd) → $\prod=-1$. Both satisfy
$I=-ABCDE$, i.e. they live in the **complementary (alternate) fraction**. They are genuine
**off-fraction corners**. (BEAUTY1 and NOSYS are not factorial cells at all — they carry no component
slots.) This is the precise version of PLAN §III.1's parity remark; note that the AOI cells, by
contrast, are *in*-fraction, so "LOO/AOI corners" collapses to "the LOO cells plus NEUTRAL are the
off-fraction additions."

**The frozen 16-run sign table (verify $\prod_i x_i=+1$ each row):**

| run | $x_A$ | $x_B$ | $x_C$ | $x_D$ | $x_E$ | \#minus | $\prod x_i$ | name |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| 1 | $+$ | $+$ | $+$ | $+$ | $+$ | 0 | $+$ | FULL |
| 2 | $+$ | $-$ | $-$ | $-$ | $-$ | 4 | $+$ | AOI-C1 |
| 3 | $-$ | $+$ | $-$ | $-$ | $-$ | 4 | $+$ | AOI-C2 |
| 4 | $-$ | $-$ | $+$ | $-$ | $-$ | 4 | $+$ | AOI-C3 |
| 5 | $-$ | $-$ | $-$ | $+$ | $-$ | 4 | $+$ | AOI-C4 |
| 6 | $-$ | $-$ | $-$ | $-$ | $+$ | 4 | $+$ | AOI-C5 |
| 7 | $+$ | $+$ | $+$ | $-$ | $-$ | 2 | $+$ | F-123 |
| 8 | $+$ | $+$ | $-$ | $+$ | $-$ | 2 | $+$ | F-124 |
| 9 | $+$ | $+$ | $-$ | $-$ | $+$ | 2 | $+$ | F-125 |
| 10 | $+$ | $-$ | $+$ | $+$ | $-$ | 2 | $+$ | F-134 |
| 11 | $+$ | $-$ | $+$ | $-$ | $+$ | 2 | $+$ | F-135 |
| 12 | $+$ | $-$ | $-$ | $+$ | $+$ | 2 | $+$ | F-145 |
| 13 | $-$ | $+$ | $+$ | $+$ | $-$ | 2 | $+$ | F-234 |
| 14 | $-$ | $+$ | $+$ | $-$ | $+$ | 2 | $+$ | F-235 |
| 15 | $-$ | $+$ | $-$ | $+$ | $+$ | 2 | $+$ | F-245 |
| 16 | $-$ | $-$ | $+$ | $+$ | $+$ | 2 | $+$ | F-345 |

Every row multiplies to $+1$; the design is the principal fraction. `src/skill_assembly` holds this
table frozen and `src/mixedlm` rebuilds it from the generator.

### T1.3 The model matrix and its rank

On the 16 fraction runs we fit intercept + 5 mains + 10 2FIs (the resolution-V estimable set, T2):

$$
X = \big[\,\mathbf 1 \ \big|\ x_A,\dots,x_E \ \big|\ x_Ax_B,\dots,x_Dx_E\,\big] \in \{\pm1\}^{16\times16}.
\tag{T1.4}
$$

Because the design is a saturated orthogonal fraction, the columns are mutually orthogonal
($X^\top X = 16\,I_{16}$), so $\operatorname{rank}(X)=16$ and $\hat\beta=\tfrac1{16}X^\top\bar y$.
**One collinearity trap** (PLAN §III.2): the generator forces $x_E=x_Ax_Bx_Cx_D$ on the fraction, so an
explicit $E$ column equals the $ABCD$ column; never place *both* $E$ and $ABCD$ in the model.
Likewise each 2FI column equals a 3FI column on the fraction (e.g. $x_Dx_E=x_Ax_Bx_C$, see T2); we
include only the 2FI, so the 16-term model stays full-rank. `src/mixedlm` asserts
$\operatorname{rank}(X)=16$.

### T1.4 The estimators: main effects (from the fraction), and LOO/AOI contrasts

**Main effect and 2FI (fraction).** By orthogonality (T1.2 restricted to the 16 runs),

$$
\widehat{2\beta_i} = \tfrac{1}{8}\Big(\textstyle\sum_{x_i=+1}\bar y - \sum_{x_i=-1}\bar y\Big),\qquad
\widehat{2\beta_{ij}} = \tfrac{1}{8}\Big(\textstyle\sum_{x_ix_j=+1}\bar y - \sum_{x_ix_j=-1}\bar y\Big).
\tag{T1.5}
$$

**LOO (necessity) and AOI (sufficiency) as conditional contrasts.** These are *not* the marginal main
effects — they are the effect of a component **in a specific context**, which is exactly what
"necessary in the full skill" and "sufficient alone" should mean. Evaluate (T1.1) (through 2FI; 3FI+
absorbed into a remainder $R$) at the relevant corners. For $C_1$:

*Necessity* — flip $C_1$ from $+$ to $-$ with all partners **present** (FULL $\to$ LOO-C1):

$$
\text{Nec}_1 := \mathbb E[y_{\text{FULL}}]-\mathbb E[y_{\text{LOO-}C_1}]
= 2\beta_1 + 2\!\!\sum_{j\neq1}\beta_{1j}\;(+1) + R
= 2\beta_1 + 2\sum_{j\neq1}\beta_{1j} + R.
\tag{T1.6a}
$$

*Sufficiency* — turn $C_1$ on with all partners **absent** (NEUTRAL $\to$ AOI-C1):

$$
\text{Suff}_1 := \mathbb E[y_{\text{AOI-}C_1}]-\mathbb E[y_{\text{NEUTRAL}}]
= 2\beta_1 + 2\!\!\sum_{j\neq1}\beta_{1j}\;(-1) + R
= 2\beta_1 - 2\sum_{j\neq1}\beta_{1j} + R.
\tag{T1.6b}
$$

*Derivation of the sign flip.* In Nec$_1$ only $x_1$ changes ($+\to-$) while partners stay $+1$: the
main term contributes $\beta_1(+1)-\beta_1(-1)=2\beta_1$; each pair $\{1,j\}$ contributes
$\beta_{1j}[(+1)(+1)-(-1)(+1)]=2\beta_{1j}$; pairs not containing $1$ are unchanged and cancel. In
Suff$_1$ partners are $-1$, so pair $\{1,j\}$ contributes $\beta_{1j}[(+1)(-1)-(-1)(-1)]=-2\beta_{1j}$.
Hence the $\pm$ on the interaction sum. **The 3FI part is identical in both**: a triple $\{1,j,k\}$
contributes $\beta_{1jk}\cdot 2\,(x_jx_k)$, and in *both* contrasts the surviving partners have
$x_jx_k=+1$ (all $+$ in Nec, all $-$ in Suff, both squaring to $+1$), so each triple adds the same
$+2\beta_{1jk}$ to $R$ on both sides.

**The bridge across tiers.** Adding and subtracting (T1.6a,b), and using that the shared 3FI remainder
$R$ **cancels in the difference but survives in the sum**:

$$
\boxed{\;\tfrac12\big(\text{Nec}_i+\text{Suff}_i\big)=2\beta_i+R,\qquad
\tfrac14\big(\text{Nec}_i-\text{Suff}_i\big)=\sum_{j\neq i}\beta_{ij}\;\;(\text{exact through 3FI}).}
\tag{T1.7}
$$

So the **half-difference isolates the 2FI load exactly** (three-factor terms drop out by the parity
above; only 4FI+ contaminate it, and those are aliased-away/negligible per T2), whereas the average
carries the 3FI in $R$ and equals the pure main effect $2\beta_i$ only under the standing
"3FI+ negligible" assumption. This asymmetry is why $R$ appears in one box entry and not the other.

> PAPER-EQ (candidate): T1.7 — necessity and sufficiency of a component are the **same** quantity
> only when its interactions vanish; their average recovers the factorial main effect and their
> half-difference is the component's total 2FI load. This single identity links RQ1, RQ2, RQ3 and
> predicts the H3 asymmetry ("negatives help more once a palette is present" ⇒ $\sum_j\beta_{5j}>0$ ⇒
> Nec$_5>$ Suff$_5$).

This is *why* necessity (RQ1) and sufficiency (RQ2) are asked as separate questions and why the
factorial block (RQ3) is needed to interpret them: if the ten $\beta_{ij}$ are ≈0, LOO and AOI agree and
both equal the main effect; if interactions are positive (synergy), each component looks **more
necessary than sufficient** — components carry the skill *together*.

**What the off-fraction corners buy us.** The 16-run fraction alone estimates $\{\beta_0,\beta_i,
\beta_{ij}\}$ (16 params, saturated in the design — error d.f. comes only from prompt$\times$seed
replication, T2). The six off-fraction corners (5 LOO + NEUTRAL) are *not* added to the factorial model
matrix (T1.4); instead they supply the **direct paired contrasts** Nec$_i$, Suff$_i$ (and FULL−NEUTRAL)
that the confirmatory family tests. Formally, appending them would begin to *de-alias* main effects
from 4FIs (a full second fraction would give the complete $2^5$); with only $6/16$ of the alternate
fraction we cannot cleanly estimate the 4FIs, so we treat these corners as **replicated contrast
anchors**, not as factorial-model rows — consistent with the "3FI+ negligible" stance of T2. Replication
across tiers (FULL appears in the fraction *and* in every Nec$_i$; NEUTRAL in every Suff$_i$; each shared
across 5 seeds × 40 prompts) is what powers the objective signal even where the preference signal is
thin (PLAN §III.5 "power alignment").

**Used in:** PLAN §III.1 (cell table), §III.2 (model matrix), RQ1/RQ2/RQ3; PREREG §3; notebook
`05_stage1_analysis`. Feeds T2 (SEs), T6 (the 12-test Holm family).

---

## T2 — Aliasing of the resolution-V fraction

### T2.1 The alias group and the derivation rule

A half-fraction has a two-element defining contrast subgroup $\{I,\ ABCDE\}$. Two effects are **aliased**
(indistinguishable on the fraction) iff their columns are equal on all kept runs, which happens iff one
is the other times the defining word. Because each factor letter squares to the identity column
($x_i^2\equiv 1$), the alias of any effect $S$ is obtained by **multiplying by the defining word and
reducing mod squares**:

$$
S \;\equiv\; S\cdot ABCDE \pmod{x_i^2=1}.
\tag{T2.1}
$$

Worked examples: $A\cdot ABCDE = A^2BCDE = BCDE$; $AB\cdot ABCDE = A^2B^2CDE = CDE$;
$DE\cdot ABCDE=ABC D^2E^2=ABC$.

### T2.2 The full alias table (16 cosets)

| kept effect | alias (via $I=ABCDE$) | type pairing |
|---|---|---|
| $I$ | $ABCDE$ | — (defining word, length 5) |
| $A$ | $BCDE$ | main ↔ 4FI |
| $B$ | $ACDE$ | main ↔ 4FI |
| $C$ | $ABDE$ | main ↔ 4FI |
| $D$ | $ABCE$ | main ↔ 4FI |
| $E$ | $ABCD$ | main ↔ 4FI |
| $AB$ | $CDE$ | 2FI ↔ 3FI |
| $AC$ | $BDE$ | 2FI ↔ 3FI |
| $AD$ | $BCE$ | 2FI ↔ 3FI |
| $AE$ | $BCD$ | 2FI ↔ 3FI |
| $BC$ | $ADE$ | 2FI ↔ 3FI |
| $BD$ | $ACE$ | 2FI ↔ 3FI |
| $BE$ | $ACD$ | 2FI ↔ 3FI |
| $CD$ | $ABE$ | 2FI ↔ 3FI |
| $CE$ | $ABD$ | 2FI ↔ 3FI |
| $DE$ | $ABC$ | 2FI ↔ 3FI |

Sixteen cosets $= 32/2$, accounting for all $2^5$ effects. (This is PLAN Table T4.)

### T2.3 Why this is resolution V, and the estimability guarantee

The **resolution** of a fractional design is the length of the shortest word in the defining subgroup.
Here the only non-identity word is $ABCDE$ (length 5), so the design is **resolution V**. The general
rule "an $R_e$-resolution design aliases $p$-factor effects with $(R_e-p)$-and-higher effects" gives, for
$R_e=5$:

- $p=1$ (mains) aliased with $5-1=4$-factor interactions and higher — **mains ⟂ 2FI, 3FI**;
- $p=2$ (2FIs) aliased with $5-2=3$-factor interactions and higher — **2FIs ⟂ each other, ⟂ mains**.

> **Assumptions box (T2).** *3FI-and-higher negligible.* Under $\beta_{ijk}=\beta_{ijkl}=\beta_{ABCDE}=0$,
> the alias table shows each main-effect estimate carries only a 4FI contaminant and each 2FI estimate
> only a 3FI contaminant; both are assumed $\approx0$. For five **prescriptive** design components this
> is defensible: a genuine 3-way synergy (e.g. color×layout×typography beyond all pairwise synergies)
> is a priori small relative to mains and pairwise effects. The honest hedge: any surviving 2FI is
> reported as "$C_iC_j$ (aliased with the $C_kC_lC_m$ 3FI, assumed negligible)."

**Consequence.** All five main effects and all ten 2FIs are **cleanly and simultaneously estimable**
from 16 runs — exactly the estimand set of the factorial MixedLM (T1.3, PLAN §III.6). This is the
statistical justification for spending $16/32$ of the corners: we lose only the (assumed-null) 3FI+
structure.

**Used in:** PLAN §III.2, RQ3; Table T4; `src/mixedlm` factorial builder. Depends on T1; feeds T6 (BH
over the 10 2FIs).

---

## T3 — Mixed-effects models for the prompt×seed structure

### T3.1 The model

Each objective endpoint $y_{cps}$ (POC or a family metric) is measured for cell $c$, prompt $p$, seed
$s$. Cells are **fixed** (they are the designed manipulation); prompts and seeds are **random** (a
sample of tasks / stochastic decodes). The crossed/nested model (PLAN §III.6):

$$
y_{cps} \;=\; \mu + \tau_c + u_p + v_{cp} + \epsilon_{cps},\qquad
u_p\sim N(0,\sigma_p^2),\; v_{cp}\sim N(0,\sigma_{cp}^2),\; \epsilon_{cps}\sim N(0,\sigma^2),
\tag{T3.1}
$$

all independent. $\tau_c$ is the fixed cell mean (with $\sum_c\tau_c=0$ or a reference coding); $u_p$ is
the random prompt intercept (some briefs are intrinsically "designier"); $v_{cp}$ is the random
cell$\times$prompt slope (a component may help landing pages more than forms); $\epsilon$ is
seed-to-seed decode noise. Fit with `statsmodels MixedLM`, `groups=prompt`, random intercept (+ slope
where it converges). Binary render-success uses a binomial GLMM.

> PAPER-EQ (candidate): T3.1 — the inference model behind every objective delta; naming $u_p$ and
> $v_{cp}$ is what separates this study from per-generation $t$-tests.

### T3.2 Pseudoreplication: deriving the variance-inflation (design-effect) formula

Suppose we ignored the random effects and treated all $n$ generations of a cell as i.i.d. — the
"pseudoreplication" error. Consider a cell mean $\bar y$ over $G$ prompts with $m$ seeds each,
$n=Gm$. Within a prompt, two seeds share $u_p$ (and $v_{cp}$), so
$\operatorname{Corr}(y_{cps},y_{cps'})=\rho_{\mathrm{ICC}}$ for $s\neq s'$, where the **intraclass
correlation** is

$$
\rho_{\mathrm{ICC}}=\frac{\sigma_p^2+\sigma_{cp}^2}{\sigma_p^2+\sigma_{cp}^2+\sigma^2}.
\tag{T3.2}
$$

Compute the true variance of the mean (let $\sigma_y^2=\sigma_p^2+\sigma_{cp}^2+\sigma^2$ be the total
per-obs variance):

$$
\operatorname{Var}(\bar y)=\frac{1}{n^2}\Big[\underbrace{n\sigma_y^2}_{\text{diagonal}}
+\underbrace{G\,m(m-1)\rho_{\mathrm{ICC}}\sigma_y^2}_{\text{within-prompt covariances}}\Big]
=\frac{\sigma_y^2}{n}\big[1+(m-1)\rho_{\mathrm{ICC}}\big].
\tag{T3.3}
$$

The bracket is the **design effect** $\mathrm{DEFF}=1+(m-1)\rho_{\mathrm{ICC}}$. The i.i.d. formula
$\sigma_y^2/n$ understates the variance by this factor, so the naive $t$-statistic is inflated by
$\sqrt{\mathrm{DEFF}}$ and its nominal $\alpha$ is anti-conservative. Equivalently, the **effective
sample size** is

$$
\boxed{\,n_{\text{eff}}=\dfrac{n}{1+(m-1)\rho_{\mathrm{ICC}}}\,.}
\tag{T3.4}
$$

> PAPER-EQ (candidate): T3.4 — the one line that shows why "$5$ seeds $\times 40$ prompts $=200$
> independent points" is false. With $m=5$ and a modest $\rho_{\mathrm{ICC}}=0.3$,
> $\mathrm{DEFF}=1+4(0.3)=2.2$, so $n_{\text{eff}}\approx 200/2.2\approx 91$ — the honest $n$. The
> MixedLM recovers this automatically by partitioning variance into $\sigma_p^2,\sigma_{cp}^2,\sigma^2$.

### T3.3 Why pairing over prompts is efficient (and sets the bootstrap unit)

For a within-prompt contrast (e.g. Nec$_i=$ FULL$-$LOO-$C_i$), form
$d_p=\bar y_{\text{FULL},p\cdot}-\bar y_{\text{LOO},p\cdot}$ (average over seeds within prompt). Under
(T3.1) the prompt intercept $u_p$ is **common to both cells at prompt $p$ and cancels**:

$$
d_p=(\tau_{\text{FULL}}-\tau_{\text{LOO}})+(v_{\text{FULL},p}-v_{\text{LOO},p})+(\bar\epsilon_{\text{FULL},p}-\bar\epsilon_{\text{LOO},p}),
\tag{T3.5}
$$

so $\operatorname{Var}(d_p)=2\sigma_{cp}^2+2\sigma^2/m$ — free of the (usually large) $\sigma_p^2$. This is
the classical paired-design efficiency gain, and it is why the design **seed-matches** cells within a
prompt (PLAN §III.5) and why the **cluster bootstrap resamples whole prompts** (§T3.5): the prompt is
the exchangeable unit whose resampling preserves both $u_p$ and $v_{cp}$.

### T3.4 REML vs ML

The variance components $(\sigma_p^2,\sigma_{cp}^2,\sigma^2)$ are estimated by maximizing a likelihood.
**ML** treats the fixed effects $\tau_c$ as known when forming the variance likelihood, so it does not
"spend" degrees of freedom on them and yields **downward-biased** variance components (the mixed-model
analogue of dividing a sample variance by $n$ instead of $n-1$). **REML** maximizes the likelihood of a
maximal set of **error contrasts** $K^\top y$ with $K^\top X=0$ (linear combinations orthogonal to the
fixed-effects design), which removes the fixed effects from the objective and gives approximately
unbiased variance components. **Rule:**

- **REML** for reporting variance components, SEs, and CIs (our default; the DEFF/ICC we quote come from
  REML fits).
- **ML** when comparing **nested fixed-effects** models by likelihood ratio (e.g. "does adding the 2FI
  block improve fit?"), because REML likelihoods computed under different $X$ are **not comparable**
  (they are likelihoods of different contrast sets).

`src/mixedlm` defaults to REML and switches to ML only for LR comparisons of fixed structure.

### T3.5 Cluster bootstrap over prompts — assumptions and consistency

For estimands without clean parametric SEs (BT utilities T4; ratios like %-skill-reproduced T10;
composite POC contrasts), we resample **whole prompts** with replacement, refit, and take percentile
CIs (PLAN §III.5, §III.6). Justification:

- **Right cluster.** Prompts are the top exchangeable unit; seeds are nested and cells are crossed
  *within* a prompt. Resampling prompts preserves the entire within-prompt dependence
  ($u_p,v_{cp}$, shared brief, seed-matching), which the i.i.d. bootstrap would destroy.
- **Consistency conditions.** Treat the $G$ prompts as an i.i.d. sample from a population of briefs;
  let the statistic be a smooth (Hadamard-differentiable) functional of the prompt-level empirical
  measure. Then the cluster bootstrap distribution converges to the sampling distribution as
  $G\to\infty$.
- **Finite-$G$ caveat (honest).** We have $G=40$ dev prompts (18 held-out). Cluster-bootstrap CIs are
  **calibrated to the number of clusters**, not the number of generations; with 40 clusters the
  resolution of the tails is limited (a reason we also report parametric MixedLM CIs and treat the two
  as a robustness pair). We do **not** claim generalization beyond the task-type population the 58
  briefs sample.

### T3.6 Convergence-fallback ladder (what each rung preserves)

Random-slope mixed models frequently fail to converge on unbalanced seeds (headline cells 5 seeds,
interaction cells 3). The preregistered ladder (PLAN §III.6), and what each step still guarantees:

1. **Drop the random slope** $v_{cp}$ → random-intercept-only. *Preserves* the prompt-level clustering
   (the dominant variance term) and the $u_p$-cancellation of §T3.3; *loses* heterogeneity of the cell
   effect across prompts (SEs may be slightly optimistic if real slope variance exists).
2. **REML → ML.** Trades a little variance-component bias for a better-behaved optimizer; used only if
   REML will not converge.
3. **Per-prompt cluster bootstrap of the cell-mean contrast** (fully non-parametric). *Preserves*
   validity under the weakest assumptions (only prompt exchangeability + smoothness); *loses* the
   parametric efficiency of the mixed model. This is the floor: it always returns a usable CI.

The rung actually used is recorded per model (reproducibility; PLAN §VI.3).

**Used in:** PLAN §III.6 (analysis), RQ1–RQ4, RQ7-black-box; PREREG §4; `src/mixedlm`; notebook
`05_stage1_analysis`. Consumes T1 contrasts; feeds T5 (power on $n_{\text{eff}}$), T6 (test family).

---

## T4 — Chance-corrected agreement (the reliability gate)

The preference signal counts only if the VLM judge tracks human judgment. We quantify judge–human
agreement with two coefficients and gate on them (PREREG §5). The general chance-corrected form is

$$
\text{coeff}=\frac{p_o-p_e}{1-p_e},
\tag{T4.1}
$$

observed agreement $p_o$ minus chance agreement $p_e$, renormalized so perfect $=1$, chance $=0$. The
coefficients differ **only** in how $p_e$ is modeled.

### T4.1 Krippendorff's $\alpha_K$ (ordinal)

$$
\alpha_K = 1-\frac{D_o}{D_e},
\tag{T4.2}
$$

with $D_o$ the observed disagreement and $D_e$ the disagreement expected from the **pooled marginal**
category distribution. For a difference/metric $\,{}_{\delta}$ on categories $c,k$ these are, over the
coincidence matrix $o_{ck}$ (counts of $c$–$k$ pairings) with marginals $n_c$ and total $n$:

$$
D_o=\frac{1}{n}\sum_{c}\sum_{k}o_{ck}\,{}_{\delta^2_{ck}},\qquad
D_e=\frac{1}{n(n-1)}\sum_{c}\sum_{k}n_c\,n_k\,{}_{\delta^2_{ck}} .
\tag{T4.3}
$$

Measurement level enters through the metric ${}_{\delta^2_{ck}}$. **Nominal:** ${}_{\delta^2_{ck}}=\mathbb 1[c\neq k]$.
**Ordinal** (our graded preference "A ≫ / A > / tie / B > / B ≫", or A/tie/B): the metric is the squared
sum of intervening marginal masses,

$$
{}_{\delta^{2}_{ck}}=\Big(\sum_{g=c}^{k} n_g-\frac{n_c+n_k}{2}\Big)^{2},
\tag{T4.4}
$$

so that disagreeing across *adjacent* ordinal levels (A>-vs-tie) costs far less than across *extreme*
levels (A≫-vs-B≫). We use ordinal weighting because a judge that says "A slightly better" when the human
says "tie" is nearly right, and $\alpha_K$ should reflect that (PLAN §III.8). CIs by bootstrap over
labeled pairs.

### T4.2 Gwet's AC1 and its chance model

Krippendorff's $D_e$ uses the *empirical* marginals as if raters guessed by sampling from them —
which, under a dominant category, makes "chance agreement" nearly as high as observed agreement and
crushes $\alpha_K$ toward 0 (the **kappa paradox**). Gwet's AC1 replaces the chance model: it posits
that **random agreement can only occur on the subset of items about which raters are actually guessing**,
and estimates that propensity as

$$
p_e^{\gamma}=\frac{1}{q-1}\sum_{k=1}^{q}\pi_k(1-\pi_k),\qquad
\text{AC1}=\frac{p_o-p_e^{\gamma}}{1-p_e^{\gamma}},
\tag{T4.5}
$$

with $q$ categories and pooled marginals $\pi_k$. Note $\sum_k\pi_k(1-\pi_k)$ is maximized at the uniform
marginal and $\to0$ as one category dominates ($\pi_1\to1$): under extreme skew Gwet's chance term
**shrinks**, so AC1 stays near $p_o$ instead of collapsing. AC2 extends (T4.5) with ordinal weights; we
report AC1 for the binary decision and note AC2 where graded.

> PAPER-EQ (candidate): T4.2 + T4.5 — the two chance models side by side are the entire justification
> for a *disjunctive* reliability gate; a reviewer who knows only $\kappa$ needs this to accept
> "AC1 rescue under skew."

### T4.3 The kappa paradox in exact numbers (worked micro-example)

Two raters, $N=100$ binary items ("A preferred" = category 1). Hold the **agreement rate fixed at
$p_o=0.90$** and vary only the marginal skew.

**Skewed panel** (skill usually wins): both-1 $=85$, both-0 $=5$, disagree $=10$ (5 each direction).
Pooled marginals over the $2N=200$ judgments: $\pi_1=(2\cdot85+10)/200=0.90$, $\pi_0=0.10$.

$$
p_e=\pi_1^2+\pi_0^2=0.81+0.01=0.82,\quad D_e=1-p_e=0.18,\quad D_o=1-p_o=0.10,
$$
$$
\alpha_K = 1-\frac{0.10}{0.18}=0.444,\qquad
p_e^{\gamma}=\pi_1(1-\pi_1)+\pi_0(1-\pi_0)=0.09+0.09=0.18,\qquad
\text{AC1}=\frac{0.90-0.18}{0.82}=0.878.
$$

**Balanced panel** (same $p_o=0.90$): both-1 $=45$, both-0 $=45$, disagree $=10$. Now $\pi_1=\pi_0=0.5$:

$$
p_e=0.50=p_e^{\gamma}\ \Rightarrow\ \alpha_K=1-\frac{0.10}{0.50}=0.80,\quad \text{AC1}=\frac{0.90-0.50}{0.50}=0.80 .
$$

**Reading.** Identical 90% agreement yields $\alpha_K=0.44$ (skew) vs $0.80$ (balanced) — the coefficient
moved **only because of the marginal**, not the agreement. AC1 stayed at $0.88$ vs $0.80$. When marginals
are balanced the two coincide. (All figures reproduced in `scratchpad`; they are the F11 exemplar.)

### T4.4 The preregistered gate, operationally

$$
\textbf{Pass}\iff \alpha_K\ge 0.667\ \ \textbf{OR}\ \ \big(\text{AC1}\ge0.80\ \text{under demonstrable skew}\big).
\tag{T4.6}
$$

- $\alpha_K\ge0.667$ is Krippendorff's own "lowest acceptable for tentative conclusions"
  (`hayes2007alpha`); the primary rung.
- **"Demonstrable skew"** is operationalized, not eyeballed: the observed marginal must be imbalanced
  enough that the paradox is active — concretely, the majority preference category exceeds a
  preregistered share (report $\pi_{\max}$; skew is "demonstrable" when $\pi_{\max}\gtrsim0.80$, the regime
  where §T4.3 shows $\alpha_K$ depression) **and** the AC1 bootstrap CI lower bound clears 0.80. This
  prevents AC1 from being a loophole in the *balanced* case (where, by §T4.3, AC1 and $\alpha_K$ agree and
  AC1 cannot rescue a genuinely low-agreement judge).
- **Honesty note.** These thresholds are **convention, not derived optima** (`gwet2008ac1`,
  Landis–Koch bands are heuristic). They are frozen in PREREG §5 and reported with bootstrap CIs so a
  reader can apply a stricter bar.

**Used in:** PLAN §III.8 (judge protocol), PREREG §5, F11; `src/agreement` (runs now on synthetic
labels). Gates T4→T5 preference admissibility and the T6 two-signal rule.

---

## T5 — Bradley–Terry with style control

### T5.1 The base model, ties, and the likelihood

Each cell $i$ has latent design-quality strength $\beta_i$. Basic Bradley–Terry (`bradley1952rank`):

$$
P(i\succ j)=\frac{e^{\beta_i}}{e^{\beta_i}+e^{\beta_j}}=\sigma(\beta_i-\beta_j),\quad \sigma(z)=\frac{1}{1+e^{-z}} .
\tag{T5.1}
$$

Our judge returns ties (order-inconsistent verdicts → tie; PLAN §III.8). We model ties with the
**Davidson (1970)** extension, which adds a tie mass geometric in the two strengths:

$$
P(i\succ j)=\frac{e^{\beta_i}}{e^{\beta_i}+e^{\beta_j}+\nu\,e^{(\beta_i+\beta_j)/2}},\quad
P(\text{tie})=\frac{\nu\,e^{(\beta_i+\beta_j)/2}}{e^{\beta_i}+e^{\beta_j}+\nu\,e^{(\beta_i+\beta_j)/2}},
\tag{T5.2}
$$

with tie parameter $\nu\ge0$ ($\nu=0$ recovers T5.1). *Why the geometric-mean form:* ties should be most
likely when the two items are **evenly matched** ($\beta_i\approx\beta_j$), and (T5.2) makes
$P(\text{tie})$ peak at $\beta_i=\beta_j$ and decay as strengths separate — the correct qualitative
behavior, and it keeps the three probabilities summing to 1 by construction. We prefer this to
"split a tie as half-win/half-loss," which throws away the information that an order-inconsistent verdict
signals *near-equality*.

**Estimation = logistic/multinomial regression.** With one indicator per cell, the log-likelihood over
observed comparisons is concave in $\beta$ (sum of log-sigmoids/log-softmaxes of linear functions), so
the MLE is found by standard convex optimization (`src/bt_model`).

### T5.2 Identifiability and the reference constraint

The likelihood depends on $\beta$ **only through differences** $\beta_i-\beta_j$ (and, in Davidson, the
common shift also cancels in every term after normalization). Hence $\beta$ and $\beta+c\mathbf1$ give the
identical likelihood — one non-identified direction. We remove it by fixing the reference cell

$$
\beta_{\text{NEUTRAL}}=0,
\tag{T5.3}
$$

so every reported strength is "utility **relative to the length-matched neutral control**" — exactly the
scientifically meaningful zero (ADR-003). All CIs are for contrasts $\beta_i-\beta_{\text{NEUTRAL}}=\beta_i$
or $\beta_i-\beta_j$.

### T5.3 Connectivity: when the MLE exists

A finite MLE requires the **comparison digraph** (arc $i\to j$ when $i$ beats $j$ at least once) to be
**strongly connected** — equivalently **Ford's condition**: for every partition of the cells into two
nonempty sets, some cell in each set beats some cell in the other. If a cell only ever wins (or a subset
always beats its complement), its $\hat\beta\to+\infty$ (degenerate). This is why the preference protocol
is a **designed hub graph**, not arbitrary pairs (PLAN §III.5): every cell is compared to **FULL and/or
NEUTRAL**, and FULL–NEUTRAL are compared to each other, so there is a directed path (via ties and mixed
outcomes across prompts/seeds) between any two cells and back. The hub guarantees connectivity at minimum
judgment cost.

### T5.4 Style control: deriving why it purges judge bias (and when it backfires)

VLM judges are known to reward length/verbosity/format/colorfulness independent of quality
(`zheng2023mtbench`, `chiang2024stylecontrol`). Augment (T5.1)/(T5.2) with per-page style covariates $s$
(differences $s_i-s_j$) and coefficient $\gamma$:

$$
\boxed{\,P(i\succ j)=\sigma\!\big((\beta_i-\beta_j)+\gamma^\top(s_i-s_j)\big)\,}\qquad
s=\big(\log\!\text{DOM},\ \log\!\text{tok},\ \#\text{elem},\ \text{colorfulness},\ \text{text-density}\big).
\tag{T5.4}
$$

> PAPER-EQ (candidate): T5.4 — the preference endpoint the whole oracle's second signal is built on;
> the covariate list is the analysis-level twin of the design-level length-matched control.

**Omitted-variable derivation.** Suppose the *true* judgment process is (T5.4) with quality difference
$\Delta^{\text{qual}}_{ij}=\beta_i-\beta_j$ and style channel $\gamma^\top(s_i-s_j)$. If we **omit** style
and fit the plain BT $\sigma(b_i-b_j)$, then (to first order, exactly in the linear-probit analogue) the
estimated strength gap absorbs the systematic style difference between the cells:

$$
\hat b_i-\hat b_j \;\longrightarrow\; \underbrace{(\beta_i-\beta_j)}_{\text{substance}}
\;+\;\gamma^\top\underbrace{(\bar s_i-\bar s_j)}_{\text{cell-mean style gap}} ,
\tag{T5.5}
$$

where $\bar s_i$ is cell $i$'s mean style. If the skill systematically produces longer/denser/more
colorful pages ($\bar s_{\text{FULL}}\neq\bar s_{\text{NEUTRAL}}$), plain BT **inflates** the design
effect by $\gamma^\top(\bar s_{\text{FULL}}-\bar s_{\text{NEUTRAL}})$. Including $s$ identifies $\gamma$
from **within-cell** style variation (pages of the same cell that happen to differ in length) and
subtracts the bias, leaving $\hat\beta$ as substance. This is standard omitted-variable-bias logic:
the bias equals (coefficient of the omitted regressor) $\times$ (its cell-conditional mean shift).

**When it backfires — the collinearity / mediation trap.** If a cell has **no within-cell style
variation**, or if the component's *causal effect flows through the covariate*, then $s$ and the cell
indicator are collinear and the model cannot separate "quality" from "style." Concretely, C1's real
mechanism partly **is** to set a deliberate, moderate colorfulness; regressing out colorfulness would
then absorb a **genuine** C1 effect. Preregistered interpretation rule (PLAN §III.5 C3-note):

1. **Covariate choice is by bias-channel, not design-channel.** $\log$DOM, $\log$tok, \#elem,
   text-density are pure judge-bias channels (a designer does not judge quality by node count). These
   are always controlled.
2. **Colorfulness is included but flagged as partially causal.** Because color *is* a design lever, we
   (a) report both the style-controlled and the uncontrolled $\hat\beta$ so the adjustment is visible,
   and (b) recover the legitimate color effect through the **objective** channel — the POC's
   $-|\text{colorfulness}-c^\*|$ term (T7) and the RQ8 color-family steering signature (T8) — which are
   not routed through the judge and therefore not double-counted. If controlled and uncontrolled
   $\hat\beta$ disagree in sign, the contrast is reported as **style-confounded** rather than resolved.
3. **CIs** by cluster bootstrap over prompts (T3.5), $B=2000$.

**Used in:** PLAN §III.5 (BT), RQ1/RQ2/RQ4/RQ6; PREREG §4/§7; `src/bt_model`; F1, F8. Consumes T3.5
(clustered CIs); its utilities feed T5→power (T6) and the two-signal rule (T6.4).

---

## T6 — Power (paired-preference sizing) and multiplicity

### T6.1 McNemar paired power from first principles

Preference comparisons are **paired** (cell A vs cell B on the *same* prompt, seed-matched). Classify each
of the $N$ judged pairs as **decisive** — an order-consistent A-win or B-win — or a **tie** (an
order-inconsistent verdict, treated as non-decisive; PLAN §III.8). Let $\pi_b,\pi_c$ be the
**unconditional** (over all pairs) probabilities of a decisive A-win and a decisive B-win respectively
(so the tie mass is $1-\pi_b-\pi_c$). Define

$$
p_d=\pi_b+\pi_c\ \ (\text{P a pair is decisive}),\qquad \delta=\pi_b-\pi_c\ \ (\text{signed gap}).
$$

McNemar conditions on the decisive pairs and tests $H_0:\pi_b=\pi_c$ (no preference), i.e. among decisive
pairs the winner is a fair coin. Given $N_{\text{dec}}$ decisive pairs, the count $b\sim\text{Bin}(N_{\text{dec}},\theta)$
with $\theta=\pi_b/p_d$; $H_0:\theta=\tfrac12$. A normal approximation with continuity dropped gives the
general sample-size formula (PLAN §III.7):

$$
\boxed{\,N\;\approx\;\frac{\big(z_{1-\alpha/2}\sqrt{p_d}+z_{1-\beta}\sqrt{p_d-\delta^2/p_d}\big)^2}{\delta^2}\,},
\tag{T6.1}
$$

where $N$ is the number of **total** pairs, $z_{1-\alpha/2}=1.95996$ (two-sided $\alpha=0.05$),
$z_{1-\beta}=0.84162$ (power $0.80$).

### T6.2 Reproducing the plan's numbers exactly

The clean way to see PLAN's headline figures is to **count decisive pairs** and test the conditional
split $\theta$ against $\tfrac12$ — algebraically the one-sample proportion test, and identical to
(T6.1) with $p_d=1$ (every counted pair decisive). With $\theta_1$ the alternative win-share among
decisive pairs and $\theta_0=\tfrac12$:

$$
N_{\text{dec}}\approx\frac{\big(z_{1-\alpha/2}\sqrt{\theta_0(1-\theta_0)}+z_{1-\beta}\sqrt{\theta_1(1-\theta_1)}\big)^2}{(\theta_1-\theta_0)^2}.
\tag{T6.2}
$$

| split $\theta_1$ | $\sqrt{\theta_0(1-\theta_0)}$ | $\sqrt{\theta_1(1-\theta_1)}$ | $(\theta_1-\theta_0)^2$ | $N_{\text{dec}}$ | PLAN |
|---|---|---|---|---|---|
| $0.60$ | $0.5$ | $\sqrt{0.24}=0.48990$ | $0.01$ | $\dfrac{(1.95996\cdot0.5+0.84162\cdot0.48990)^2}{0.01}=193.8$ | $\sim200$ |
| $0.65$ | $0.5$ | $\sqrt{0.2275}=0.47697$ | $0.0225$ | $\dfrac{(0.97998+0.40142)^2}{0.0225}=84.8$ | $\sim80$ |
| $0.55$ | $0.5$ | $\sqrt{0.2475}=0.49749$ | $0.0025$ | $\dfrac{(0.97998+0.41866)^2}{0.0025}=782.5$ | $\sim780$ |

All three reproduce (arithmetic in `scratchpad`).

> PAPER-EQ (candidate): T6.2 — the sizing that justifies the judgment budget (200 pairs on
> FULL–NEUTRAL, ~120 on necessity edges); the numbers a reviewer will spot-check.

**Reconciling $N$, $N_{\text{dec}}$, and the "$p_d\approx0.5$" remark (a mis-plug warning).** PLAN quotes
"~200 **informative** pairs" and also "$p_d\approx0.5$." These are consistent **only** if $N_{\text{dec}}$
(informative pairs) is what "~200" counts, and $p_d$ converts to **total** judged pairs
$N=N_{\text{dec}}/p_d$: with $p_d=0.5$ (half the pairs tie), detecting 60/40 needs ~200 decisive → ~400
total judge calls. **Do not** plug the *marginal* $\delta=0.2$ together with $p_d=0.5$ into (T6.1): that
mixes a conditional split with a total-pair discordance rate and yields $N\approx93$ — neither 200 nor
400. The internally consistent readings are: (i) $N_{\text{dec}}$ via (T6.2) $=194\approx200$; or (ii)
(T6.1) with the *marginal* $\delta=0.1,\ p_d=0.5$ giving $N=388$ total, $\times p_d=194$ decisive. Both
land on **~200 decisive pairs**; the file uses (T6.2) as canonical and flags the mis-plug so the
budget arithmetic is not silently wrong.

### T6.3 Post-hoc power as an admissibility screen (not inference)

The **power gate** (PREREG §6): a preference delta counts as a signal only if its contrast achieved
$\ge$ the pairs (T6.2) requires **at the observed $\hat\theta$**. This is deliberately used as a
**screen on the design**, not as a $p$-value interpretation. The known caveat: "observed (post-hoc)
power" is a monotone transform of the observed $p$-value, so re-reporting it as evidence is circular
(a non-significant result *always* has low observed power — it tells you nothing new about the truth).
We escape the circularity by using it **only** to decide *admissibility of the preference channel* — if
a contrast is under-powered, we do **not** reinterpret it as a null; we fall back to the **objective**
channel for the two-signal rule (T6.4), or raise seed-pairs up to the budget (a pre-stated contingency).
Post-hoc power here answers "is the preference evidence strong enough to *use*," never "is the effect
real."

### T6.4 Multiplicity: Holm (confirmatory) and BH (exploratory)

**Holm's step-down (FWER control under arbitrary dependence).** Order the $m$ confirmatory $p$-values
$p_{(1)}\le\dots\le p_{(m)}$. Reject $H_{(k)}$ while $p_{(k)}\le \alpha/(m-k+1)$, stopping at the first
failure. *Proof of FWER $\le\alpha$.* Let $H_{(1')},\dots$ be the true nulls and let $p_{(j^\*)}$ be the
smallest true-null $p$-value, at position $j^\*$ in the sorted list. A false rejection requires
$p_{(j^\*)}\le\alpha/(m-j^\*+1)$. Because all $j^\*-1$ predecessors are (rejected) among the $m$
hypotheses and at most $m-|\{\text{true nulls}\}|$ of them are false nulls, the number of hypotheses with
$p$-value $\le p_{(j^\*)}$ that could precede it is bounded so that $m-j^\*+1\ge |\mathcal T|$, the number
of true nulls. Hence the event of *any* false rejection implies some true-null $p$-value $\le\alpha/|\mathcal T|$,
and by the union (Bonferroni) bound over the $|\mathcal T|$ true nulls,
$\mathrm{FWER}\le|\mathcal T|\cdot\alpha/|\mathcal T|=\alpha$ — using **only** the marginal validity of each
$p$-value, no independence. Holm is uniformly more powerful than Bonferroni (larger thresholds for later
steps).

**Benjamini–Hochberg (FDR control under PRDS).** Order as above; let
$k^\*=\max\{k:\ p_{(k)}\le \tfrac{k}{m}q\}$ and reject $H_{(1)},\dots,H_{(k^\*)}$. BH controls the
**false discovery rate** $\mathrm{FDR}=\mathbb E[V/\max(R,1)]\le \tfrac{m_0}{m}q\le q$ (with $V$ false,
$R$ total rejections, $m_0$ true nulls) whenever the test statistics are **PRDS** (positive regression
dependent on the null subset) — a monotone-positive-dependence condition satisfied by, e.g., statistics
that are positively correlated. Our exploratory scans are **positively correlated metric families on
shared renders** (align-regularity, whitespace, type-scale, contrast all move together on a good page),
which is the sanctioned PRDS use-case; hence BH (not Bonferroni) for the 10 2FIs, per-family scans,
per-task-type breakdowns.

**The philosophical split (why Holm here, BH there).** Confirmatory claims (RQ1 necessity, RQ2
sufficiency, RQ4 nudge, the Stage-2 families) are **headline** — a single false claim is costly, so we
control the **family-wise** error (Holm, FWER 0.05). Exploratory scans are **discovery-mode** — we accept
a controlled *fraction* of false leads to retain power (BH, FDR 0.10). The confirmatory family is frozen
in PREREG §4: the 12 tests $\{$FULL$-$NEUTRAL; $5\times$FULL$-$LOO-$C_i$; $5\times$AOI-$C_i-$NEUTRAL;
FULL$-$BEAUTY1$\}$, applied **separately** to the POC family and the BT family.

### T6.5 The two-signal null rule as a decision rule (false-claim algebra)

PREREG §8 (verbatim, non-negotiable): an effect is **non-null** iff it moves the **objective** signal
(POC Holm-significant, OR $\ge2$ concordant BH-significant families) **OR** a preference delta passing
**both** the reliability gate (T4.6) and the power gate (T6.3). Two error-rate facts follow.

- **The "non-null" OR loosens Type-I (deliberately), bounded by a union.** Let $A$ = "objective signal
  fires under $H_0$" and $B$ = "gated preference fires under $H_0$." The claim "non-null" is $A\cup B$, so

$$
\Pr(\text{false non-null}\mid H_0)=\Pr(A\cup B)\le \Pr(A)+\Pr(B)\le \alpha_{\text{obj}}+\alpha_{\text{pref}}.
\tag{T6.3}
$$

  With each channel Holm/gate-controlled near $0.05$, the disjunction's false-positive rate is
  $\lesssim0.10$. This is an **intentional** trade: the project's dominant risk is a **false null**
  (missing a real component effect / declaring the design direction dead), so a disjunctive evidence
  standard raises power. It is safe because the objective channel is **deterministic and unfoolable**
  (its only error is sampling, honestly controlled) and the preference channel is **separately gated**
  for reliability and power before it may fire.

- **The Stage-2 headline is an AND — false-claim rate multiplies down.** RQ6 success (PREREG §7)
  requires **all** of: steered $\succ$ unsteered on $\ge1$ objective family after Holm ($E_1$); gated BT
  CI $>0$ ($E_2$); norm-matched random control fails both ($E_3$); flip test attenuates ($E_4$). Under a
  true null (no causal design direction),

$$
\Pr(\text{false Stage-2 claim}\mid H_0)=\Pr(E_1\cap E_2\cap E_3\cap E_4\mid H_0)\ \le\ \min_k \Pr(E_k\mid H_0),
\tag{T6.4}
$$

  and, to the extent the four checks probe **independent** failure modes (objective vs preference vs
  specificity vs necessity), the joint is far below any single $\alpha$. This is why the "hard bar" can be
  claimed at all: conjunction is what buys a *causal* headline out of individually-fallible tests.

> PAPER-EQ (candidate): T6.3 + T6.4 — the two-signal rule stated as error algebra: the necessity/
> sufficiency *screen* uses a power-raising OR; the causal *headline* uses a false-positive-crushing AND.

**Used in:** PLAN §III.6/§III.7 (power, multiplicity), PREREG §4/§6/§7/§8; all confirmatory RQs;
`src/power`, `src/mixedlm`, `src/bt_model`. Consumes T3 ($n_{\text{eff}}$), T4 (gate), T5 (BT).

---

## T7 — Objective-metric formalism (the deterministic oracle half)

All metrics are computed on the **rendered** DOM + screenshot (CLAUDE.md; PLAN Appendix B), never on raw
code strings. `src/metrics_dom` uses Playwright `boundingBox()`/`getComputedStyle`; `src/metrics_visual`
uses the desktop $1440\times900$ PNG. Below each metric is defined as a computable function with its
$[0,1]$ orientation; the section closes with the POC as a formal function of the metric vector.

### T7.1 WCAG relative luminance and contrast (family A)

For an sRGB channel value $C\in[0,1]$, linearize (undo gamma):

$$
C_{\text{lin}}=\begin{cases} C/12.92, & C\le 0.03928\\[2pt] \big((C+0.055)/1.055\big)^{2.4}, & C>0.03928.\end{cases}
\tag{T7.1}
$$

Relative luminance $L=0.2126\,R_{\text{lin}}+0.7152\,G_{\text{lin}}+0.0722\,B_{\text{lin}}$ (the
luminosity weights are the sRGB → CIE-Y row). Contrast ratio between a lighter $L_1$ and darker $L_2$:

$$
\mathrm{CR}=\frac{L_1+0.05}{L_2+0.05}\in[1,21].
\tag{T7.2}
$$

Per text node we compute CR(text color, effective background); report `contrast_frac_below_4_5`,
`contrast_min`, `contrast_median`. AA thresholds: 4.5 (normal text), 3.0 (large). The $+0.05$ flare term
models ambient reflection so pure black-on-black is $\mathrm{CR}=1$, white-on-black $=21$.

> PAPER-EQ (candidate): T7.2 — the accessibility endpoint (a POC term and a family-A signal);
> deterministic and legally standardized, the archetype of "unfoolable."

### T7.2 Ngo layout measures (family L)

From element bounding boxes; each $\in[0,1]$, higher = better (`ngo2003modelling`). Define an element's
weight as area, and axis balance via summed weight $\times$ distance on each side of the frame axis:

$$
\mathrm{BM}=1-\frac{|BM_v|+|BM_h|}{2},\quad
BM_{\text{axis}}=\frac{\sum_{\text{left}}a_k d_k-\sum_{\text{right}}a_k d_k}{\max(\sum_{\text{left}}a_k d_k,\ \sum_{\text{right}}a_k d_k)} .
\tag{T7.3}
$$

$$
\mathrm{EM}=1-\frac{|EM_x|+|EM_y|}{2},\quad
EM_x=\frac{2}{n_{\text{el}}\,W}\sum_k a_k (x_k-x_{\text{center}}),\ \text{(analogously }EM_y),
\tag{T7.4}
$$

i.e. the normalized offset of the layout's **center of mass** from the frame center (centered mass →
high equilibrium). $\mathrm{SYM}$ is the normalized agreement of reflected object measures
(x, y, width, height, distance-to-center) across the vertical/horizontal/diagonal axes. Alignment /
grid regularity via **distinct-edge counts**:

$$
\texttt{align\_regularity}=1-\frac{n_{\text{distinct edges}}}{n_{\text{elements}}},
\tag{T7.5}
$$

over the multiset of left/right/top/bottom edge coordinates (few shared edges → many alignment lines →
low regularity). $\texttt{whitespace\_ratio}=1-\texttt{occupied\_area}/\texttt{viewport\_area}$;
$\texttt{density}=\texttt{occupied\_area}/\texttt{viewport\_area}$ (used with an inverted-U prior).

**Gap-entropy variant (alignment/rhythm).** Let $\{g_1,\dots,g_m\}$ be inter-element gaps along an axis,
binned into $B$ bins of a fixed width (e.g. 4 px) with empirical bin probabilities $\hat p_b$. The
**Shannon gap entropy**

$$
H_{\text{gap}}=-\sum_{b=1}^{B}\hat p_b\log \hat p_b
\tag{T7.6}
$$

is **low** when gaps concentrate on a regular spacing scale (a designed rhythm) and **high** when spacing
is scattered. We report $H_{\text{gap}}$ normalized by $\log B$ so it lies in $[0,1]$; the fixed bin width
is frozen in `config/render.yaml` (entropy is binning-dependent — the width must be pinned for
comparability).

### T7.3 Typography (family T)

`n_font_sizes`, `n_font_families` from computed styles. **Modular type-scale adherence**: adjacent
distinct font sizes, sorted, produce ratios $r_k=\text{size}_{k+1}/\text{size}_k$; a modular scale has a
common geometric ratio $r$. We fit $r$ over the canonical set $\{1.125,1.2,1.25,1.333,1.414,1.5\}$ and
score

$$
\texttt{type\_scale\_adherence}=\frac{1}{K}\sum_{k=1}^{K}\mathbb 1\!\big[\,|\log r_k-\log r^\*|\le \log(1.10)\,\big],\quad
r^\*=\arg\max_{r}\ \#\{k:\,|\log r_k-\log r|\le\log1.10\},
\tag{T7.7}
$$

i.e. the fraction of adjacent ratios within $\pm10\%$ (in log space, so the tolerance is symmetric in
ratio) of the best-fitting modular ratio. Log-space is the natural metric for multiplicative scales.

### T7.4 Hasler–Süsstrunk colorfulness (family C)

On screenshot pixels, opponent axes $rg=R-G$, $yb=\tfrac12(R+G)-B$ (`hasler2003colorfulness`):

$$
\sigma_{rgyb}=\sqrt{\sigma_{rg}^2+\sigma_{yb}^2},\quad \mu_{rgyb}=\sqrt{\mu_{rg}^2+\mu_{yb}^2},\quad
\boxed{\,M=\sigma_{rgyb}+0.3\,\mu_{rgyb}\,}.
\tag{T7.8}
$$

$M$ correlates $>0.9$ with human colorfulness ratings; the $0.3$ weights the mean-saturation term below
the spread term (spread of hue/saturation dominates perceived colorfulness). Also `n_dominant_colors`
(quantized palette size) and `figure_ground` (fg–bg mean-color distance).

### T7.5 Visual complexity (family X)

$\texttt{complexity}=\texttt{quadtree\_leaf\_count}$ from a space-based decomposition to a fixed
variance threshold, normalized by a max; used with the **inverted-U** appeal prior
(`reinecke2013predicting`): both extremes hurt.

### T7.6 The purple-slop index (PSI) — the skill's own negatives, made measurable

C5 (negatives) tells us exactly what "AI slop" is; we measure precisely those tells (PLAN §III.3, App B.7):

$$
\mathrm{PSI}=0.30\,\underbrace{\text{hueFrac}[260^\circ,290^\circ]}_{\text{purple pixels}}
+0.30\,\underbrace{\text{gradientBgPrevalence}}_{\text{hero gradients}}
+0.25\,\underbrace{\text{InterRobotoShare}}_{\text{default fonts}}
+0.15\,\underbrace{\text{centeredHeroFlag}}_{\text{centered hero}} ,
\tag{T7.9}
$$

each subcomponent $\in[0,1]$: `hueFrac` = share of salient pixels with HSV hue in $[260^\circ,290^\circ]$;
`gradientBgPrevalence` = fraction of large/hero elements with a `linear-gradient` background;
`InterRobotoShare` = fraction of text using Inter/Roboto/system-ui; `centeredHeroFlag` = 1 if a large
centered flex block sits in the top viewport third. Lower PSI = less slop. Report subcomponents **and**
composite.

### T7.7 The Primary Objective Composite (POC) as a formal function

To have **one** primary objective number per generation for the confirmatory family while honoring
"don't aggregate raw metrics blindly" (`si2024design2code`), the POC is a pre-registered mean of
**oriented, z-scored** core metrics. Let $z(\cdot)$ denote z-scoring over **all dev generation units**
(the reference distribution; frozen), and orient each term so higher = better. Define the metric vector
$\mathbf x$ and

$$
\mathrm{POC}(\mathbf x)=\frac{1}{7}\Big[
z(\texttt{align\_reg})+z(\texttt{whitespace})+z(\texttt{type\_scale})+z(\texttt{contrast\_pass})
-z(\texttt{overflow\_overlap})-z(\mathrm{PSI})-z\big(|\,M-c^\*|\big)\Big],
\tag{T7.10}
$$

with $\texttt{contrast\_pass}=1-\texttt{contrast\_frac\_below\_4\_5}$,
$\texttt{overflow\_overlap}=n_{\text{overflow}}+n_{\text{overlap}}$, and $M$ the Hasler colorfulness
(T7.8). The colorfulness term is a **distance to a target** $c^\*$ (not "more is better") — the
inverted-U/moderate-colorfulness prior (`reinecke2013predicting`).

> PAPER-EQ (candidate): T7.10 — the primary objective endpoint; every RQ1/RQ2/RQ4/RQ6 objective delta is
> a contrast on this scalar. Its exact definition (7 terms, orientation, z-reference) is what makes the
> confirmatory tests preregisterable.

**Construction rules (formal, frozen).**
- **Orientation**: signs above; z-scoring uses the dev-unit mean/SD so cross-cell comparisons are on a
  common scale.
- **Render-fail exclusion**: units with `render_success = 0` (or non-hermetic, re-scored 0) are
  **excluded** from POC and counted in family V — a non-rendering page is a validity null regardless of
  aesthetics (`wu2024uicoder`). POC is thus defined on the rendered subset; family V carries the render
  rate as its own endpoint.
- **Two pre-specified conditionals** (part of the frozen endpoint, *not* post-hoc; PREREG §4, §9):
  (i) **PSI-out 6-term variant** — if PSI fails its admission gate ($\rho(\mathrm{PSI},\text{human "AI"
  rating})\ge0.4$), drop the $-z(\mathrm{PSI})$ term and average the remaining **six**; every
  confirmatory decision then uses the 6-term POC. (ii) **$c^\*$ fallback** — $c^\*=$ median $M$ of
  human-preferred pages **iff** $\ge30$ such pages exist; else $c^\*=$ median $M$ of the dev FULL-cell
  generations (the skill-on distribution operationalizes "moderate colorfulness" without human data).
  The branch that fires is written to the manifest **before** the first confirmatory test.

Formally, POC is a **piecewise** function of $\mathbf x$ selected by two frozen indicators
$(\mathbb 1_{\text{PSI-admit}},\mathbb 1_{\ge30})$; both are measurable pre-analysis, so the estimand is
well-defined before any test is run.

### T7.8 Why UIClip/CLIP are validation targets, not oracle evidence

UIClip (design-quality score) and CLIP (prompt↔screenshot relevance) are **learned** signals. They are
**inadmissible as oracle evidence** because (a) their provenance is **non-deterministic and opaque** — a
neural scorer can be wrong or biased in ways we cannot audit, violating the "deterministic and
unfoolable" requirement (CLAUDE.md); and (b) they carry **distribution shift** — UIClip was trained on a
mobile-screenshot distribution unlike our desktop $1440\times900$ renders (`wu2024uiclip`), so its scores
may not transport. They are retained as **auxiliary validation targets**: UIClip is admitted as a
*secondary* signal only if $\rho(\mathrm{UIClip},\text{human win-rate})\ge0.3$ on the human subset, and
even then it never enters the POC or a confirmatory decision. This keeps the oracle's evidentiary half
fully computable while still using the learned signals to cross-check.

**Used in:** PLAN §III.3/§III.4, App B; PREREG §4/§9; every objective endpoint; `src/metrics_dom`,
`src/metrics_visual`; F4, F10. Feeds T6 (POC is the Holm endpoint) and T8/T10 ($Q=$ POC in the causal
tests).

---

## T8 — Interpretability I: residual stream, diff-in-means, addition, ablation, probing, patching

This is the mathematical core of Stage 2 — the paper's Part-2 backbone.

### T8.1 The residual-stream formalism and why it is the intervention locus

Qwen2.5-Coder-7B is a **pre-norm** decoder ($L=28$ layers, width $d=3584$; ADR-001). Layer $\ell$
updates the residual stream by **adding** the attention and MLP contributions of the *normalized* input:

$$
h^{\ell+1}=h^{\ell}+\mathrm{Attn}^{\ell}\!\big(\mathrm{LN}(h^{\ell})\big)+\mathrm{MLP}^{\ell}\!\big(\mathrm{LN}(h^{\ell})\big).
\tag{T8.1}
$$

Because every block **reads** a LayerNorm of the stream and **writes back additively**, the residual
stream is a **linear communication channel**: the layer-$\ell$ state is the running sum
$h^{\ell}=\text{embed}+\sum_{\ell'<\ell}(\text{writes})$, and the logits are
$W_U\,\mathrm{LN}(h^{L})$. Two consequences make it the natural place to read and write concepts:

1. **Linear read/write.** A concept encoded as a direction can be *read* by projection
   ($\langle h,\hat v\rangle$) and *written* by addition ($h+\alpha\hat v$) with first-order-additive
   effect on downstream reads — exactly the operations Stage 2 needs.
2. **Linear representation hypothesis / superposition.** High-level concepts are (approximately) linear
   directions (`park2023lrh`, `park2024geometry`), and superposition packs many features as directions
   (not neurons) in the $d$-dim space (`elhage2022superposition`) — so **directions**, not units, are the
   correct object, and the residual stream is where they live. We intervene on `model.model.layers[i]`
   output `[0]`, shape $[\text{batch},\text{seq},3584]$ (ADR-002).

**Activation sites.** For a teacher-forced pass over `[prompt ‖ response]`, define $h_\ell(t)$ as the
layer-$\ell$ output at token $t$. Contrast statistics use the **mean over response tokens**
$\bar h_\ell=\frac{1}{|R|}\sum_{t\in R}h_\ell(t)$ (the behavior manifests in the output, not the prompt;
`chen2025persona`).

### T8.2 Diff-in-means, and its optimality as a linear discriminant

The **clean-design direction** at layer $\ell$ is the difference of response-mean residuals between the
FULL and NEUTRAL sides, over the 200 matched dev pairs (PLAN S2.0/S2.2):

$$
\boxed{\,v_\ell=\bar h_\ell^{(\text{FULL})}-\bar h_\ell^{(\text{NEUTRAL})},\qquad \hat v_\ell=v_\ell/\lVert v_\ell\rVert\,}.
\tag{T8.2}
$$

> PAPER-EQ (candidate): T8.2 — the extracted design direction; the object every Stage-2 causal claim is
> about. Its contrast (skill vs length-matched neutral) is what makes it "design content," not
> "instruction-following mode" (ADR-003).

**Why diff-in-means (and not a probe direction) for *causal* steering.** Model the two classes as Gaussian
with a **shared covariance** $\Sigma$ and means $\mu_1$ (FULL), $\mu_0$ (NEUTRAL), equal priors. The
Bayes-optimal classifier compares log-likelihoods; for equal-covariance Gaussians,

$$
\log\frac{p(h\mid 1)}{p(h\mid 0)}
=-\tfrac12(h-\mu_1)^\top\Sigma^{-1}(h-\mu_1)+\tfrac12(h-\mu_0)^\top\Sigma^{-1}(h-\mu_0)
= h^\top\underbrace{\Sigma^{-1}(\mu_1-\mu_0)}_{w^\*}-\tfrac12(\mu_1^\top\Sigma^{-1}\mu_1-\mu_0^\top\Sigma^{-1}\mu_0),
\tag{T8.3}
$$

so the optimal **discriminant direction** is $w^\*=\Sigma^{-1}(\mu_1-\mu_0)$ — Fisher's LDA (and the
population limit of a well-regularized logistic probe). Diff-in-means is $v=\mu_1-\mu_0$, which equals
$w^\*$ **iff $\Sigma\propto I$** (isotropic): then $w^\*=\sigma^{-2}(\mu_1-\mu_0)\propto v$.

> PAPER-EQ (candidate): T8.3 — the LDA/diff-in-means relationship; the formal reason a *probe* direction
> and a *steering* direction differ, and why we steer with the un-whitened one.

**The causal-shift argument (`arditi2024refusal`).** For *steering* we want the vector that, added to a
NEUTRAL activation, moves it to where FULL activations actually live — i.e. the **empirical mean shift**
$\mu_1-\mu_0$, which by construction lies on the between-class axis and **on the data manifold**. The
whitened discriminant $\Sigma^{-1}(\mu_1-\mu_0)$ is optimal for **reading** (it re-weights by inverse
variance to maximize separation) but for **writing** it is pathological: it **amplifies low-variance
nuisance directions** (dividing by small $\Sigma$ eigenvalues), so adding it pushes activations
**off-distribution** along directions the model rarely uses, degrading coherence without a
correspondingly larger behavior change. Diff-in-means also **cancels nuisance directions common to both
sets** (shared "you are writing HTML" content subtracts out), isolating the concept. Hence: probe/LDA to
**locate** (T8.6), diff-in-means to **steer**. When $\Sigma\approx I$ they coincide and the choice is
moot; we report $\cos(\hat v_\ell,\text{PC1 of paired diffs})$ and $\cos(\hat v_\ell,\text{probe-}w)$ as
diagnostics (PLAN S2.2).

**The mean-over-response-tokens estimator, and its bias.** $\bar h_\ell$ estimates the **generation-time
shift averaged over token positions and content**:
$\mathbb E_{t\in R}[\,h_\ell(t)\mid \text{FULL}]-\mathbb E_{t\in R}[\,h_\ell(t)\mid\text{NEUTRAL}]$. It is a
**biased** estimate of the shift at any *specific* position when the true shift is
**position-dependent** — e.g. if the design commitment concentrates at the tokens where the model emits a
color hex or a `font-family`, averaging over all response tokens **dilutes** a localized shift and
**conflates** committing-positions with filler positions. This is precisely why we also extract a
**first-$k$ ($k=64$)** variant (early-commitment) and a **last-prompt-token** variant, and why S2.9 tests
early-only steering (PLAN S2.2/S2.9). The mean statistic is the robust default (averaging reduces
variance); the variants probe the bias.

### T8.3 Activation addition (the steering operator)

Steering adds the unit direction at layer $\ell$, **all generated positions** (`rimsky2024caa`):

$$
h_\ell \leftarrow h_\ell + \alpha\,\hat v_\ell,\qquad
\boxed{\,\alpha=\rho\cdot\overline{\lVert h_\ell\rVert}\,}\ \ (\text{norm-relative; }\rho\text{ the primary axis}).
\tag{T8.4}
$$

> PAPER-EQ (candidate): T8.4 — the steering intervention and the norm-relative parameterization that
> makes the coefficient transfer across layers (PLAN S2.3).

**Units argument (why norm-relative $\rho$ transfers, absolute $m\lVert v_\ell\rVert$ does not).** The
residual-stream norm $\overline{\lVert h_\ell\rVert}$ grows systematically with depth (pre-norm models
accumulate writes). An **absolute** coefficient tied to $\lVert v_\ell\rVert$ injects a perturbation whose
*relative* size $\alpha/\lVert h_\ell\rVert$ varies wildly across layers, so a value tuned at layer 13 is
too weak at layer 20 and too strong at layer 8. Parameterizing $\alpha=\rho\cdot\overline{\lVert h_\ell\rVert}$
makes the injection a **fixed fraction of the ambient norm**, so $\rho$ is dimensionless and comparable
across layers/positions (`12_steering_variants_survey`; consistent with `chen2025persona`,
`konen2024style`). We sweep both (report absolute $m\in\{1,2,4,8,16\}$ and $\rho\in\{0.05,\dots,1.0\}$)
but $\rho$ is the axis we freeze on ($\rho^\*$).

**First-order effect on the next-token distribution (state with care).** Adding $\alpha\hat v_\ell$ at
layer $\ell$ perturbs the final residual and hence the logits. To first order,

$$
\Delta\text{logits}\approx \alpha\,W_U\,J_{\ell\to L}\,\hat v_\ell,\qquad J_{\ell\to L}=\frac{\partial\,\mathrm{LN}(h^L)}{\partial h^\ell},
\tag{T8.5}
$$

where $J_{\ell\to L}$ is the Jacobian of the rest of the network (a product of per-layer Jacobians) and
$W_U$ the unembedding. In the crude **identity-path heuristic** (treat the residual highway as
$J\approx I$ and freeze LayerNorm gain), $\Delta\text{logits}\approx\alpha\,W_U\hat v_\ell$ — useful for
intuition (the direction's "logit shadow"). **Caveats we do not hide:** LayerNorm is nonlinear (it
renormalizes $h+\alpha\hat v$, so the effect is *not* linear in $\alpha$), attention mixes positions, and
downstream MLPs are nonlinear; (T8.5) is a heuristic, not an identity.

**Non-monotonicity in $\alpha$.** Behavior is **not** monotone in the coefficient: as $\alpha$ grows,
$h_\ell+\alpha\hat v_\ell$ leaves the training manifold, LayerNorm's renormalization and downstream
nonlinearities respond non-monotonically, and coherence eventually collapses (`taimeskhanov2026strength`).
Hence a **sweep with a guardrail**, not a fixed large $\alpha$; expect a sweet spot then degradation
(PLAN S2.3; F7 dose-response).

**The KL guardrail.** On a fixed 512-token eval text, cap the mean per-token divergence of the steered
next-token distribution from the unsteered one:

$$
D_{\mathrm{KL}}\!\big(p_{\text{steered}}\,\|\,p_{\text{unsteered}}\big)=\sum_{w\in V}p_{\text{steered}}(w)\log\frac{p_{\text{steered}}(w)}{p_{\text{unsteered}}(w)}\ \le\ 0.30\ \text{nats}.
\tag{T8.6}
$$

> PAPER-EQ (candidate): T8.6 — the coherence guardrail that stops "winning by gibberish"; the operating
> constraint the freeze is subject to (PREREG §7).

KL is the natural **off-distribution alarm**: it measures how much steering has overwritten the model's
own predictions; large KL means the direction is coherent-breaking regardless of any metric gain. **The
$0.30$-nat threshold is a preregistered operating constraint, not a derived optimum** — we say so plainly.
It was chosen to admit a visible design shift while excluding runs where the model's distribution is
grossly rewritten; the freeze selects $(\ell^\*,\rho^\*,\text{variant}^\*)=\arg\max$ dev POC-gain **subject
to** (T8.6) and steered render-success $\ge0.90$ (PREREG §7).

### T8.4 Directional ablation and weight orthogonalization

To **remove** the direction everywhere (the necessity flip test), project it out of the stream:

$$
h\leftarrow h-\hat v\hat v^\top h = P h,\qquad \boxed{\,P=I-\hat v\hat v^\top\,}.
\tag{T8.7}
$$

> PAPER-EQ (candidate): T8.7 — the ablation operator; the second causal arm (necessity) and the flip
> test's mechanism.

**$P$ is an orthogonal projector.** *Idempotent:*
$P^2=(I-\hat v\hat v^\top)(I-\hat v\hat v^\top)=I-2\hat v\hat v^\top+\hat v(\hat v^\top\hat v)\hat v^\top
=I-2\hat v\hat v^\top+\hat v\hat v^\top=I-\hat v\hat v^\top=P$ (using $\hat v^\top\hat v=1$). *Symmetric:*
$P^\top=(I-\hat v\hat v^\top)^\top=I-\hat v\hat v^\top=P$. So $P$ is the orthogonal projector onto the
hyperplane $\hat v^\perp$; it kills exactly the component of any vector along $\hat v$ and leaves the
$d-1$ orthogonal directions untouched.

**Runtime projection ≡ baking into the weights (proof, and the caveat).** Every additive write to the
residual stream is $W_{\text{out}}\,g$ for some source $g$ (attention $W_O$ on the head output, MLP
$W_{\text{down}}$ on the hidden, the embedding on the token). Suppose we replace **every**
residual-writing matrix *at and after* the ablation point by $W_{\text{out}}\leftarrow P\,W_{\text{out}}$.
Then each write becomes $P W_{\text{out}}g=P(W_{\text{out}}g)$, and if the stream entering the edited
region already lies in $\operatorname{im}(P)$ (i.e. its $\hat v$-component is zero), the running sum stays
in $\operatorname{im}(P)$:

$$
h=\sum_k P(W_k g_k)=P\Big(\sum_k W_k g_k\Big)=P\,h_{\text{unprojected}} ,
\tag{T8.8}
$$

so reading $\mathrm{LN}(h)$ sees the projected state — identical to applying $P$ after every write at
runtime. Hence the bake-in and the hook are equivalent for all components written **after** the edit, and
the bake-in needs **no inference-time hook** (a "static" ablated model; `arditi2024refusal`). **Caveat:**
components written **before** the edit layer (and the token embedding) are not projected unless we also
orthogonalize them; to make ablation truly global, Arditi projects **all** residual-writing matrices
including the embedding. We follow that for the flip test (project $\hat v$ out at every layer and
position). "Ablation everywhere" thus means: remove the $\hat v$-component of **every** write into the
stream, so no site can re-introduce the direction — the cleanest interventional test of necessity.

### T8.5 Probing and control tasks

To **locate** the signal (RQ5), fit a **linear logistic probe** on mean-response residuals to classify
FULL vs NEUTRAL, per layer, with **5-fold CV split by prompt** (never leak a prompt across folds; PLAN
S2.1). Report per-layer **AUC**. Decodability alone is weak evidence (a probe can *memorize*
`hewitt2019control`), so we require **selectivity**:

$$
\text{Selectivity}_\ell=\mathrm{AUC}^{\text{real}}_\ell-\mathrm{AUC}^{\text{control}}_\ell ,
\tag{T8.9}
$$

where the **control task** assigns each prompt a **random-but-fixed** label (shuffled within prompt
strata), preserving structure while destroying the real skill/neutral signal. A trustworthy probe has
high real AUC and **low** control AUC (high selectivity); a probe that scores high on both is memorizing
prompt identity. Linear (not MLP) probes are used precisely because they are far more selective
(`hewitt2019control`).

**Probe accuracy $\neq$ causal relevance.** A direction can be linearly **decodable** without being
**used** by the model downstream (`alain2017probes`). This correlational-vs-causal gap is the reason
Stage 2 cannot stop at probing: RQ5 (probing/patching) only **localizes candidate layers**; RQ6
(steering) and the flip test (RQ, ablation) are what establish the model **uses** the direction
(`zhang2024patching`, `hewitt2019control`). The decision rule (PLAN RQ5) pairs AUC $\ge0.80$ **with**
selectivity $\ge0.15$ **and** patching $\ge25\%$ (below) so no single correlational signal decides the
band.

### T8.6 Activation patching (localization by intervention)

Patching swaps activations between a **clean** (skill-present) and **corrupted** (length-matched neutral)
run to see where the behavior is carried (`zhang2024patching`, `heimersheim2024patching`). Two directions:

- **Denoising** (our choice): run on the **neutral** prompt, **patch in the skill-side** activation at
  site $(\ell,\text{position})$, ask if the design behavior is **restored**. Answers *"is this site
  **sufficient**?"* Denoising is robust to **self-repair/backup** (the hydra effect, where ablating one
  component lets others compensate and a necessary site looks unnecessary), which contaminates the
  noising direction.
- **Noising**: clean run, patch in corrupted activation, ask if behavior **breaks** (necessity) — more
  self-repair-prone, so secondary.

**Metric for long generations (the probe-projection / logit-diff proxy).** There is no single "answer
token" in a 3k-token HTML generation, so we cannot use a clean logit-diff on a target token directly.
Two proxies (PLAN S2.1c), both stated with their assumptions:

1. **Design-token logit-difference.** At the first response position where the model **commits to a style
   token**, compute $\Delta=\text{logit}(t^{+})-\text{logit}(t^{-})$ with $t^{+}$ a **non-default** choice
   (a non-`Inter` `font-family` token, a non-purple hex digit) and $t^{-}$ the default. Logit-diff is
   preferred over probability/accuracy (smoother, less saturation-prone; `zhang2024patching`). *Assumption:*
   a small set of identifiable "commitment tokens" carries the design decision — reasonable for
   font/color, weaker for diffuse layout choices.
2. **Probe-projection proxy.** Project the **patched-run** downstream activations onto $\hat v_\ell$ and
   measure how far the projection moves toward the clean value. *Assumption:* the probe direction is a
   faithful readout of the behavior at downstream layers (cross-checked against steering, §T8.5).

Both report **% of the clean–corrupted gap recovered**,
$\%\text{rec}=\frac{m_{\text{patched}}-m_{\text{corrupt}}}{m_{\text{clean}}-m_{\text{corrupt}}}\times100\%$.
Full-generation patching (re-decode the entire page under every site's patch and re-score POC) is
$O(\text{sites}\times\text{tokens})$ forward passes — infeasible at our scale — hence the **first-commitment /
projection** proxies, which localize *where the skill first bends the trajectory* rather than recovering a
crisp circuit. **Interpretability-illusion caveat** (`heimersheim2024patching`, Makelov–Lange–Nanda): a
subspace patch can move behavior via a **dormant parallel pathway** rather than the studied feature, so a
patching result alone is not proof; we **corroborate** with steering + probing (the triangulation the RQ5
decision rule enforces).

**Used in:** PLAN §IV S2.0–S2.5, RQ5/RQ6; ADR-002; `src/hooks`, `src/activations`, `src/steering`,
`src/probes`; F5, F13. Feeds T9 (SAE contrast) and T10 (the causal framing).

---

## T9 — Interpretability II: the causal test as `do`-calculus (what is and is not established)

### T9.1 Interventions as `do`-operators

Steering and ablation are **interventions** on an activation node of the generating process, in Pearl's
sense: they **set** the node, severing its normal dependence on upstream computation. Write $Q$ for the
UI-quality outcome (POC or a preference utility, T7). The two arms:

$$
\textbf{Sufficiency (RQ6):}\quad \mathbb E\big[Q\mid \mathrm{do}(h_{\ell^\*}\!\mathrel{+}=\alpha^\*\hat v_{\ell^\*}),\ \text{NOSYS}\big]\ >\ \mathbb E\big[Q\mid \text{NOSYS}\big],
\tag{T9.1}
$$

$$
\textbf{Necessity (flip):}\quad \mathbb E\big[Q\mid \mathrm{do}(h\leftarrow P h),\ \text{FULL}\big]\ <\ \mathbb E\big[Q\mid \text{FULL}\big].
\tag{T9.2}
$$

> PAPER-EQ (candidate): T9.1 + T9.2 — the causal statements the paper's headline rests on: with **no
> design prompt**, forcing the direction raises quality (sufficiency); with the skill present, removing
> the direction lowers it (necessity). "Steer with no prompt" = NOSYS is what makes these interventional,
> not observational.

The intervention is **on-activation**, so the comparison isolates the direction's effect from the
prompt's — the whole point of "steer with no design prompt." Sufficiency uses the NOSYS base (no
instruction to confound); necessity uses FULL (the skill in context) and asks whether the direction is
load-bearing.

### T9.2 The controls, as threats-and-fixes

Each internal-validity threat and the control that neutralizes it (PLAN §IV, VIII.1; PREREG §7):

| threat | why it fakes an effect | control |
|---|---|---|
| **Norm confound** | *any* large perturbation might jog quality | **norm-matched random vector**, $k=5$ draws re-normalized to $\lVert v_{\ell^\*}\rVert$, same injection; must **not** reproduce the gain (T9.3) |
| **Non-identifiability / cones** (`wollschlager2025cones`, arXiv:2602.06801) | many behaviorally-equivalent vectors exist under single-layer access | claim **"a** causally sufficient direction," never **"the** direction"; report the cosine/cone structure (RQ8) |
| **Self-repair** (patching) | necessity underestimated under noising | **denoising** patching (T8.6) |
| **Interpretability illusion** (`heimersheim2024patching`) | subspace intervention acts via dormant pathway | triangulate steering + probing + patching (RQ5 rule) |
| **Spurious extraction cues** (`tan2024analysing`) | direction rides features correlated with skill in the extraction set | **held-out** verification incl. **unseen task types**; pre-screen by class separation |
| **Selection leakage** | tuning the operating point on test data | freeze $(\ell^\*,\rho^\*,\text{variant}^\*)$ on **dev**, git-tag `steer-frozen`, touch held-out **once** |
| **Engine confound** (ADR-002) | vLLM vs HF numeric mismatch | **within-HF** comparisons only; re-generate any baseline in HF |

The **specificity** requirement is the random control formalized:

$$
\mathbb E\big[Q\mid \mathrm{do}(h_{\ell^\*}\!\mathrel{+}=\alpha^\*\hat r),\ \text{NOSYS}\big]\ \not>\ \mathbb E\big[Q\mid\text{NOSYS}\big]\quad\text{for random }\hat r,\ \lVert\alpha^\*\hat r\rVert=\lVert\alpha^\*\hat v_{\ell^\*}\rVert,
\tag{T9.3}
$$

for $k=5$ independent $\hat r$ — if a random direction of **equal norm** also lifts $Q$, the effect is a
**norm** effect, not a **direction** effect, and we downgrade the claim (PLAN S2.4).

### T9.3 What can and cannot be concluded

- **Established if all four checks pass** (the AND of T6.4): a **causally sufficient** (T9.1) and, if the
  flip attenuates (T9.2), **causally necessary** design direction exists — the first such result for
  UI-code aesthetic quality (novelty, `12_steering_variants_survey`). If addition succeeds but the flip
  does not, we report **"sufficient, not demonstrably necessary"** (the direction is one carrier among a
  possible cone; `wollschlager2025cones`).
- **Not established, by construction:** that $\hat v_{\ell^\*}$ is **the unique** design direction
  (non-identifiability), nor that design is one-dimensional (RQ8 tests near-orthogonality of component
  sub-vectors; `engels2024notlinear` keeps a multi-dim null on the table).
- **Generalization adds transportability.** A causal effect that holds on the **unseen task types**
  (settings-panel ST, admin-table AT — absent from dev) is evidence the direction encodes design
  **content** that **transports OOD**, not an in-distribution artifact of the extraction corpus
  (`tan2024analysing`). We still report the **anti-steerable fraction** and dose-response non-monotonicity
  (RQ7) — a positive *mean* OOD effect can hide heavy-tailed per-prompt behavior, so the distribution, not
  the mean, is the claim.

### T9.4 The correspondence test (RQ8) and what cosine can/cannot show

Component sub-vectors $v_{C_i}=\bar h_{\ell^\*}^{(\text{AOI-}C_i)}-\bar h_{\ell^\*}^{(\text{NEUTRAL})}$
(diff-in-means of "only $C_i$" vs neutral). **Geometry:** the cosine matrix among $\{v_{C_1},\dots,v_{C_5}\}$
and with $\hat v_{\text{full}}$. Near-orthogonality — mean $|\cos(v_{C_i},v_{C_j})|<0.3$ — is **evidence
for a component basis** (distinct sub-concepts as roughly orthogonal directions, predicted by
`park2024geometry`) rather than one entangled direction. **What cosine can establish:** that the
sub-vectors are *linearly distinguishable* (a necessary condition for a basis). **What it cannot:** that
each sub-vector *causally* steers its own metric family — orthogonality of directions does **not** imply
independence under intervention (`wollschlager2025cones`). Hence RQ8's decision rule pairs the cosine
criterion **with** a **steering signature match** (each $\hat v_{C_i}$, added, must move *its* objective
family most; PLAN S2.8) — the causal half that cosine cannot supply. "Found" requires **both**
($|\cos|<0.3$ **and** $\ge3/5$ signatures match).

**Used in:** PLAN §IV S2.4–S2.9, RQ6/RQ7/RQ8; PREREG §7; ADR-002; F8, F9, F12. Consumes T7 ($Q$), T8
(direction, operators), T6 (the AND error bound).

---

## T10 — The SAE objective (stretch, honestly demoted)

Sparse autoencoders (SAEs) are the alternative route to a **monosemantic** "clean-design feature." We
demoted them to a labeled stretch (ADR-008); here is the objective and the honest reasons.

**Objective.** An SAE learns an overcomplete dictionary $D=[d_1,\dots,d_m]$ ($m\gg d$) and encoder $f$ so
that a residual activation $x$ is reconstructed from a **sparse** code $f(x)$:

$$
\mathcal L=\underbrace{\lVert x-\hat x\rVert_2^2}_{\text{reconstruction}}+\lambda\underbrace{\lVert f(x)\rVert_1}_{\text{sparsity}},\qquad \hat x=D f(x)=\sum_i f_i(x)\,d_i .
\tag{T10.1}
$$

This is **dictionary learning**: features are the dictionary atoms $d_i$; a monosemantic design feature
would be one atom whose activation tracks "clean design," steerable by clamping $f_i$. Variants (one line
each): **TopK** — replace the $\ell_1$ penalty by keeping the $K$ largest codes (hard sparsity, no
$\lambda$ tuning); **JumpReLU** — a learned per-feature threshold $\theta_i$ with a Heaviside jump so
small activations are gated to zero (better sparsity/fidelity trade-off).

**Why demoted (evidence, not preference).**
- **No suite for our model.** There is **no public SAE suite for Qwen2.5-Coder** (`deng2026qwenscope` —
  Qwen-Scope covers Qwen3/3.5); training one on Colab is out of scope.
- **DiffMean $\ge$ SAE for steering.** On the largest head-to-head benchmark, **difference-in-means beats
  SAE steering** and matches/leads on concept detection (`wu2025axbench`); SAEs are "not competitive" by
  default (the rebuttals `arad2025saesteering`/Jørgensen–Hansen show this is really "naive SAE feature-
  picking loses," which does not help us without a suite).
- **Steering-vector decompositions are unfaithful.** Decomposing a steering vector into SAE features can
  be **unfaithful** to the vector's actual effect (`mayne2024decompose`), so an SAE view would not even
  reliably *explain* our diff-in-means direction.

Consequently the SAE route, if ever pursued, is a clearly-labeled **cross-model transfer demo**
(e.g. Llama-Scope on the recorded fallback), off the critical path — never the primary evidence.

**Used in:** ADR-008; PLAN Part IV (stretch framing), §11 SAE-line survey. Contrasts with T8 (the
adopted diff-in-means route).

---

## PAPER-EQ index (candidates for the two-part paper)

The equations most likely to surface in the paper, id → one-line reason. **14 headline entries** (some
bundling a two-display pair, e.g. T4.2+T4.5, T6.3+T6.4, T9.1+T9.2); final selection at write-up.

1. **T1.7** — necessity $=2\beta_i+2\sum\beta_{ij}$, sufficiency $=2\beta_i-2\sum\beta_{ij}$: unifies
   RQ1/RQ2/RQ3 and predicts the necessity>sufficiency asymmetry.
2. **T3.1** — the MixedLM $y_{cps}=\mu+\tau_c+u_p+v_{cp}+\epsilon$: the inference model behind every
   objective delta.
3. **T3.4** — $n_{\text{eff}}=n/(1+(m-1)\rho_{\mathrm{ICC}})$: the pseudoreplication deflation; why 200
   generations are not 200 independent points.
4. **T4.2 + T4.5** — $\alpha_K=1-D_o/D_e$ vs AC1's $p_e^\gamma$: the two chance models that justify the
   disjunctive reliability gate (kappa paradox).
5. **T5.4** — style-controlled BT $P(i\succ j)=\sigma((\beta_i-\beta_j)+\gamma^\top(s_i-s_j))$: the
   preference endpoint with judge-bias control.
6. **T6.2** — McNemar/one-sample sizing reproducing 200/80/780: the judgment-budget justification.
7. **T6.3 + T6.4** — two-signal rule as error algebra: OR raises power (necessity/sufficiency screen),
   AND crushes false positives (the Stage-2 causal headline).
8. **T7.2** — WCAG contrast ratio $\mathrm{CR}=(L_1+0.05)/(L_2+0.05)$: the archetypal deterministic
   accessibility endpoint.
9. **T7.10** — the POC as a 7-term oriented z-score composite: the primary objective scalar.
10. **T8.2** — diff-in-means $v_\ell=\bar h_\ell^{(\text{FULL})}-\bar h_\ell^{(\text{NEUTRAL})}$: the
    extracted design direction.
11. **T8.3** — $w^\*=\Sigma^{-1}(\mu_1-\mu_0)$ vs diff-in-means: why we steer with the un-whitened vector.
12. **T8.4** — activation addition $h_\ell\leftarrow h_\ell+\alpha\hat v_\ell$, $\alpha=\rho\overline{\lVert h_\ell\rVert}$: the steering operator + norm-relative transfer.
13. **T8.7** — the ablation projector $P=I-\hat v\hat v^\top$ (idempotent, symmetric) + weight-orth
    equivalence: the necessity arm.
14. **T9.1 + T9.2** — the `do`-operator sufficiency/necessity statements: the causal claims the paper's
    Part 2 rests on. **(T8.6** — the KL guardrail — is the strongest supporting-constraint equation.)

---

*End of THEORY.md. Notation is verified against PLAN Part VII; decision rules are those frozen in
PREREGISTRATION.md. Where a value is convention rather than a derived optimum (the KL 0.30-nat threshold,
the agreement gates, the multiplicity levels), the text says so explicitly.*
