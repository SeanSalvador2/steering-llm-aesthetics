# SEAN-README.md — the plain-language companion to Project 19

*Anatomy of a Design Skill: which words in a design prompt do the work, and where that work happens
inside the model.*

Sean — this file explains **every** part of this project in plain language, at three levels:

- **Conceptual** — what a thing is and why it's here, before any jargon.
- **Technical** — the same thing in the real vocabulary (the terms you'd use in the paper or an
  interview), each introduced only after the intuition.
- **Code-level** — where it lives in this repo and what actually runs.

The goal is not that you can recite this project. It is that you can **defend** every decision — to
a skeptical interviewer, to a Yale faculty member, to a reviewer. Understanding is a first-class
deliverable here, on the same footing as the code and the paper. Every technical term is introduced
with intuition first; every "why" is answered; and every section ends with a **"where this lives"**
pointer into the repo so you can go read the primary source.

A note on how to use it: read Sections 1–5 for the ideas, Section 6 for the map of the repo, Section
7 to test yourself, and Section 8 for the honest risk picture and what *you* personally should
re-derive to own this. All file paths are absolute.

**One-screen orientation.** One open-weights model (`Qwen/Qwen2.5-Coder-7B-Instruct`) used for both
stages. Stage 1 is a **24-cell** factorial ablation over **58 prompts** producing **4,630**
generations. Stage 2 extracts a steering vector from **200 matched activation pairs**, sweeps and
freezes an operating point, then does a one-shot causal test on held-out prompts. The design skill
is **391 tokens** in five components; the interpretability focus is a mid-network **layer band
11–20** of 28. Judging costs **~$14**, compute **~$50–65**, total **~$65–80**. **137 tests** already
pass on CPU; the GPU half is written, tested against mocks and synthetic data, and left unexecuted
for Colab.

---

## 1. The story in one page

**The mystery.** If you ask a code LLM to "build me a landing page," you tend to get the same tired
thing: a purple-to-indigo gradient hero, one giant centered headline with a big number under it,
three identical icon cards in a row, everything in the Inter font with uniformly rounded corners.
The community calls this **"purple slop"** — the default aesthetic an LLM reaches for when nobody
steers it. People discovered that pasting in a few hundred tokens of "frontend-design guidance" (a
**design skill**) dramatically improves the output. Everyone *reports* this. **Nobody has measured
it.** Two questions are wide open:

1. *Which words carry the weight?* The skill is a bundle — color rules, layout rules, typography
   rules, component patterns, and a list of "don't do this." Is it the color advice? The "avoid
   purple gradients" list? All of them together? Nobody knows which pieces are load-bearing.
2. *Where does the guidance act inside the model?* When those tokens change the output, something
   changes in the model's internal computation. Is there a "clean-design" signal you could point to
   — and could you reproduce the improvement by nudging that internal signal **directly, with no
   design prompt at all**?

**What the two stages deliver.**

- **Stage 1 (black-box ablation).** Treat the skill like a drug with five active ingredients.
  Systematically remove ingredients (and combinations of them), regenerate UIs, and measure the
  causal effect of each on quality. Deliverable: a ranked, quantified decomposition — which design
  instructions matter, by how much, and whether they add up independently or interact. This stands
  alone as a complete result.
- **Stage 2 (white-box interpretability).** Open the model up. Find where in its activations the
  skill's effect lives, extract a **steering vector** (a single direction in the model's internal
  number-space that represents "turn on clean design"), and **causally verify** it: inject that
  direction at inference with **no design prompt** and see whether UI quality improves on prompts —
  and even task types — the model never saw during extraction. This is the scarce, differentiated
  contribution: activation-level interpretability has never been pointed at the visual quality of
  generated UI code.

**The possible endings.** Every research question has a preregistered honest-null branch. The
headline endings for Stage 2:

- **Branch A — a causal design direction exists.** Steering with no prompt reproduces a measurable
  chunk of the skill's quality gain on held-out prompts, a random push of equal size does not, and
  (best case) removing the direction disables the skill even when its 391 tokens are present. This
  is the strong result.
- **Branch B — the honest null.** No single direction steers quality under the coherence guardrail,
  even though a probe can *read* the skill/no-skill distinction cleanly. That means we found a
  direction that **correlates** with design but does not **cause** it when injected — a hypothesis,
  not a finding, reported as such.
- **Branch C — partial outcomes.** It steers the objective metrics but not human preference; or it
  only "works" by breaking coherence; or it helps half the prompts and harms the other half; or it's
  sufficient but not necessary.

**Why the null is still a win.** The whole project is built to make its own measurements
trustworthy, which means it must be equally willing to report "the effect is real" and "the effect
is not there." A **tight** null — one where the confidence interval is narrow enough to *exclude*
the effect the study was designed to detect — is a genuine scientific result: it rules out the
strongest form of the "single steerable direction" story for aesthetic behavior in this model, which
is a real datapoint for the interpretability literature. A forced or buried null would corrupt
exactly the credibility the project exists to defend. So the null is published with the same rigor
as a positive result.

**Where this lives.** `docs/BRIEF.md` (the original mandate), `CLAUDE.md` (the governance that locks
the model and the oracle), `PLAN.md` §0.1 (the one-paragraph statement), and
`paper/sections/stage2_results.tex` (the full, written-out A/B/C branches, one of which gets kept on
real data).

---

## 2. Stage 1 explained — the ablation

### 2.1 Why ablation *is* causation here

You already know the cleanest way to establish that X causes Y is to intervene on X and watch Y,
holding everything else fixed. That is exactly what an **ablation** does: you take the full skill,
remove one component (or a designed combination of components), regenerate the UIs, and measure the
change in quality. Because the prompt is the only thing that changed — same model, same task briefs,
same sampling settings, same seeds — a change in output quality is *caused* by that component. This
is a randomized intervention on the instruction, not an observational correlation. The word
"ablation" is borrowed from experimental biology (lesion a part, see what breaks); in ML it means
removing a piece of the input or architecture to measure its contribution.

The subtlety, and the thing that makes Stage 1 more than a pile of A/B tests, is that "remove one
component" can mean two genuinely different questions, and the design asks both (Section 2.4).

### 2.2 The five components — and why the negatives got their own component

The skill is deliberately written as five **content-orthogonal** components
(`research/skill_exemplars/canonical_skill_v1.md`):

- **C1 — Color / palette:** choose a deliberate 4–6 color palette, build depth with layered
  backgrounds, clear WCAG AA contrast. *(75 tokens)*
- **C2 — Layout / spacing / hierarchy:** lead with the characteristic element, consistent spacing
  scale, align to shared edges, generous white space. *(73 tokens)*
- **C3 — Typography:** pair a display face with a readable body face and a utility face, set a
  modular type scale, give type personality. *(75 tokens)*
- **C4 — Component patterns:** one signature element, at most one orchestrated motion moment, vary
  radii/borders/shadows with intent. *(80 tokens)*
- **C5 — Negative constraints:** avoid purple/indigo gradients, Inter/Roboto, centered
  hero-with-a-big-number, three identical icon cards, uniform rounded corners, scattered animation,
  generic template palettes. *(88 tokens)*

"**Content-orthogonal**" means each component talks about exactly one topic, and the topics don't
overlap. This is not cosmetic — it's what makes the ablation interpretable, and it took a real
design decision (ADR-009) to get right.

**The C1-contamination story.** A first draft of the skill wrote it the way real published skills
write it: negatives sprinkled inside every component — "no purple gradients" tucked into the color
section, "not a centered hero" inside the layout section, "don't default to Inter" inside the
typography section. That feels natural, but it wrecks the experiment. If "no purple gradients" lives
inside C1, then when you ablate C5 you have **not** removed all the negative guidance — some of it
is still hiding in C1. And when you ablate C1, you've removed both a color instruction *and* a
negative instruction, so you can't attribute the effect to "color" as distinct content. Component
effects stop being attributable to distinct topics. ADR-009's fix: **C1–C4 are purely prescriptive**
(they only say what to do), and **all** negatives are consolidated in **C5**. Now ablating C5
removes exactly "the list of don'ts," ablating C1 removes exactly "the color advice," and each
component's measured effect means one clean thing. (A "realistic mixed" variant with interleaved
negatives is kept as an optional robustness cell, not the primary design.)

**Why this matters for the whole paper.** The community's own theory is that the skill's
negative-constraint core is the heavy hitter — "avoid the slop defaults" is emphasized as very
important. The preregistered prior is that **C5 (negatives) and C1 (color)** will punch above their
token weight. If negatives were smeared across components you could never test that cleanly.

**Where this lives.** `docs/DECISIONS.md` ADR-009 (the decision),
`research/skill_exemplars/canonical_skill_v1.md` (the frozen text), `src/p19/skill_assembly.py`
(assembles system prompts from components and asserts the content rules), `PLAN.md` §II.1.1.

### 2.3 The four control cells — and what each one catches

A comparison is only as good as its baseline. Stage 1 has **four** control cells, because "the full
skill" needs to be compared against several different "off" states, each of which rules out a
different alternative explanation:

- **FULL** — the intact five-component skill. The treatment.
- **NEUTRAL** — the same *length* of design-irrelevant filler text. This is the flagship control
  (see below).
- **BEAUTY1** — a five-word nudge: *"Make it beautiful and well-designed."* (~8 tokens).
- **NOSYS** — no system prompt at all. The bare baseline, and the "no design prompt" base that Stage
  2 steers from.

**Why NEUTRAL is length-matched filler and not an empty prompt — the prompt-mass confound.** This is
the single most important design choice in Stage 1, and it's worth being able to defend cold. If you
compared FULL (391 tokens of design guidance) against NOSYS (nothing), and quality went up, you
would not know *why*. Maybe the design content helped. But maybe **any** long, imperative
instruction block would help — a big system prompt changes the model's attention patterns, makes it
more verbose, makes it more compliant and careful, independent of *what the block says*. That
confound — "the mere presence of a long instruction" versus "the design content of the instruction"
— is the **prompt-mass confound**. To break it, NEUTRAL is a block of exactly matched length and
imperativeness that is deliberately about something else entirely (source-code hygiene: indentation,
comments, naming). FULL vs NEUTRAL therefore isolates **design content**, because prompt mass is
held constant. (NOSYS is still run, so you can *also* measure the prompt-mass effect directly:
NEUTRAL − NOSYS.) This is why the frozen headline hypothesis is "FULL ≻ NEUTRAL," not "FULL ≻
nothing." It is also why Stage 2's steering vector is extracted from the FULL-vs-NEUTRAL contrast —
so the direction encodes *design content*, not *instruction-following mode*.

**The render-inertness episode — how our own control almost biased the metrics, and how it was
caught.** Here is a genuinely subtle trap, and the story of catching it is a good interview answer
about experimental rigor. The objective metrics are computed on the **rendered** page (Section 3).
Some of those metrics reward things like semantic HTML landmarks (`<header>`, `<nav>`, `<main>`), a
`lang` attribute, a `<title>`, and well-formed tag closure — these are visible to the accessibility
checker (axe-core) and to the render-success gate. The first sketch of the NEUTRAL filler described
it as "code-hygiene instructions," and code hygiene *naturally* includes "use semantic HTML5
landmarks and set the page language." But if the neutral control tells the model to do those things,
then NEUTRAL pages would score *better* on accessibility and validity — and the control would be
**moving the very metrics it exists to hold constant**. That would inflate the baseline and make the
real components look *less* necessary than they are. It was caught in plan review. The fix (now
binding): fillers must be **render-inert** — they may only mandate things that leave the rendered
DOM byte-for-byte unaffected (source formatting, comment style, class-naming conventions, CSS
declaration ordering, JS source organization) and may **not** touch semantic elements,
`lang`/`title`/`meta`, ARIA, tag closure, or event handlers. This is enforced by a build-time
**filler audit**: a hard unit test that greps every filler against a banned-topic term list and
fails the build on any whole-word match. So the "neutral" control is provably neutral with respect
to the oracle.

**Where this lives.** `docs/DECISIONS.md` ADR-003 (the length-matched control and its
render-inertness refinement), `research/skill_exemplars/canonical_skill_v1.md` §3 (the filler texts
and the inertness rule), `config/skill.yaml` (`filler_banned_topics`), `src/p19/skill_assembly.py`
(the audit) and `tests/test_skill_assembly.py` (22 tests enforcing it), `PLAN.md` §II.1.3.

### 2.4 The factorial — necessity, sufficiency, and what a half-fraction buys

Five components, each either on (+) or off (−), gives 2⁵ = 32 possible combinations. Multiply by 58
prompts and up to 5 seeds and you have far too many generations, most of which answer no specific
question. The design (ADR-004) is smarter than "run everything," and it rests on three ideas you
should be able to explain.

**Leave-one-out (LOO) = necessity.** Take the full skill and remove exactly one component (replacing
it with its matched filler so length stays constant). FULL − LOO-Cᵢ answers: *does removing Cᵢ
hurt?* That's **necessity** — is the component load-bearing when everything else is present.

**Add-one-in (AOI) = sufficiency.** Start from all-filler NEUTRAL and turn on exactly one component.
AOI-Cᵢ − NEUTRAL answers: *does Cᵢ alone help?* That's **sufficiency** — can the component carry
quality by itself.

These are **not the same question**, and the reason is interactions. Here's the identity that ties
it all together, translated from THEORY §T1.4. Writing the response as a sum of a main effect for
each component (2βᵢ) plus pairwise interaction terms (2βᵢⱼ for each pair), the algebra gives:

- Necessity of Cᵢ = 2βᵢ **+** 2·(sum of its interactions with the others) + higher-order remainder
- Sufficiency of Cᵢ = 2βᵢ **−** 2·(sum of its interactions with the others) + the *same* remainder

In English: **how much a component is worth depends on who else is in the room.** Necessity measures
its worth with all its partners present; sufficiency measures its worth alone. The sign on the
interaction sum flips between the two. Two consequences fall out immediately:

- Their **average** is the component's pure "solo" main effect, 2βᵢ (the interaction terms cancel).
- Their **half-difference** is the component's total teamwork load, the sum of its pairwise
  interactions (the main effect cancels).

So if components **synergize** (positive interactions — e.g., "avoid purple gradients" helps *more*
once a real palette has been specified), each component will look **more necessary than
sufficient**: they carry the skill *together*, and removing one hurts more than adding one alone
helps. If interactions are zero, necessity = sufficiency = main effect, and the skill is simply
additive. This single identity is why RQ1 (necessity), RQ2 (sufficiency), and RQ3 (interactions) are
three separate questions that only make sense together — and it makes a concrete prediction: because
negatives are expected to synergize with color, necessity of C5 should exceed its sufficiency.

**What the resolution-V half fraction buys (the LOO/AOI add-ons).** To measure the ten pairwise
interactions you seem to need many combinations. A **fractional factorial** design says: run a
cleverly chosen **half** of the 32 combinations (16 runs), picked by the rule "keep only the
combinations with an **even number of fillers**" (formally, the sign-product is +1, the "defining
relation" I = ABCDE). This particular half is a **resolution-V** design, and resolution V is exactly
the guarantee you want: **all five main effects and all ten pairwise interactions are cleanly
estimable from the 16 runs.** Each estimate is confounded ("aliased") only with three-way-or-higher
interactions, which we assume are negligible for five prescriptive design rules (a genuine three-way
color×layout×typography synergy, beyond all the pairwise ones, is a priori tiny). So you spend half
the runs and lose only the high-order synergy you were willing to assume away. Better still, of
those 16 runs, **6 coincide with cells you already need**: the all-on run *is* FULL, and the five
single-on runs *are* the AOI cells — so the fraction contributes only **10 new** three-component
"interaction" cells. Add the 5 LOO cells and NEUTRAL (which sit in the *other* half — they have an
odd number of fillers) plus BEAUTY1 and NOSYS, and the deduplicated design is exactly **24 distinct
cells**. That is the whole cell table.

Concretely: 4 controls + 5 LOO + 5 AOI + 10 interaction = **24 cells**. Necessity and sufficiency
come from direct paired contrasts (LOO and AOI vs their baselines); interactions come from a
factorial mixed model fit to the 16-run block.

**Where this lives.** `docs/DECISIONS.md` ADR-004, `PLAN.md` §III.1 (the full 24-cell table) and
§III.2 (the aliasing statement), `THEORY.md` §T1 (the identity derived) and §T2 (the full alias
table), `src/p19/mixedlm.py` (builds the factorial design matrix and asserts it's full rank 16),
`PREREGISTRATION.md` §3 (the frozen sign vectors).

### 2.5 Why 3–5 seeds, and what pseudoreplication is

The model samples at temperature 0.7, so the same prompt gives a different page each run. Each seed
is one draw from the model's distribution. You run multiple seeds because a single output is an
anecdote; you want the **distribution** of quality a cell produces, and its uncertainty. Headline
cells (the four controls, the 5 LOO, the 5 AOI) get **5 seeds**; the interaction cells get **3**.
(Greedy decoding at temperature 0 would be a mistake here — it collapses every seed to the *same*
output, destroying the very seed-to-seed variation the analysis needs.)

But here's the statistical trap you must be able to name: **pseudoreplication**. If a cell produces
5 seeds × 40 prompts = 200 pages, it is tempting to treat those as 200 independent data points. They
are not. Five seeds of the *same prompt* share that prompt's idiosyncrasies — some briefs are
intrinsically "designier" than others — so seeds within a prompt are **correlated**. Treating
correlated observations as independent understates your variance and inflates your test statistics:
you'd claim significance you haven't earned. The formal object is the **intraclass correlation**
ρ_ICC (how much of the total variance is shared within a prompt) and the resulting **design effect**
DEFF = 1 + (m−1)·ρ_ICC, which deflates your real sample size to an **effective sample size**:

> n_eff = n / (1 + (m−1)·ρ_ICC).

With m = 5 seeds and a modest ρ_ICC = 0.3, DEFF = 1 + 4(0.3) = 2.2, so 200 pages are worth about
**91 independent points**, not 200. The honest analysis (Section 5) uses a **mixed-effects model**
that puts a random effect on prompt (and on cell-within-prompt) and recovers this deflation
automatically. This is why you can't get away with per-generation t-tests, and why the bootstrap
resamples *whole prompts*, not individual pages.

**Where this lives.** `THEORY.md` §T3.2 (the DEFF/n_eff derivation), `PLAN.md` §II.3 (seed
allocation) and §III.6 (the mixed model), `src/p19/mixedlm.py`, `PREREGISTRATION.md` §3.

### 2.6 The token-equalization saga — preregistration discipline as the punchline

This is a small story with a big moral, and it's a great "tell me about a time you caught your own
mistake" answer.

The confound control in Section 2.3 only works if the cells are *actually* the same length. Early
on, component lengths were estimated the lazy way: words × 1.33 (a rule of thumb for how many
sub-word tokens a word becomes). That estimate said all five components were nicely balanced. Then
the exact `Qwen2.5-Coder` tokenizer was run for real, and two problems the estimate had masked
jumped out:

1. **C5 measured 104 tokens** — about 28% over the component mean, and outside the preregistered
   ±15% balance band. Why? **BPE** (byte-pair encoding, the sub-word tokenizer) fragments things the
   word-count estimate treats as single units: semicolon-separated lists and long hyphen chains. The
   phrase `cream-and-terracotta-serif` alone is **7 tokens**, not one word's worth. The negatives
   component was full of exactly this kind of text.
2. **The fillers ran ~10% lighter than their matched components**, so FULL (391 exact tokens) versus
   NEUTRAL (347 exact tokens) was an **11% mass gap** — not the length-match the flagship control
   promises.

Now the interesting part: **how you fix this reveals your discipline.** The easy fix is to widen the
±15% band so C5 fits. That would make the problem disappear. It would also be **weakening a
preregistered rule to accommodate a tokenization artifact** — precisely the kind of after-the-fact
rule-bending that preregistration exists to prevent. The chosen fix instead kept the rule and
changed the text:

- **C5 was reworded to 88 tokens** — back in band — preserving all eleven of its semantic
  constraints (all six slop tells, generic palettes, both named "looks," the escape clause, the
  cut-purposeless-decoration rule), just phrased so BPE doesn't fragment it (hyphen chains broken
  up; only the non-constraint adjective "overused" dropped). A dedicated test verifies every
  constraint survived.
- **The fillers are equalized at build time**, each padded or trimmed deterministically from a
  frozen, inertness-audited clause pool until it's within ±2 tokens of its component. A consequence
  test asserts every cell's system-prompt mass lands within ±10 tokens of FULL.
- **All nominal token counts everywhere were re-anchored to exact counts**, with the ×1.33 estimate
  kept only as the documented no-tokenizer fallback.

The punchline: this all happened **before** the preregistration was frozen (fixing the independent
variable's text is explicitly a pre-freeze activity), so it's sanctioned, not a deviation. The five
exact component counts — 75, 73, 75, 80, 88 — sum to exactly **391**, their mean is exactly
**78.2**, the ±15% band is [66.5, 89.9], and C5's 88 sits just inside it. Everything reconciles. The
moral you can state in an interview: *when your measuring rule and your data disagree, fix the
data-generating text, not the rule — otherwise the rule was never real.*

**Where this lives.** `docs/DECISIONS.md` ADR-010 (the whole saga),
`research/skill_exemplars/canonical_skill_v1.md` §2 (the token table and reword note), `PLAN.md`
§II.1.2, `src/p19/skill_assembly.py` (`equalize_fillers`, the ±15% assertion) and
`tests/test_skill_assembly.py`.

---

## 3. The measurement problem — the correctness oracle

### 3.1 Why "does it look better" is a swamp

Aesthetic quality is the kind of thing that feels obvious to a human and is treacherous to measure.
If you let yourself score UIs by eyeballing them, three things go wrong: you'll unconsciously favor
the condition you expect to win; "better" will mean different things on different days; and you'll
have no defense when a reviewer asks "how do you *know* the purple one is worse?" An entire
literature confirms the danger — objective aesthetic metrics explain **at most about half** the
variance in human appeal, and human raters are swayed by length, colorfulness, and which page they
saw first. The credibility of both stages rests entirely on measurement being real. So the project
makes measurement its constitution.

### 3.2 The two-signal oracle — the project's constitution

The rule (from `CLAUDE.md`, non-negotiable and stated to be un-weakenable): **every quality claim —
an ablation delta in Stage 1 or a steering delta in Stage 2 — requires two independent signals.**

1. **Objective metrics on the rendered output.** Render each page in a real headless browser and
   compute deterministic numbers on the **rendered DOM and screenshot** — never on the raw HTML
   string. These are "unfoolable": a contrast ratio is a contrast ratio; the model can't sweet-talk
   it.
2. **A pairwise preference protocol.** Have a strong vision-language model (VLM) judge compare two
   rendered screenshots, validated against human labels, and gated behind reliability and power
   checks.

And the **null rule** that binds them (preregistered verbatim): *an effect is reported as **null**
unless it moves an objective-metric endpoint **OR** a preference delta that passes both the
reliability gate and the power gate. Aesthetic claims not backed by the objective half are
inadmissible.* An effect that moves **neither** signal is null — full stop. This is the constitution
because it's what lets the project honestly say "this didn't matter" as readily as "this did." Note
the deliberate asymmetry the null rule encodes: the two channels are joined by **OR** for detecting
an effect (either signal firing is enough — this raises power, and the dominant risk is missing a
real effect), but Stage 2's causal headline is joined by **AND** across four checks (Section 4.4),
which crushes false positives. That OR/AND split is a decision-theoretic choice, not an accident
(THEORY §T6.5).

**Why "rendered DOM, never raw code."** Two identical-looking pages can have very different HTML,
and vice versa; what a *user* experiences is the rendered pixels and the live DOM geometry, so
that's what you measure. It also makes render-*failure* itself a metric — a page that doesn't render
is a validity failure regardless of how pretty the code looks.

**Where this lives.** `CLAUDE.md` ("The correctness oracle"), `PLAN.md` §0.2, `PREREGISTRATION.md`
§8 (the verbatim null rule), `paper/sections/oracle.tex`.

### 3.3 The objective metric families — one sentence each

The metrics are reported as a **vector** organized into six families, not blended into one number
blindly (blending comes later, carefully, in the POC). Each family catches a different failure mode:

- **V — Validity/hermeticity:** does it render at all, does it fetch anything external (it
  shouldn't), how many elements overflow the viewport or overlap each other, how many accessibility
  violations does axe-core find. *Catches broken and non-self-contained pages.*
- **A — Accessibility/contrast:** the WCAG contrast ratio of every text node against its background
  — fraction below the 4.5:1 legibility threshold, plus min and median. *Catches unreadable
  low-contrast text.*
- **L — Layout:** the Ngo family of computational-aesthetic measures — balance, equilibrium
  (center-of-mass offset), symmetry, alignment regularity (how few distinct edges elements share),
  white-space ratio, density. *Catches sloppy, unaligned, cramped or empty layouts.*
- **T — Typography:** how many distinct font sizes and families, and whether the sizes follow a
  consistent modular scale (a fixed geometric ratio). *Catches ransom-note typography.*
- **C — Color:** Hasler colorfulness (a validated single number for how colorful an image is),
  number of dominant colors, figure-ground contrast, and the purple-slop subcomponents. *Catches
  garish or muddy palettes.*
- **X — Complexity:** visual complexity via quadtree/edge density, used with an inverted-U prior
  (too simple *and* too busy both hurt). *Catches over- or under-designed pages.*

There is also an **auxiliary** tier (UIClip, a learned UI-quality scorer, and CLIP prompt-screenshot
relevance), which is treated as *validation targets only*, never as oracle evidence — because a
learned neural scorer is opaque and non-deterministic, which violates "deterministic and
unfoolable," and UIClip was trained on a mobile distribution unlike these desktop renders.

**Where this lives.** `PLAN.md` §III.3 and Appendix B (exact formulas), `THEORY.md` §T7,
`src/p19/metrics_dom.py` (families V/A/L/T from the DOM), `src/p19/metrics_visual.py` (families C/X
from the screenshot), `tests/test_metrics.py`.

### 3.4 The POC — one composite, and why composites are dangerous

The confirmatory tests need **one** primary objective number per page (you can't run a clean,
preregistered test on a 20-metric vector without drowning in multiple comparisons). So the project
defines the **Primary Objective Composite (POC)**: z-score seven core metrics over all development
generations, orient each so higher = better, and average them. The seven: alignment regularity,
white-space, type-scale consistency, contrast pass-rate (all +), and overflow/overlap count,
purple-slop index, and distance-of-colorfulness-from-a-target (all −). Render-failed pages are
excluded from POC and counted in family V instead.

**Why composites are dangerous, and why this one is safe.** The moment you're allowed to *choose*
how to blend metrics after seeing the data, you enter the **garden of forking paths**: with enough
metrics and enough ways to weight them, some combination will always look significant by chance, and
you'll have no way to know if you found a real effect or just the lucky blend. The only defense is
to **fix the exact formula before you see the data** — the seven terms, their orientations, the
z-score reference distribution, and any conditional branches — and freeze it in the preregistration.
That's what makes the POC an admissible confirmatory endpoint rather than a fishing expedition. Note
the colorfulness term is a *distance to a target* c\*, not "more is better," encoding the empirical
inverted-U: moderate colorfulness is most appealing.

The POC even carries two **pre-specified conditionals** frozen with it, so that data-dependent
choices are made by a rule written in advance rather than by judgment after the fact: (i) if the
purple-slop index fails its validation (Section 3.5), the confirmatory POC drops that term and
becomes a **6-term** composite; (ii) the colorfulness target c\* is the median colorfulness of
human-preferred pages *if* at least 30 such pages exist, else it defaults to the median colorfulness
of the development FULL-cell pages. Which branch fired is written to the manifest *before* the first
confirmatory test runs.

**Where this lives.** `PLAN.md` §III.4 and Appendix B.8, `THEORY.md` §T7.7, `src/p19/poc.py`,
`tests/test_poc.py`.

### 3.5 The purple-slop index — and why it must be validated before it counts

The purple-slop index (PSI) is the clever bit: the skill's own C5 negatives tell you *exactly* what
"AI slop" looks like, so you measure precisely those tells. PSI is a weighted mix of four
subcomponents, each in [0,1]: the fraction of salient pixels in the purple hue range [260°, 290°];
the prevalence of `linear-gradient` backgrounds on large/hero elements; the share of text in
Inter/Roboto/system-ui; and a centered-hero flag. Lower PSI = less slop.

But PSI is something *we invented*, so it doesn't automatically get to count as evidence. It has to
**earn** admissibility by correlating with reality: on the human-labeled subset, humans also rate
each screenshot on "how AI-generated does this look?", and PSI is admitted as evidence only if its
Spearman correlation with that human rating is **≥ 0.4** (with a bootstrap CI excluding zero). If it
fails, PSI is demoted to a descriptive diagnostic and the POC recomputes without it (the 6-term
conditional above). This is the general principle in miniature: **a metric you built is a hypothesis
until it's validated against something external.** The same discipline applies to UIClip (admitted
only if it correlates ≥ 0.3 with human win-rate, else dropped).

**Where this lives.** `PLAN.md` §III.3.1 (validation gates) and Appendix B.7, `THEORY.md` §T7.6,
`src/p19/metrics_visual.py`, `PREREGISTRATION.md` §9, figure F10.

### 3.6 The judge protocol — position bias, both orders, ties

The second signal is a **pairwise preference**: show a VLM judge two rendered screenshots built for
the same brief and ask which is better designed. Pairwise (A-vs-B) is far more reliable than asking
for an absolute 1–10 score. The primary judge is **Gemini 2.5 Flash** (cheap, high-throughput, and —
importantly — a *different model family* from Qwen, so it can't self-enhance by preferring its own
outputs), with GPT-4o auditing a 15% random subset. The judge is anchored to a checklist drawn from
the six metric families (color coherence, layout/hierarchy, typography, component quality,
restraint/absence-of-slop, fit-to-brief), which is what pushes agreement up.

Two bias controls you should know:

- **Position bias / both orders.** LLM judges have a systematic preference for whichever option is
  shown first. So every pair is judged **twice** — once as (A, B), once as (B, A) — and a winner
  **counts only if it's consistent across both orders**. If the judge flips its answer when you swap
  the order, that's recorded as a **tie**. This is a clean, cheap way to neutralize position bias.
- **Ties are information, not noise.** An order-inconsistent verdict means the two pages are
  near-equal, and that's modeled explicitly (Section 3.8), not thrown away as half-a-win.

**Where this lives.** `PLAN.md` §III.8 and Appendix C (the verbatim judge prompt),
`config/judge.yaml`, `src/p19/judge.py` (both-orders adjudication, with a mock dry-run mode so it's
testable on CPU), `tests/test_judge.py`.

### 3.7 Why raw agreement lies under skew — the kappa paradox

Before you trust the judge, you have to show it agrees with humans. The naive way is "percent
agreement" — but that number lies when one answer dominates, and here the skill almost always wins,
so the labels are heavily skewed. This is the **kappa paradox**, and here it is in exact numbers (a
paragraph you should be able to reproduce).

Take 100 items, and hold **agreement fixed at 90%** in two scenarios. **Skewed** (skill usually
wins): raters agree "A wins" 85 times, agree "B wins" 5 times, disagree 10 times. **Balanced:**
agree "A" 45, agree "B" 45, disagree 10. Same 90% raw agreement in both. Now compute
**Krippendorff's α**, which is (observed agreement − chance agreement) / (1 − chance agreement),
where "chance" is estimated from the marginal category frequencies:

- Skewed: chance agreement is high (because "A" is so common that two raters guessing would often
  both say "A"), so α = 1 − 0.10/0.18 = **0.44**.
- Balanced: chance agreement is 0.50, so α = 1 − 0.10/0.50 = **0.80**.

Identical 90% agreement, but α reads 0.44 versus 0.80 — the coefficient moved **only because of the
marginal skew**, not because the raters agreed any less. That's the paradox: under skew, α is
crushed toward zero and would false-fail a perfectly good judge. **Gwet's AC1** fixes this by using
a different chance model — it assumes random agreement can only happen on the items raters are
actually unsure about, and that propensity *shrinks* as one category dominates. On the same skewed
panel, AC1 = **0.878**; on the balanced panel it's 0.80 (when marginals are balanced, α and AC1
coincide). So the reliability **gate** is disjunctive: pass if **α ≥ 0.667 OR (AC1 ≥ 0.80 with
demonstrable skew)** — where "demonstrable skew" is operationalized (the majority category exceeds
~80%) so AC1 can't become a loophole in the balanced case where it has no excuse. You report both,
with bootstrap CIs, so a stricter reader can apply their own bar.

**Where this lives.** `THEORY.md` §T4 (the full derivation and this exact worked example), `PLAN.md`
§III.8, `src/p19/agreement.py`, `tests/test_agreement.py` (which asserts the 0.444/0.878/0.80
numbers exactly), `PREREGISTRATION.md` §5, figure F11.

### 3.8 Bradley-Terry — chess ratings for web pages — and the style-control trick

Once you have a pile of pairwise verdicts, you need to turn them into a per-cell quality score with
uncertainty. **Bradley-Terry** is the model for exactly this, and the cleanest analogy is **chess
ratings**: give each cell a latent "strength" β, and model the probability that cell i beats cell j
as a logistic function of the strength difference, σ(βᵢ − βⱼ). Fit by what is, mechanically, a
logistic regression with one indicator per cell. It's the same math behind Elo and behind the LMSYS
Chatbot Arena leaderboard. Ties are handled with a **Davidson** term (tie mass peaks when strengths
are equal). One strength is unidentifiable (only differences matter), so the reference is pinned at
β(NEUTRAL) = 0 — meaning every reported utility is "quality relative to the length-matched neutral
control," which is precisely the scientifically meaningful zero.

**The style-control trick — and the mediation trap.** VLM judges reward superficial style — longer
pages, more elements, more color — independent of actual quality. Chatbot Arena's fix (which this
project borrows) is to add **style covariates** to the Bradley-Terry model: regress the outcome on
the strength difference *plus* the difference in log-DOM-size, log-token-length, element count,
colorfulness, and text density. This is standard omitted-variable-bias logic — if you leave style
out, the estimated design effect absorbs the systematic style gap between cells (if the skill makes
longer pages and the judge likes length, plain Bradley-Terry over-credits the skill). Putting the
covariates in identifies the style bias from within-cell variation and subtracts it, leaving
substance. It's the analysis-level twin of the design-level length-matched control — defense in
depth.

But there's a trap you must flag: **the mediation trap.** Some of these covariates are *pure* judge
biases (a designer does not judge quality by DOM node count), and those are always controlled. But
**colorfulness is different** — choosing a deliberate, moderate palette *is* part of good design, so
it's partly the *mechanism* through which C1 works. If you blindly regress out colorfulness, you'd
subtract a **genuine** C1 effect along with the bias — you'd be "controlling for" a mediator, which
is a classic causal-inference error. The preregistered rule: control the pure-bias covariates
always; include colorfulness but **flag it as partially causal**, report the Bradley-Terry utility
both with and without it so the adjustment is visible, and recover the legitimate color effect
through the *objective* channel (the POC's colorfulness term and the Stage-2 color-family steering
signature), which doesn't route through the judge and so isn't double-counted. If the controlled and
uncontrolled estimates disagree in sign, the contrast is reported as "style-confounded" rather than
resolved.

**Where this lives.** `THEORY.md` §T5 (the model, the omitted-variable derivation, and the mediation
caveat), `PLAN.md` §III.5, `src/p19/bt_model.py` (style-controlled BT with Davidson ties and
cluster-bootstrap CIs), `tests/test_bt_model.py`.

### 3.9 Power — how many judgments before 60/40 beats a coin

A preference delta is only usable if you gathered enough comparisons to see it. The question is
literally: *how many judgments before a 60/40 win-split is statistically distinguishable from a fair
coin (50/50)?* Because comparisons are paired (same prompt, two cells), the sizing uses the
**McNemar** paired-proportion formula, and the answers (at α = 0.05, power = 0.80) are:

- **60/40** split needs **~200** pairs,
- **65/35** needs **~80**,
- **55/45** needs **~780**.

(I recomputed these from the formula and got 193.8, 84.8, 782.5 — they check out.) The judgment
budget is allocated to match: the headline FULL-vs-NEUTRAL edge gets 200 pairs (enough to catch even
a 55/45 shift), each necessity edge gets ~120 (enough for 60/40), and small expected effects are
lightly powered on the *preference* signal on purpose — because their non-null status can still be
established via the fully-powered *objective* signal, per the two-signal rule.

**The decisive-vs-judged subtlety** (worth getting right, because it looks like a contradiction and
isn't): the "~200" counts **decisive** pairs — those where the judge gave an order-consistent,
non-tie verdict. The allocation table counts **judged** pairs. At a tie rate t, an edge yields
roughly (1 − t) × judged decisive pairs. So if half your pairs tie, you need ~400 judged pairs to
get ~200 decisive ones. The one thing you must *not* do is plug the marginal preference gap together
with a "probability a pair is decisive" of less than 1 into the two-parameter formula — that mixes a
conditional split with a discordance rate and yields a meaningless ~93. THEORY §T6.2 flags this
"mis-plug" explicitly and shows the two internally consistent readings both land on ~200 decisive.
The **power gate** then applies post-hoc: a preference delta counts only if its edge actually
achieved the pairs required *at the observed split*; if not, it's "under-powered" and cannot be the
sole signal (but is never reinterpreted as a null — you fall back to the objective channel or buy
more seed-pairs).

**Where this lives.** `THEORY.md` §T6.1–T6.3 (derivation, the 200/80/780 table, the mis-plug
warning, and post-hoc power as an admissibility screen — *not* an inference), `PLAN.md` §III.7,
`src/p19/power.py`, `tests/test_power.py`, `PREREGISTRATION.md` §6.

---

## 4. Stage 2 explained — the interpretability chapter

This is the part you're newest to, so it goes slowest and deepest. Everything here happens *inside*
the model, on its activations. The reassuring news: the core objects map onto things you already
know — a linear probe is logistic regression, a steering vector is a difference of group means, the
necessity test is a projection, and the causal logic is an intervention (a do-operation, the
interventionist's RCT).

### 4.1 What "the model's activations" literally are — the residual stream

A transformer processes a sequence of tokens. As each token flows through the model's 28 layers, it
carries with it a vector of **3,584 numbers** — think of it as a running summary of "everything the
model currently understands about this position." That evolving vector is the **residual stream**.
The name comes from the architecture: each layer doesn't *replace* the vector, it **reads a
normalized copy and adds its edit back**:

> h(next layer) = h(this layer) + [attention's contribution] + [MLP's contribution].

Because every layer reads and writes by **addition**, the residual stream is a **linear
communication channel** — a running ledger where the state at layer ℓ is just the embedding plus the
sum of all the edits written by earlier layers, and the final prediction is a linear readout of the
last layer's state. Two facts make this the natural place to do interpretability:

- **You can read a concept by projecting and write it by adding.** If "clean design" is encoded as
  some direction in that 3,584-dimensional space, you can *measure* how much of it is present by
  taking a dot product (project the state onto the direction), and you can *inject* it by adding a
  multiple of the direction to the state. Those two operations — read by projection, write by
  addition — are exactly what Stage 2 needs, and they only make sense because the stream is additive
  and linear.
- **Concepts live as directions, not as individual neurons** (the linear-representation hypothesis,
  plus superposition: the model packs many more features into the space than it has dimensions, as
  overlapping directions). So the right object to hunt for is a **direction**, and the residual
  stream is where directions live.

So concretely: **reading** activations = run the model over `[prompt ‖ response]`, record the
residual-stream vector at each layer for each token (in practice, the *mean over the response
tokens*, because the behavior shows up in what the model *writes*, not in the prompt). **Writing** =
during generation, add a chosen vector to the residual stream at a chosen layer, on the fly, and let
the rest of the forward pass proceed. In this codebase, "each layer's output" is
`model.model.layers[i]` output `[0]`, a tensor of shape `[batch, seq, 3584]`, and hooks grab or edit
it.

**Where this lives.** `THEORY.md` §T8.1, `docs/DECISIONS.md` ADR-002 (the hook approach and why HF
transformers, not vLLM, for this), `src/p19/hooks.py` (~200 lines of capture/add/project-out ops,
unit-tested against a fake decoder layer so the logic is verified with no GPU),
`src/p19/activations.py`, `tests/test_hooks.py`.

### 4.2 What a steering vector is — and the honest caveat

The **steering vector** is disarmingly simple. Generate a batch of pages **with** the skill (FULL)
and a matched batch **without** it (NEUTRAL), record the mean residual-stream vector for each, and
**subtract**:

> v = mean(activations with skill) − mean(activations without skill), then normalize to unit length.

That's it — a **difference of means**, the exact object you know from a two-sample comparison. Why
does subtracting means isolate "design"? Because **everything the two conditions share cancels**.
Both batches are writing HTML, both are following the task brief, both are in "generate a web page"
mode — all of that common content is present in *both* means and vanishes in the difference. What
*survives* is exactly what differs between the conditions: the design shift the skill induces. And
because NEUTRAL is length-matched filler (Section 2.3), the surviving difference is design
**content**, not "responding to a long instruction." The vector points from "no-skill activations"
toward "skill activations" — the empirical mean shift, which by construction lands on the data
manifold where real skill-on activations live.

**Why a difference of means and not a probe direction, for steering.** You'll be tempted to ask: why
not use the direction a classifier (a linear probe / LDA) would learn to *separate* the two classes?
Because reading and writing want different vectors. The Bayes-optimal *discriminant* direction is
Σ⁻¹(μ₁ − μ₀) — the mean shift **whitened** by the inverse covariance, which re-weights to maximize
separation (great for *reading*). But for *writing*, whitening is pathological: dividing by small
covariance eigenvalues **amplifies low-variance nuisance directions**, so adding the whitened vector
shoves activations off-distribution along directions the model rarely uses — you break coherence
without a proportionate behavior change. The un-whitened difference of means stays on-manifold and
cancels shared nuisance. So the rule is: **probe/LDA to locate, difference-of-means to steer.**
(When the class covariance is roughly isotropic the two coincide, and the project reports the cosine
between them as a diagnostic.)

**The honest caveat — "a" direction, not "the" direction.** Even if this vector steers beautifully,
you have **not** shown it is the unique "design direction." Under single-layer access, many
behaviorally-equivalent vectors can exist — a whole **concept cone** of directions that produce the
same effect (this is a real non-identifiability result in the literature). So the claim is always
carefully worded: "**a** causally sufficient/necessary design direction," never "**the** design
direction." Compare it to collinear regressors — you can't identify a unique coefficient vector from
behavior alone. This honesty is baked into the paper's wording and into RQ8, which explicitly probes
whether the direction is one axis or a cone.

**Where this lives.** `THEORY.md` §T8.2 (the difference-of-means derivation, the LDA comparison, the
bias of the mean-over-response estimator), `PLAN.md` §IV S2.2, `src/p19/steering.py`,
`tests/test_steering.py`.

### 4.3 Locate → extract → steer → verify — a detective story

The Stage-2 pipeline is a detective story with five moves. Each move rules out a way you could be
fooling yourself.

**Move 1 — Locate (probing, diffing, patching): where is the signal?** You don't know which of the
28 layers carries the design signal, so you interrogate all of them.

- **Linear probes.** At each layer, fit a **linear logistic probe** — literally logistic regression
  on the residual-stream vectors — to classify skill vs no-skill, cross-validated by prompt (never
  letting a prompt appear in both train and test folds). Report the **AUC** per layer: high AUC
  means the skill/no-skill distinction is **linearly decodable** at that layer. But — and this is
  the crux — **decoding is not causing.** A probe reading 0.95 AUC only tells you the *information
  is present and readable*, exactly like finding that a variable is a strong *predictor* in a
  regression. It does **not** tell you the model *uses* that direction to do anything downstream. A
  probe can even memorize; to guard against that you also compute **selectivity** = (real-task AUC)
  − (control-task AUC), where the control task assigns each prompt a random-but-fixed label. A
  trustworthy probe scores high on the real task and low on the memorization control. High AUC with
  high selectivity says "genuinely, linearly there" — but still only *correlational*.
- **Activation patching.** A more surgical localization: run the model on a neutral prompt, then
  **transplant** (patch in) the skill-side activation at one specific (layer, position) site, and
  see whether the design behavior gets restored. This is *denoising* patching (start
  corrupted/neutral, add a clean piece, measure recovery), chosen because it's robust to
  "self-repair" — the phenomenon where ablating one component lets others compensate and a
  truly-necessary site looks unnecessary. It answers "**is this site sufficient** to move the
  behavior?" measured as the percent of the clean-vs-corrupt gap recovered. (There's no single
  "answer token" in a 3,000-token HTML page, so the metric is a logit-difference on the first token
  where the model *commits* to a style choice — a non-Inter font, a non-purple hex — with an
  explicit caveat that patching alone can be an "interpretability illusion," so it's only ever used
  to triangulate, never to decide alone.)

The RQ5 decision rule requires **all three** to agree — probe AUC ≥ 0.80 **and** selectivity ≥ 0.15
**and** patching recovers ≥ 25% — before calling a layer band "localized." No single correlational
signal gets to decide.

**Move 2 — Extract:** compute the difference-of-means vector (Section 4.2) at the located layers, in
three position variants (mean-over-response as primary, plus last-prompt-token and first-64-tokens),
and cross-check it against a PCA-of-differences direction (they should point the same way).

**Move 3 — Steer with NO design prompt (the causal proof of sufficiency).** Here's the move that
turns correlation into causation, and it's the single most important idea in Stage 2. Take the
**NOSYS** base — the model with **no design prompt whatsoever** — and during generation, **add** the
steering vector to the residual stream at the frozen layer. Compare steered-NOSYS against
unsteered-NOSYS. Why is this *causal* where probing was only correlational? Because the model was
**never told about design**. The only thing that differs between the two arms is the injected
vector. In Pearl's language this is a **do-operation**: you *set* the activation, severing its
normal dependence on the (absent) prompt, so any resulting quality gain is *caused* by the vector,
not by some confounder in the prompt. It's the interpretability analogue of a randomized controlled
trial: probing is the observational study (X predicts Y), steering-with-no-prompt is the RCT (we
*set* X and Y moved). If quality improves with the prose removed, the vector carries the mechanism.

**Move 4 — The flip test (the causal proof of necessity).** Sufficiency ("adding it helps") and
necessity ("removing it hurts") are different claims, and a direction can be one without the other.
The flip test establishes necessity: with the skill **present** (FULL), **project the direction
out** of the residual stream at every layer and position — multiply the state by P = I − v̂v̂ᵀ, the
orthogonal projector that kills exactly the component along v̂ and leaves the other 3,583 dimensions
untouched (the same projection geometry as the regression hat matrix). If the skill's quality gain
**disappears** even though its 391 tokens are still in the prompt, then the skill was routing its
effect *through that direction* — the direction is necessary. If the gain survives, the skill has
other routes (a cone), and you honestly report "sufficient, not demonstrably necessary." (Elegantly,
this projection can be "baked into the weights" so no inference-time hook is needed — Arditi's
weight-orthogonalization trick.)

**Move 5 — The three controls that keep you honest.**

- **The norm-matched random control.** Maybe *any* big shove to the activations jogs quality, and it
  has nothing to do with *your* direction. To rule this out, draw **5 random directions** of the
  **same magnitude** as the steering vector and inject them the same way. If a random push of equal
  norm *also* improves pages, you have a **norm effect**, not a **direction effect**, and you
  downgrade the claim. The real direction must beat the random ones.
- **The KL guardrail (dose-response).** You can always "improve" a metric by cranking the injection
  so hard the model leaves its training distribution and outputs degenerate pages that happen to
  game a number. Behavior is **non-monotone** in the injection strength — there's a sweet spot, then
  collapse. So the injection strength is swept, and capped by a **coherence guardrail**: the mean
  per-token KL divergence between the steered and unsteered next-token distributions on a fixed eval
  text must stay **≤ 0.30 nats**, and steered render-success must stay ≥ 0.90. KL is the natural
  "off-distribution alarm" — it measures how much steering has overwritten the model's own
  predictions. A win bought above the guardrail (Branch C.2) doesn't count. (The 0.30 threshold is
  an honestly-labeled operating convention, not a derived optimum.)
- **Out-of-distribution held-out task types.** The direction is extracted only from development
  prompts (marketing/content pages: landing, dashboard, form, etc.). The causal test includes **two
  task types the extraction corpus never contained** — settings-panels and admin-data-tables, which
  are control-dense, information-dense layouts structurally unlike the training types. If steering
  still helps *there*, it encodes transferable design *content*, not a memorized artifact of the
  extraction set. This is the memorization-vs-mechanism test.

**The operating-point freeze that makes this legitimate.** All the tuning — which layer, which
strength, which position variant — happens on the **development** set. The winning configuration is
frozen, written to `config/steering_frozen.yaml`, and **git-tagged `steer-frozen` before the
held-out set is touched even once**. Held-out is touched exactly one time, for the confirmatory
test. This prevents the cardinal sin of tuning on your test data.

**Where this lives.** `PLAN.md` §IV S2.0–S2.7, `THEORY.md` §T8 (probing, patching, addition,
ablation operators) and §T9 (the do-calculus framing and the threats-and-fixes table),
`src/p19/probes.py`, `src/p19/patching.py`, `src/p19/steering.py`, `src/p19/hooks.py`, `RUNBOOK.md`
sessions 6–8, `PREREGISTRATION.md` §7 (the verbatim success criterion).

### 4.4 What each Stage-2 ending means — branches A/B/C in plain language

The success criterion is a **conjunction** (AND) of four checks, which is what buys a causal
headline out of individually-fallible tests: (E1) steered beats unsteered on ≥ 1 objective family
after multiple-comparison correction; (E2) the reliability-gated preference delta favors steered
with a CI above zero; (E3) the norm-matched random control does **not** clear both bars; (E4) the
flip test attenuates the skill's gain. Mapping to the paper's written branches:

- **Branch A — a causal design direction exists.** All the addition checks pass and random fails.
  Sub-branch **A.1 (sufficient and necessary)** if the flip test also attenuates — the strongest
  result, the skill's effect is largely *routed through this one direction*, mirroring the famous
  refusal-direction result but for a graded, multi-component *aesthetic* behavior. Sub-branch **A.2
  (sufficient, not demonstrably necessary)** if addition works but the flip test doesn't — the
  direction is *a* carrier, not *the* unique one (a concept cone). The headline number is
  **%-skill-reproduced** = (steered − unsteered) / (FULL − unsteered), the fraction of the full
  skill's gain that a single injected vector recovers with the prose removed.
- **Branch B — the honest null.** No single direction steers under the guardrail — even the
  pre-stated multi-layer and subspace fallbacks fail — *yet* the probe can still read the
  skill/no-skill distinction at high AUC. So there's a direction that **correlates** with design but
  does not **cause** it when injected. This is a "null with teeth": the power gate certifies the CIs
  are tight enough to exclude the effect the study was designed to detect. It rules out the
  strongest single-direction account for this behavior in this model and is consistent with two
  readings stated honestly (distributed across many directions, or genuinely non-linear).
- **Branch C — partial outcomes**, each with a bounded claim: **C.1** steers the objective metrics
  but not human preference (metric-level effect, aesthetic claim declined); **C.2** only "steers" by
  breaking coherence above the KL guardrail (reported as coherence-breaking, not a win); **C.3**
  anti-steerable majority — the mean is ~zero because it helps half the prompts and harms half (why
  the protocol reports the full per-prompt distribution, never just the mean); **C.4** sufficient
  but not necessary (the concept-cone outcome).

**Where this lives.** `paper/sections/stage2_results.tex` (all branches written out in full, one
kept on real data), `PLAN.md` §IV S2.4, `PREREGISTRATION.md` §7, `paper/SLOT_REGISTRY.md` ("Which
branch to keep").

### 4.5 The Stage-1 ↔ Stage-2 bridge — the coolest possible result

Here's the payoff that connects the two stages. Stage 1 finds that the skill decomposes into
components (color, layout, typography, ...). Stage 2 finds a direction in activation space. The
bridge question (RQ8): **do the ablation's components correspond to separable directions inside the
model?**

You build a **component sub-vector** for each component — the difference-of-means of "only Cᵢ
present" (the AOI cells) vs NEUTRAL — and ask two things:

- **Geometry (near-orthogonality):** is the cosine between different component sub-vectors small
  (mean |cos| < 0.3)? Near-orthogonal sub-vectors are *evidence* that the components live as
  distinct, roughly-independent directions — a **component basis** — rather than one entangled blob.
  (This is predicted by the geometry of linear representations.)
- **Signature match (the causal half):** cosine can only show the sub-vectors are *linearly
  distinguishable*; it cannot show each one *causally* steers its own topic. So you also **steer
  each sub-vector** and check that it moves *its* metric family most — the color sub-vector moves
  color metrics, the layout sub-vector moves layout metrics, and so on. "Found" requires **both**:
  near-orthogonal **and** ≥ 3 of 5 signatures match.

If this holds, you've shown that "clean design" is not one entangled thing but a **small set of
separable, individually actuatable sub-concepts**, and that the black-box ablation signatures
correspond to white-box steering directions — an ablation ↔ activation correspondence, a genuine
bridge between prompt-level and representation-level explanations. That would be the paper's
strongest result. If it's absent, that's also informative and slightly surprising: the component
structure was a property of the *instruction*, and the model compresses five instructions into one
axis of variation.

**Where this lives.** `PLAN.md` §IV S2.8, `THEORY.md` §T9.4 (what cosine can and cannot show),
`paper/sections/stage2_results.tex` (RQ8 branches), `paper/sections/discussion.tex` (the "bridge
holds / bridge fails" framing), figure F9.

---

## 5. The statistics, translated

You know all of these; this section just names how they're used here and gives the one-line
intuition for each.

**Mixed-effects models — "prompts are personalities; seeds are moods."** Every objective delta is
estimated with a mixed model: y = μ + (fixed cell effect) + (random prompt effect) + (random
cell-within-prompt effect) + (seed noise). The **cells are fixed** (they're the manipulation you
designed), while **prompts and seeds are random** (a sample of tasks and stochastic decodes). The
mental model: a *prompt* is a personality — some briefs are intrinsically designier — and that
personality shifts every cell's score at that prompt up or down together (the random prompt
intercept); a *seed* is a mood — the same prompt on a different day comes out a bit different (the
residual noise). Modeling prompt as a random effect is what correctly deflates your sample size for
pseudoreplication (Section 2.5) and what a per-generation t-test gets wrong. When the richest model
won't converge on the unbalanced seed counts, there's a preregistered fallback ladder (drop the
random slope → REML-to-ML → non-parametric cluster bootstrap over prompts), and the rung actually
used is recorded.

**Holm vs BH — "strict list vs discovery list."** You're testing many things, so you must control
for multiple comparisons — but not the same way everywhere. The **confirmatory** claims (the
headline effects: FULL−NEUTRAL, the five necessity contrasts, the five sufficiency contrasts,
FULL−BEAUTY1 — 12 tests, applied separately to the objective and preference channels) use **Holm**,
which controls the *family-wise error rate* — the chance of even **one** false claim among them.
That's the "strict list": a single false headline is costly, so you protect against any. The
**exploratory** scans (the ten interactions, per-family metric scans, per-task-type breakdowns) use
**Benjamini-Hochberg**, which controls the *false discovery rate* — the expected *fraction* of your
flagged findings that are false. That's the "discovery list": you accept a controlled sprinkling of
false leads to keep the power to find real ones. Confirmatory = don't cry wolf even once;
exploratory = a few wolves are fine if most are real.

**Preregistration — "we wrote the rules before rolling the dice."** Everything that could be chosen
after seeing the data — the cell table, the exact POC formula and its conditional branches, the
endpoints, every gate threshold, the Holm/BH split, the null rule, the power targets, the Stage-2
success criterion — is frozen in `PREREGISTRATION.md` and **git-tagged `prereg-v1` before a single
GPU generation runs**. This is the structural defense against the garden of forking paths: you can't
p-hack a rule you committed to in public beforehand. Any post-freeze change requires a dated
amendment, and a change to a *confirmatory* decision forks a new tag and is reported as a deviation
in the paper. The four things that may **never** be weakened post-freeze: the null rule, the cell
table, the confirmatory family, and the Stage-2 success criterion.

**The null rule (verbatim), and its plain-language paraphrase.**

> *An ablated component's effect, or a steering direction's effect, is reported as **null** unless it
> moves an objective-metric endpoint (POC Holm-significant, or ≥2 concordant BH-significant families)
> **OR** a preference delta that passes both the reliability gate and the power gate. Aesthetic claims
> not backed by the objective half are inadmissible. Stage-2 bar: a "design direction" is real only if
> steering it with no design prompt causally reproduces a measurable quality gain on held-out prompts;
> a direction that correlates but does not causally steer is a hypothesis, not a finding. If no clean
> steerable direction exists, that null is a result and is written up honestly.*

Paraphrase: *Nothing counts as an effect unless a deterministic rendered-page metric moves it, or a
human-validated, adequately-powered preference moves it. Pretty pictures alone prove nothing. For
Stage 2 specifically, the direction has to actually **cause** a quality gain when you inject it with
no prompt — merely correlating with design isn't enough. And if the honest answer is "no steerable
direction here," you say so, and that's a real result.*

**Where this lives.** `THEORY.md` §T3 (mixed models), §T6.4 (Holm/BH proofs and the philosophy),
§T6.5 (the null rule as error algebra); `PLAN.md` §III.6; `PREREGISTRATION.md` (the whole file,
especially §8); `src/p19/mixedlm.py`, `src/p19/multiplicity.py`.

---

## 6. Repo tour — and what runs where

### 6.1 Top-level map

- **`CLAUDE.md`** — the governance contract: locks the model, defines the compute policy (no GPU
  here), states the oracle and commit policy. The rules everything else obeys.
- **`docs/BRIEF.md`** — the original project brief (do not edit); the mandate the whole thing
  answers.
- **`docs/DECISIONS.md`** — the 10 ADRs (architecture decision records): the model choice (001), the
  hook tooling (002), the length-matched control (003), the factorial design (004), the judge
  protocol (005), hermetic output (006), build order (007), SAE demotion (008), component
  orthogonality (009), and the tokenizer/freeze reconciliation (010). This is the "why we chose X"
  log — read it before challenging any decision.
- **`PLAN.md`** — the authoritative, self-contained master plan (~1,500 lines). Every knob has a
  value; a competent engineer could execute the whole project from it with no further design
  decisions. Parts 0–VIII cover framing, data, Stage 1, Stage 2, figures, engineering, statistics
  hooks, and risks.
- **`THEORY.md`** — the mathematical backbone (T1–T10): the DOE algebra, mixed models, agreement
  coefficients, Bradley-Terry, power, the objective-metric formulas, and the interpretability math
  (residual stream, diff-in-means, addition/ablation, do-calculus). Where every equation the paper
  might use is derived, with honest labels on the conventions.
- **`PREREGISTRATION.md`** — the freeze document: hypotheses, the 24-cell table, endpoints, gates,
  the null rule, power targets, amendments policy. Git-tagged before any GPU run.
- **`RUNBOOK.md`** — the Colab execution guide: nine GPU/CPU sessions with exact commands, GPU type,
  time, inputs, outputs, and an acceptance check to eyeball before proceeding.
- **`research/`** — the literature dossier: `SYNTHESIS.md` (the decision document — 10 load-bearing
  findings, the assembled recipes, risks, and the honest novelty statement), per-paper notes under
  `notes/`, the frozen skill under `skill_exemplars/`, and `refs.bib`.
- **`config/`** — all the frozen knobs in YAML (model, skill, prompts, cells, render settings,
  judge, steering grids, and the steering-frozen file written by Stage 2).
- **`fixtures/`** — hand-authored HTML pages (clean, slop, broken, overflow) that give every metric
  a known-answer test case.
- **`paper/`** — the two-part paper scaffold (see 6.4).
- **`SEAN-README.md`** — this file.

### 6.2 The `src/p19` package — module by module

Reusable machinery lives here with unit tests; notebooks import from it. GPU-dependent modules are
import-guarded and tested against **mocked** model objects (a fake decoder layer returning known
tuples) so the logic is verified with no weights.

| module | what it does | runs on CPU now? |
|---|---|---|
| `config.py` | load/validate YAML, freeze-hash configs | yes |
| `skill_assembly.py` | build system prompts from components+fillers; the ±15% token assertion, the render-inertness filler audit, LOO/AOI padding | yes |
| `prompts.py` | prompt corpus loader; the whole-word leakage audit; ChatML assembly | yes |
| `generation_vllm.py` | Stage-1 bulk generation (vLLM); plan builder + import-guarded runner | plan/tests yes, gen on GPU |
| `generation_hf.py` | Stage-2 HF generation (hookable); same record schema | tests yes, gen on GPU |
| `hooks.py` | residual-stream capture / add-vector / project-out ops (~200 LOC) | logic tested vs mocks |
| `activations.py` | mean-response / last-prompt / first-k capture; running-mean stability | yes (synthetic) |
| `steering.py` | diff-in-means, PCA/LAT direction, add/ablate, KL guardrail, weight-orth | yes (synthetic) |
| `probes.py` | per-layer linear probes + control-task selectivity + band choice | yes (synthetic) |
| `patching.py` | denoising activation patching + logit-diff proxy + %-recovered | yes (synthetic) |
| `rendering.py` | deterministic Playwright render + DOM-JSON export | **yes (real renders)** |
| `metrics_dom.py` | render-success, hermeticity, overflow/overlap, WCAG contrast, Ngo layout, type-scale | **yes (real)** |
| `metrics_visual.py` | Hasler colorfulness, dominant colors, figure-ground, complexity, PSI | **yes (real)** |
| `judge.py` | pairwise VLM judge, both-orders, JSON schema, mock dry-run mode | dry-run yes, live on API |
| `agreement.py` | Krippendorff α + Gwet AC1 + bootstrap CIs + marginal report | yes |
| `bt_model.py` | style-controlled Bradley-Terry (Davidson ties), cluster bootstrap | yes |
| `mixedlm.py` | MixedLM wrappers + factorial design-matrix builder (rank check) | yes |
| `multiplicity.py` | Holm (confirmatory) + BH (exploratory) | yes |
| `power.py` | McNemar sizing + BT simulation power + achieved-n checker | yes |
| `poc.py` | the POC composite + metric-row assembly + the frozen conditionals | yes |
| `synthetic.py` | synthetic-data generators with **known ground truth** (see 6.5) | yes |
| `figures.py` | all figures F1–F13 from results tables | yes |
| `manifest.py` | artifact registry + SHA-256 hashing + provenance | yes |
| `schemas.py` | versioned result schemas | yes |

### 6.3 The notebooks — and their execution states

The notebooks carry the narrative arc (a data-science lifecycle). CPU notebooks ship **executed**
with real outputs; GPU notebooks are **scaffolds** with clearly-marked, unexecuted cells and exact
run instructions. I verified the execution state of each:

| notebook | state | contents |
|---|---|---|
| `00_overview` | executed (CPU) | project map, RQ table, execution-status badges |
| `01_problem_and_data` | executed (CPU) | the skill + all build-time audits live; 24-cell table; corpus EDA; split rationale |
| `02_oracle_metrics` | executed (CPU) | metric stack on fixtures; POC + conditionals demo; F4, F10 |
| `03_oracle_preference` | executed (CPU) | judge template + mock dry-run; α/AC1 + kappa-paradox demo; power tables; F11 |
| `04_stage1_generation` | **scaffold (GPU)** | pilot gate; the 4,630-gen manifest; per-session acceptance checks |
| `05_stage1_analysis` | executed (synthetic-validated) | MixedLM + style-controlled BT; F1–F3; RQ1–RQ4 decisions incl. null demo |
| `06a_stage2_locate_extract_synthetic` | executed (CPU) | planted-direction recovery; probe AUC + selectivity; stability plateau; F5, F13 |
| `06b_stage2_locate_extract_gpu` | **scaffold (GPU)** | S2.0–S2.2 on real activations |
| `07a_stage2_steer_verify_synthetic` | executed (CPU) | S2.3–S2.8 analysis paths validated end-to-end; F6–F9, F12 |
| `07b_stage2_steer_verify_gpu` | **scaffold (GPU)** | the sweep + freeze; S2.4–S2.9 real |
| `08_results_and_conclusions` | executed (skeleton) | per-RQ decision slots; honest-null templates; paper hooks |

### 6.4 The paper and the slot registry — how results get filled in

The paper (`paper/`) is a **two-part scaffold** already written in full prose, with two clever
mechanisms so that "run the GPU phase, then fill in numbers" is nearly mechanical:

- **Numeric slots.** Every awaited number is a `\numslot{ID}` macro — 79 distinct data slots (107
  uses). `paper/SLOT_REGISTRY.md` is the authoritative map from each ID to *what the number is*,
  *its fill format* (point estimate with CI, percentage, scalar, or label), *the pipeline artifact
  that produces it* (which results file and column, or which notebook), and *the RUNBOOK session*
  that generates it. When the GPU phase lands, you replace `\numslot{STEER-REPRO}` with `42% (31,
  53)` and move on.
- **Result branches.** Every outcome-contingent claim is wrapped in a `\resultbranch{...}`
  environment — all branches are written now (Branch A/B/C, RQ7 robust/partial/brittle, RQ8
  found/partial/absent, bridge holds/fails), and you **keep exactly one** per RQ on real data and
  delete the rest. The prose is already argued for each ending, including the honest nulls.

So the write-up workflow after each RUNBOOK session is: fill that session's slots (the registry
lists them per session), then keep the branch the data selected. `paper/main.pdf` already builds
with synthetic previews so the layout is real.

### 6.5 What has already executed on CPU — and why it de-risks everything

This is the part that should give you confidence the machinery is sound before a dollar of GPU is
spent. **137 unit tests pass** across 20 test files. They fall into three groups:

1. **Known-answer metric tests** on the hand-authored fixtures (`fixtures/`): the clean page scores
   high, the slop page scores high PSI, the broken page fails render-success, the overflow page
   counts overflows — every metric has a case where you know the right answer.
2. **Real CPU execution:** Playwright actually renders the fixture HTML, the full objective-metric
   stack actually runs on those renders, the judge runs in dry-run/mock mode, and all the statistics
   run on synthetic data.
3. **Synthetic-recovery tests** — the crown jewel. `src/p19/synthetic.py` generates fake datasets
   with **planted ground truth**, and the tests assert that the **real analysis pipeline recovers
   the plant.** This is what "the pipeline recovered every planted effect" means, concretely:
   - Stage 1: a planted per-cell quality is recovered at correlation **> 0.95**; the planted
     necessity ranking (C5 > C1 > C2) is recovered with C4 as a **planted null reported null**; the
     Holm confirmatory decisions come out right (FULL−NEUTRAL, FULL−LOO-C5, FULL−LOO-C1 significant;
     C4's null stays null); the factorial recovers a planted C1×C5 **synergy** (positive) and a
     C2×C3 **sub-additivity** (negative), with the right signs.
   - Oracle: the agreement panels reproduce the THEORY kappa-paradox numbers **exactly** (α = 0.444,
     AC1 = 0.878 skewed; both 0.80 balanced); the reliability gate passes via the AC1-under-skew
     rescue rung; style-controlled Bradley-Terry recovers a planted length bias (γ > 0) and pulls
     the inflated utility down.
   - Stage 2: diff-in-means recovers a planted direction (cosine > 0.85 in-band, ≈orthogonal
     off-band); probes localize the planted peak (AUC > 0.80, selectivity > 0.15); the running-mean
     stability plateaus; the sweep recovers the planted operating point (layer 15, ρ 0.3, under the
     KL and render guardrails); the held-out arms show a positive steered−unsteered gain with CI
     excluding zero and an overall anti-steerable fraction < 50% **while** one OOD type
     (admin-table) is planted brittle > 50%; correspondence recovers near-orthogonal sub-vectors
     with ≥ 3/5 signature matches.

Why this de-risks everything: the GPU phase produces *real* data, but the code that *analyzes* it is
the exact same code being tested here on data whose answer is known. If the pipeline can recover a
planted C1×C5 synergy and a planted OOD-brittle steering direction from synthetic data, then when it
says the same things about real data you can trust the machinery isn't the source of the finding.
The only thing GPU adds is the real numbers — the statistical plumbing is already proven.

### 6.6 What awaits Colab — session by session

Nothing that loads Qwen weights, generates UIs, or captures activations runs in this environment
(the compute policy). That work is fully written, mock/synthetic-tested, and queued for Colab as
nine sessions (`RUNBOOK.md`):

| # | session | GPU | time | what it produces |
|---|---|---|---|---|
| 1 | Pilot (gate zero) | L4 | 0.5 h | 12 generations; confirm the skill visibly works before spending the budget |
| 2 | Stage-1 gen A | L4 | 3 h | ~2,000 dev generations (vLLM) |
| 3 | Stage-1 gen B | L4 | 3 h | remaining dev + held-out → cumulative 4,630 |
| 4 | Render + metrics | **CPU** | 2 h | `metrics.parquet`; PSI validation gate; F4, F10 |
| 5 | Judging + reliability + BT | CPU/API | 2 h | judgments; α/AC1; the reliability gate; BT utilities |
| 6 | Extract + locate | A100 | 2 h | the diff-in-means vector, probes, patching; F5, F13 |
| 7 | Dev sweep → **freeze** | A100 | 4 h | the α×layer sweep; freeze `(ℓ*, ρ*, variant*)`; git-tag `steer-frozen` |
| 8 | Held-out verify (the bar) | A100 | 3 h | the four-arm causal test + flip + specificity; F8, F12 |
| 9 | Stretch | A100 | 2 h | correspondence + early-token localization; F9 |

Plus a 3 h A100 buffer for re-runs. **Budget:** ~6 L4-hours + ~14 A100-hours ≈ 243 Colab compute
units ≈ **$50–65**; judging ≈ **$14**; grand total ≈ **$65–80**; storage ≈ 4–5 GB on Drive. (One
reconciliation note so it doesn't trip you up: PLAN Part IV sums the individual Stage-2 *experiment*
estimates to ~9 A100-h; the ~14 A100-h budget line in §VI.7 and the RUNBOOK adds the locate/extract
session and the 3 h buffer. The files reconcile this explicitly in Part VI — it's a
subtotal-vs-total difference, not a contradiction.)

The **hard block order** is strict: the prereg tag blocks all GPU; the pilot must pass before
generation; the dev sweep must freeze and tag before held-out is touched (once). Every session is
resumable from a manifest (checkpoint every 200 units to Drive) because Colab kills idle sessions
after ~90 minutes.

**Where this lives.** `RUNBOOK.md` (all nine sessions with commands and acceptance checks),
`PLAN.md` §VI.6–VI.7 (sessions and cost), `paper/SLOT_REGISTRY.md` (which slots each session fills).

---

## 7. "Defend it" — a self-test

Answer these out loud before an interview. One-line answer key at the very bottom; try each before
peeking.

**Stage-1 design.**
1. Why a length-matched NEUTRAL control instead of no prompt at all?
2. Why do *all* the negatives live in C5 (ADR-009)? What breaks if they're sprinkled into C1–C4?
3. Why must the neutral filler be *render-inert*, and what would go wrong if it weren't?
4. What does a resolution-V half fraction buy you over running all 32 combinations?
5. Necessity vs sufficiency — why are they different questions, and when do they coincide?
6. Why was C5 reworded to 88 tokens rather than widening the ±15% band?
7. Why 5 seeds and temperature 0.7, not greedy decoding?
8. What is pseudoreplication, and what is n_eff at m = 5, ρ_ICC = 0.3?

**Measurement / oracle.**
9. What are the two oracle signals, and why does an effect need to move at least one?
10. Why is a composite metric dangerous, and what makes the POC admissible anyway?
11. Why must the purple-slop index be validated before it counts as evidence?
12. Why judge every pair in both presentation orders?
13. Why report Gwet's AC1 alongside Krippendorff's α?
14. What is Bradley-Terry, and why add style covariates to it?
15. What is the mediation trap in style control, and how is colorfulness handled?
16. How many judgments distinguish a 60/40 split from a coin? A 65/35?
17. What's the difference between "decisive" and "judged" pairs?

**Interpretability.**
18. What is the residual stream, literally?
19. What is the steering vector, and why does subtracting means isolate "design"?
20. Why is steering-with-no-prompt causal when a high-AUC probe isn't?
21. What does the flip test establish, and how does it work mechanically?
22. Why the norm-matched random control?
23. Why the KL guardrail, and why is behavior non-monotone in the steering strength?
24. Why hold out unseen task types?
25. Why "*a* design direction," never "*the* design direction"?
26. What makes the honest null a finding rather than a failure?

**Answer key.** 1: empty-vs-full confounds design *content* with prompt *mass*
(attention/verbosity/compliance shift with any long block); NEUTRAL holds mass fixed. 2: if "no
purple" hides in C1, ablating C5 doesn't remove all negatives and each Cᵢ isn't attributable to
distinct content; orthogonality makes each component mean one thing. 3: a filler mandating semantic
tags/lang/tag-closure would move axe-core and render-success (families V/A), so the control would
bias the very metrics it anchors — caught in review, fixed with a binding inertness rule +
build-time audit. 4: all 5 main effects + all 10 pairwise interactions estimable from 16 runs, each
aliased only with 3-way+ (assumed negligible) — half the runs, lose only high-order synergy. 5:
LOO=remove-one (necessity, partners present), AOI=add-one (sufficiency, partners absent); they
differ by 2× the interaction load, coinciding only when interactions vanish. 6: C5 hit 104 tokens
because BPE fragments hyphen chains/semicolon lists; widening a preregistered band to fit a
tokenization artifact weakens a frozen rule — fix the text, keep the rule. 7: temp-0.7 gives
seed-to-seed variation the distributional analysis needs; greedy collapses every seed to one output.
8: treating correlated seeds-within-a-prompt as independent understates variance; n_eff =
n/(1+(m−1)ρ) = 200/2.2 ≈ 91. 9: deterministic rendered-DOM metrics + reliability-and-power-gated
human-validated preference; objective metrics cap at ~half the variance in appeal so the preference
is mandatory, and an effect moving neither is null. 10: aggregating invites the garden of forking
paths; safe only because the exact formula, orientation, z-reference, and conditionals are
preregistered before any GPU run. 11: PSI is something we built, so it earns evidence status only if
it correlates ≥0.4 with human "AI-generated" ratings, else the POC drops it. 12: to neutralize
position bias — a winner counts only if consistent across both orders, else it's a tie. 13: under
skew (skill usually wins) α collapses toward 0 even at 90% agreement (kappa paradox); AC1's chance
model shrinks under skew and stays honest; the gate accepts AC1 only when skew is demonstrable. 14:
a chess-Elo latent-strength model fit by logistic regression on paired outcomes; style covariates
subtract the judge's length/colorfulness bias, the analysis twin of the length-matched control. 15:
color *is* a real design lever, so regressing out colorfulness could eat a genuine C1 effect
(controlling a mediator) — colorfulness is flagged partially-causal, reported both ways, and its
legit effect recovered via the objective channel. 16: ~200 decisive pairs for 60/40; ~80 for 65/35
(~780 for 55/45). 17: "decisive" = order-consistent non-tie; the ~200 counts decisive, the
allocation counts judged, and at tie rate t an edge yields (1−t)×judged decisive — don't mis-plug
the marginal gap with a sub-1 discordance rate. 18: the running 3,584-number vector each token
carries through 28 layers, updated by each layer reading a normalized copy and adding its edit back
— a linear read/write channel. 19: mean(skill activations) − mean(neutral); everything the
conditions share ("writing HTML") cancels, leaving the design shift; length-matching makes it
content not instruction-following mode. 20: a probe only shows the info is decodable
(observational); adding the vector with no design prompt *sets* the activation (a do-operation) and
severs its dependence on the prompt, so any gain is caused by the vector — the model was never told
about design. 21: necessity — project v̂ out (P = I − v̂v̂ᵀ) while the skill is present; if the
skill's gain disappears, the direction was load-bearing. 22: to rule out a norm effect — k=5 random
directions of equal magnitude must *not* reproduce the gain, or it's "any big push helps," not a
direction effect. 23: steer too hard and the model leaves its distribution and breaks; cap mean
per-token KL ≤ 0.30 nats so a win can't be bought with gibberish; LayerNorm + downstream
nonlinearity make behavior non-monotone in α. 24: to separate memorizing the extraction corpus from
a transferable mechanism — settings-panels and admin-tables were never in the extraction set. 25:
non-identifiability / concept cones — many behaviorally-equivalent vectors can exist under
single-layer access, so you claim sufficiency/necessity of a direction, never uniqueness. 26: the
power gate certifies the CI is tight enough to exclude the effect the study was designed to detect,
so a preregistered null rules out the strong single-direction account — published with equal rigor.

---

## 8. Honest expectations

### 8.1 The risk surface, in plain terms

- **Stage 2 might not land — and that's an anticipated outcome, not a failure.** Steering directions
  are known to be unreliable and even anti-directional (up to ~50% of inputs can be anti-steerable
  for some concepts), and a clean linear "design direction" may simply not exist in this model. The
  project is explicitly built so that a well-powered null is a publishable result. Realistically,
  hold moderate expectations for the strongest Branch A.1 (sufficient *and* necessary) and be
  genuinely prepared for A.2, C, or B. What is *not* at risk is the rigor of whichever answer comes
  out.
- **The eval stack is where most of the effort is, and it's load-bearing.** The brief's own warning
  is "aesthetic evaluation is a swamp; build and trust the objective metrics first." The bulk of the
  engineering (18 modules, 137 tests, the whole oracle) exists to make the measurement trustworthy.
  If the reliability gate fails (the judge doesn't track humans), there's a preregistered cascade —
  revise the rubric, swap the judge, escalate human labeling, or fall back to objective-only
  decisions — but that's real risk and real work.
- **Colab friction is real.** ~90-minute idle disconnects, session caps, OOM on activation capture.
  The mitigations are all in place (manifest-based resume, checkpoint every 200 units, a batch-size
  ladder, chosen-layers-only capture, 4-bit fallback for generation-only arms) but the GPU phase
  will take patient babysitting.
- **The pilot is the single early gate.** Before spending the generation budget, a 12-generation
  pilot must confirm the model *visibly* applies the skill (FULL ≠ NOSYS on the metrics with a
  visible difference). If it fails after prompt-format fixes, the *only* sanctioned move is the
  model fallback to Llama-3.1-8B — which restarts both stages. That's the one place the whole plan
  could pivot hard.

### 8.2 What's novel vs what's borrowed (credit the lineage)

Be precise about this in an interview — overclaiming novelty is the fastest way to lose a reviewer.

**Genuinely new:** (1) the **first activation-level / steering-vector interpretability of
UI-and-aesthetic code generation** — steering has been applied to text, code capability,
style/persona, and multimodal understanding, but an exhaustive search found no work extracting or
steering a direction for the *visual/aesthetic quality* of generated frontend code; (2) the **first
causal component-ablation of a "design skill"** — every UI benchmark scores models/tools, none
decomposes the *guidance* and attributes quality to components with a two-signal oracle and a
factorial design; (3) the **Stage-1↔Stage-2 correspondence** bridge.

**Borrowed, and must be credited:** the **difference-in-means extraction template** (Arditi et al.'s
refusal-direction work; CAA); **persona/style vectors** (the Persona Vectors paper — which,
importantly, already demonstrated this exact diff-in-means-over-response-tokens-at-middle-layers
recipe on the *same model family*, Qwen2.5-7B-Instruct, which is what de-risks Stage 2's
feasibility); **CAA** (contrastive activation addition, the add-at-all-positions steering method);
the **style-controlled Bradley-Terry** trick (Chatbot Arena); and the **computational-aesthetics**
objective metrics (Ngo balance/symmetry, Hasler colorfulness, the appeal-prediction literature). The
honest framing: the contribution is the **synthesis pointed at a new target** — design skill → UI
code → activations — with the causal rigor (both steering arms, the random control, the honest
failure surface) the brief demands.

### 8.3 What *you* should re-derive or hand-verify to own it

You'll defend this best if you've re-run the load-bearing bits yourself rather than trusting the
docs. Concrete list, roughly in order of value:

1. **Re-derive the necessity/sufficiency identity** (THEORY §T1.4): expand the multilinear model at
   the FULL and LOO-C1 corners, confirm Necessity = 2β₁ + 2Σβ₁ⱼ (+ remainder) and Sufficiency = 2β₁
   − 2Σβ₁ⱼ (+ same remainder), and satisfy yourself that the average is the main effect and the
   half-difference is the interaction load. This one identity is the intellectual spine of Stage 1.
2. **Hand-verify a steering hook** on the tiny-model / mock test (`tests/test_hooks.py`,
   `tests/test_steering.py`): step through `hooks.py` and confirm that "add α·v̂ to the layer
   output" and "project v̂ out via I − v̂v̂ᵀ" do exactly what the math says on a fake decoder layer.
   Owning the plumbing beats trusting it.
3. **Re-run the kappa-paradox cell** (`tests/test_agreement.py` / notebook 03): reproduce α = 0.444
   vs AC1 = 0.878 on the skewed panel and both = 0.80 on the balanced panel by hand, so you can
   explain on a whiteboard *why* raw agreement lies under skew.
4. **Recompute one power number** (THEORY §T6.2): plug the 60/40 split into the one-sample sizing
   formula and get ~194 ≈ 200 yourself. (I did this; it checks.) Do the 65/35 too and you'll own the
   whole 200/80/780 table.
5. **Trace one synthetic-recovery test end to end**
   (`tests/test_synthetic.py::test_stage1_factorial_recovers_interaction`): see how a planted C1×C5
   synergy is injected and then recovered by the real `mixedlm.fit_factorial`. That test *is* the
   argument that the pipeline is trustworthy — internalize it and you can defend "why should I
   believe your GPU numbers" cold.

If you can do those five, you don't just understand this project — you can rebuild the load-bearing
parts from memory, which is the actual bar for defending it.

**Where this lives.** Risk register: `PLAN.md` §VIII.1 and `research/SYNTHESIS.md` §5. Novelty:
`research/SYNTHESIS.md` §6. The derivations and tests to re-run: `THEORY.md` §T1/§T4/§T6,
`tests/test_hooks.py`, `tests/test_steering.py`, `tests/test_agreement.py`,
`tests/test_synthetic.py`.

---

*This companion tracks the frozen state of the plan, the preregistration, and the theory as of the
CPU build. If a GPU-phase amendment forks `prereg-v2`, the affected section here should be updated
alongside it. Everything above is cross-checked against the source documents; where two documents
state a number as a subtotal vs a reconciled total (the ~9 vs ~14 A100-hours; the ~200 decisive vs
judged pairs), the reconciliation is noted inline rather than papered over.*

