# PLAN.md — Anatomy of a Design Skill (Project 19)

**Authoritative, self-contained master plan for both stages.** Every knob has a value; every
procedure has steps; every claim has a decision rule. A competent engineer or a later agent session
executes the entire project from this document with **zero further design decisions**. Binding
governance: `CLAUDE.md` (model lock, compute policy, oracle, commit policy). Decisions: `docs/DECISIONS.md`
(ADR-001…009, all accepted). Evidence: `research/SYNTHESIS.md`, `research/DECISIONS_INPUT.md`, and
`research/notes/**`. Derivations to be mirrored in `THEORY.md` (Part VII). Freeze document:
`PREREGISTRATION.md`. Citations are BibTeX keys in `research/refs.bib`.

> **Compute reality (CLAUDE.md).** No GPU / no Qwen inference runs in this environment. All
> GPU-dependent code is written, mocked/unit-tested, import-guarded, and left **unexecuted**; it runs
> later on Colab Pro/Pro+ per `RUNBOOK.md`. Everything CPU-safe (rendering fixtures, the metric
> stack, judge dry-run, statistics on synthetic data, all unit tests) actually runs and passes here.

---

# PART 0 — Executive summary & reading map

## 0.1 The project in one paragraph
LLMs produce better UIs when given a short "frontend-design skill." Everyone reports the effect;
nobody has measured it. We measure it in two committed stages on **one** open-weights model,
`Qwen/Qwen2.5-Coder-7B-Instruct` (ADR-001), so that "which instruction matters" (Stage 1) and "where
it lives inside the model" (Stage 2) describe the *same system*. **Stage 1** is a black-box factorial
ablation of a five-component design skill (necessity, sufficiency, interactions). **Stage 2** is
white-box mechanistic interpretability: locate the skill's signal in the residual stream, extract a
diff-in-means "design direction," and **causally verify** it by steering the model with **no design
prompt** on held-out prompts, including task types never seen during development.

## 0.2 The correctness oracle (non-negotiable; CLAUDE.md, BRIEF §"Correctness oracle")
Every quality claim — an ablation delta **or** a steering delta — requires **two independent
signals**:
1. **Objective metrics on the rendered output** (headless Chromium, rendered DOM + screenshot,
   never raw code strings): render-success/hermeticity, WCAG contrast distribution, axe-core
   violations, overflow/overlap counts, Ngo layout regularity/balance, white-space, typography-scale
   consistency, Hasler colorfulness, dominant-color count, visual complexity, and a validated
   **purple-slop index**. Deterministic and unfoolable.
2. **A pairwise preference protocol** (VLM judge, human-validated subset) gated behind
   chance-corrected inter-rater agreement (Krippendorff α / Gwet AC1) **and** a power check, and
   analyzed with a style-controlled Bradley-Terry model.

**Null rule (preregistered, verbatim):** *An ablated component's effect, or a steering direction's
effect, is reported as null unless it moves an objective-metric endpoint (Part III §3.6 decision) OR
a preference delta that passes both the reliability gate and the power gate. Aesthetic claims not
backed by the objective half are inadmissible.* **Stage-2 bar:** a "design direction" is real only if
steering it with no design prompt causally reproduces a measurable quality gain on held-out prompts.

## 0.3 Headline hypotheses
- **H-skill:** FULL ≫ NEUTRAL on both signals (the skill works and it is *content*, not prompt mass).
- **H-necessity (RQ1):** at least one component is necessary — removing it (LOO) degrades quality;
  we expect **C5 (negatives)** and **C1 (color)** to punch above their token weight (`SYNTHESIS` §1.9).
- **H-sufficiency (RQ2):** no single component alone (AOI) reproduces the full effect; sufficiency is
  distributed.
- **H-additivity (RQ3):** components are largely additive with a few super/sub-additive pairs
  (e.g. negatives help more once a palette is specified).
- **H-nudge (RQ4):** FULL > BEAUTY1 > NEUTRAL — 391 tokens of content beat a 5-word nudge, which
  beats nothing.
- **H-locate (RQ5):** the skill signal is linearly decodable and patch-localizable in a mid-depth
  band (layers ≈ 11–20 of 28; `chen2025persona`, `rimsky2024caa`).
- **H-steer (RQ6):** a mid-layer diff-in-means direction, added with no prompt, reproduces a
  *measurable fraction* of the skill's quality gain on held-out prompts.
- **H-fail (RQ7):** steering generalizes to unseen task types but with a nonzero anti-steerable
  fraction and dose-response non-monotonicity (`tan2024analysing`, `taimeskhanov2026strength`).
- **H-correspond (RQ8, stretch):** component sub-vectors are near-orthogonal and each steers *its
  own* metric family (`park2024geometry`).

Every hypothesis has an explicit **honest-null branch** (Part I) that is a first-class, publishable
outcome — the brief and CLAUDE.md require nulls be reported, never forced.

## 0.4 Repo map (grows as built)
```
docs/BRIEF.md            original brief (do not edit)
docs/DECISIONS.md        ADR-001…009 (accepted)
CLAUDE.md                governance (model lock, compute, oracle, commit policy)
PLAN.md                  ← this file (authoritative plan, both stages)
PREREGISTRATION.md       frozen hypotheses, cell table, endpoints, gates, null rule (git-tagged pre-GPU)
THEORY.md                derivations (DOE, MixedLM, α/AC1, BT, power, diff-in-means, do-calculus)
RUNBOOK.md               Colab session-by-session execution (GPU phase)
SEAN-README.md           plain-language companion
research/                literature dossier (SYNTHESIS, DECISIONS_INPUT, notes/**, refs.bib)
research/skill_exemplars/canonical_skill_v1.md   the frozen independent variable (Part II)
src/                     Python package (config, skill_assembly, prompts, generation_vllm,
                         generation_hf, hooks, activations, steering, rendering, metrics_dom,
                         metrics_visual, judge, agreement, bt_model, mixedlm, power, figures, manifest)
notebooks/               DS-lifecycle notebooks (import src/; unexecuted GPU cells marked)
paper/                   two-part paper scaffold with outcome-contingent templates
config/                  YAML configs (skill, prompts, cells, sampling, steering grids, judge)
artifacts/               HTML, screenshots, activations (gitignored, manifest-tracked)
results/                 JSONL/Parquet (generations, metrics, judgments, steering runs)
```

## 0.5 Execution-order dependency graph (which phase blocks which)
```
                         ┌─────────────────────────────────────────────┐
   CPU-NOW (this env)    │ src/ machinery + tests + CPU execution      │  (ADR-007)
                         │  rendering ▸ metrics_dom ▸ metrics_visual ▸  │
                         │  judge(dry-run) ▸ agreement ▸ bt_model ▸     │
                         │  mixedlm ▸ power ▸ figures(synthetic)        │
                         └───────────────┬─────────────────────────────┘
                                         │ (all green)
                                         ▼
   FREEZE ────────────────────► PREREGISTRATION.md  (git tag prereg-v1)  ── blocks all GPU work
                                         │
                                         ▼
   GPU P0  ── Pilot (gate zero, §III.9) ── PASS ─┐   FAIL → fix prompt format → re-pilot →
                                                 │           (only trigger for ADR-001 fallback)
                                                 ▼
   GPU P1  ── Stage-1 generation (vLLM) ── 4,630 gens
                                         │
                                         ▼
   CPU P2  ── render + objective metrics (CPU, local) ── metrics tables
                                         │
                                         ▼
   API P3  ── judging (Gemini Flash) + human subset + reliability gate ── BT utilities
                                         │
              ┌──────────────────────────┴─────────────────┐
              ▼ (Stage-1 analysis: RQ1–RQ4, RQ7 black-box)  │ reuse FULL/NEUTRAL dev gens
   ANALYSIS  MixedLM + style-controlled BT + Holm/BH         ▼
                                              GPU P4  Stage-2 extraction (HF fwd) ── S2.0–S2.2 (RQ5)
                                                         │
                                                         ▼
                                              GPU P5  dev sweep (HF) ── S2.3 → freeze (ℓ*,α*,variant)
                                                         │
                                                         ▼
                                              GPU P6  held-out causal verify + flip + specificity
                                                         (S2.4–S2.7, RQ6–RQ7)
                                                         │
                                                         ▼
                                              GPU P7  stretch: correspondence S2.8 (RQ8) + early-token S2.9
                                                         │
                                                         ▼
                                              P8  evaluation + figures + paper (Part V)
```
**Hard blocks:** PREREGISTRATION tag blocks all GPU. Pilot PASS blocks P1. P1 blocks P2 blocks P3.
Stage-1 FULL/NEUTRAL generations (P1) are *reused* as the Stage-2 extraction corpus (P4). The dev
sweep (P5) must **freeze** `(ℓ*, α*, variant)` before any held-out generation (P6) — held-out is
touched exactly once, for confirmatory causal verification.

---

# PART I — Problem framing (lifecycle phase 1)

Each RQ states: **hypothesis · measurement · decision rule · outcomes (incl. honest null)**. The
primary preference endpoint is the style-controlled Bradley-Terry utility (Part III §3.5); the
primary objective endpoint is the Primary Objective Composite (POC) plus the family-wise objective
decision (Part III §3.6). "Reliability-gated" = the α/AC1 gate of §III.8 passed; "powered" = the
McNemar power gate of §III.7 met.

## RQ1 — Component necessity
- **Hypothesis H1ᵢ (i∈{1..5}):** removing component Cᵢ from the full skill lowers UI quality:
  `μ(FULL) − μ(LOO-Cᵢ) > 0`.
- **Measurement:** the paired contrast FULL vs LOO-Cᵢ, on (a) POC via MixedLM and (b) preference via
  style-controlled BT, on dev prompts; replicated on held-out.
- **Decision rule:** Cᵢ is **necessary** if the FULL−LOO-Cᵢ effect is positive and significant after
  **Holm** correction across the confirmatory family (§III.6) on the POC, **OR** the BT preference
  delta is reliability-gated, powered, and its cluster-bootstrap 95 % CI excludes 0. Rank components
  by necessity effect size (standardized δ, §III.6).
- **Outcomes:** {necessary (ranked) · null (moves neither signal) · **negative** (removing Cᵢ
  *improves* quality — reported honestly, e.g. an over-constraining component)}.

## RQ2 — Component sufficiency
- **Hypothesis H2ᵢ:** Cᵢ alone lifts quality above neutral: `μ(AOI-Cᵢ) − μ(NEUTRAL) > 0`; and no
  single Cᵢ reaches FULL: `μ(AOI-Cᵢ) < μ(FULL)`.
- **Measurement:** AOI-Cᵢ vs NEUTRAL (lift) and AOI-Cᵢ vs FULL (gap), both signals.
- **Decision rule:** Cᵢ is **sufficient-partial** if AOI-Cᵢ−NEUTRAL is positive/significant
  (Holm, POC) or reliability+power-gated (preference). **Sufficiency is distributed** if no AOI-Cᵢ
  reaches within a preregistered 30 % of the FULL−NEUTRAL gap on the POC.
- **Outcomes:** {one component carries most of the effect · effect is distributed across components ·
  null (no component alone helps)}.

## RQ3 — Interactions / additivity
- **Hypothesis H3:** component effects are **not** purely additive; specific two-factor interactions
  (2FIs) are non-zero (super- or sub-additive).
- **Measurement:** the 2⁵⁻¹ resolution-V fraction (§III.2) estimates all five main effects and all
  ten 2FIs cleanly on each objective metric via a factorial MixedLM (§III.6).
- **Decision rule:** additivity is **rejected** for a pair (Cᵢ,Cⱼ) if its 2FI coefficient is
  significant after **BH** (FDR = 0.10) on the POC and concordant on ≥1 other family. Report the
  interaction heatmap (F3).
- **Outcomes:** {additive (no surviving 2FIs) · interacting (named pairs, sign) · dominated by a
  single strong main effect}.

## RQ4 — Does 5 words ≈ 391 tokens?
- **Hypothesis H4:** `μ(FULL) > μ(BEAUTY1) > μ(NEUTRAL)`.
- **Measurement:** the ordered contrasts FULL vs BEAUTY1, BEAUTY1 vs NEUTRAL, FULL vs NEUTRAL, both
  signals.
- **Decision rule:** "content matters beyond a nudge" if FULL−BEAUTY1 > 0 (Holm/POC or gated
  preference); "a nudge suffices" if BEAUTY1 reaches within 30 % of the FULL−NEUTRAL gap and
  FULL−BEAUTY1 is null.
- **Outcomes:** {structured skill content is load-bearing · a one-liner captures most of it · neither
  beats neutral (the model can't use aesthetic guidance at all — escalates to the pilot fallback if
  seen at pilot)}.

## RQ5 — Where does the effect live in activations?
- **Hypothesis H5:** the FULL-vs-NEUTRAL signal is linearly decodable and patch-localizable in a
  contiguous **mid-depth band** (≈ layers 11–20).
- **Measurement:** per-layer linear-probe AUC with control-task selectivity (`hewitt2019control`);
  per-layer diff-in-means norm/‖v_l‖ and cosine structure; denoising activation patching
  neutral→skill with a design-token logit-diff proxy (§IV S2.1).
- **Decision rule:** the **chosen band** = the maximal contiguous set of layers where probe AUC ≥ 0.80
  **and** selectivity ≥ 0.15 **and** patching recovers ≥ 25 % of the clean–corrupted gap. If no band
  meets all three, widen to a single peak layer and flag "diffuse."
- **Outcomes:** {localized band (feeds Stage-2 focus layers) · diffuse/no clean peak (steering may
  need multi-layer injection; honest report)}.

## RQ6 — Does a diff-in-means direction causally reproduce the gain with no prompt? *(the hard bar)*
- **Hypothesis H6:** with **no design prompt** (NOSYS base), adding `α*·v̂_{ℓ*}` at layer ℓ* raises
  held-out quality on both oracle signals.
- **Measurement:** the S2.4 held-out arms {unsteered-NOSYS, steered-NOSYS, norm-matched-random,
  FULL-skill reference}, both signals; the % of the skill effect reproduced.
- **Decision rule (Stage-2 success, preregistered):** steered beats unsteered on **≥1 objective
  family after Holm** AND a **reliability-gated preference delta** (BT CI > 0), **AND** the
  norm-matched random control does not achieve both, **AND** the flip test (RQ, S2.5) attenuates the
  skill's gain. If addition succeeds but the flip test does not, report "causally **sufficient**, not
  demonstrably necessary."
- **Outcomes:** {a causally sufficient (and/or necessary) design direction exists · a correlational
  direction that does not steer (honest null: design behavior is not linearly steerable / is
  distributed — a legitimate result per BRIEF)}.

## RQ7 — Failure surface & generalization
- **Hypothesis H7:** steering helps on average out-of-distribution (unseen task types) but with a
  nonzero anti-steerable fraction and a non-monotonic dose-response.
- **Measurement:** per-prompt and per-task-type steering deltas (both signals); anti-steerable
  fraction = share of held-out prompts whose steered POC < unsteered POC; dose-response curve over
  the α grid with render-success shading; break-mode taxonomy of where HTML breaks.
- **Decision rule:** "generalizes" if the mean held-out **unseen-type** delta > 0 (gated) and the
  anti-steerable fraction < 50 % (`tan2024analysing` boundary). Report the honest failure map (F7,
  F12) regardless.
- **Outcomes:** {robust · partial (helps some types, breaks others) · brittle (OOD collapse)}.

## RQ8 — Component ↔ direction correspondence *(stretch, planned)*
- **Hypothesis H8:** component sub-vectors `v_{Cᵢ}` (from AOI-Cᵢ vs NEUTRAL activations) are
  **near-orthogonal** and each steers *its own* metric family (v_C1 moves palette metrics, not
  spacing; etc.), mirroring the Stage-1 ablation signatures.
- **Measurement:** the cosine matrix among {v_C1…v_C5} and with v_full; per-sub-vector steering
  metric-signature vs the component's Stage-1 ablation metric-signature (cosine of signature vectors).
- **Decision rule:** **correspondence found** if mean |cos(v_Cᵢ,v_Cⱼ)| < 0.3 (near-orthogonal) AND
  ≥3 of 5 sub-vectors produce a steering signature whose argmax family equals the component's
  ablation-signature argmax family; **partial** if 1–2 match; **absent** otherwise.
- **Outcomes:** {clean correspondence (the paper's strongest result) · partial · absent (design is
  one entangled direction, not a component basis — still informative)}.

**Cross-cutting honest-null policy.** Any RQ resolving to null is written up with (a) the effect-size
estimate and CI showing the null is *tight* (not merely underpowered — the power gate distinguishes
these), (b) the objective-signal evidence, and (c) the interpretation. Per CLAUDE.md and BRIEF, a
clean null (skill component X does nothing; the design direction does not steer) is a legitimate,
reported finding.

---

# PART II — Data design (lifecycle phases 2–3)

## II.1 The skill (independent variable) — FINAL canonical_skill v1 (ADR-009)

The frozen text is `research/skill_exemplars/canonical_skill_v1.md`, reproduced here in full so
PLAN is self-contained. **ADR-009 is implemented:** C1–C4 are **purely prescriptive**; **all**
negative constraints are consolidated in **C5**; components are token-balanced within ±15 %.

### II.1.1 The five components (tags `[[Cn]]` stripped before use; order fixed C1→C5)

**C1 — Color / palette** *(prescriptive only)*
> Choose a deliberate palette of four to six specific colors — one dominant hue, one or two
> supporting tones, and one sharp accent — each fixed as an exact hex value and reused consistently
> throughout. Build depth with atmospheric, layered backgrounds such as subtle tints, soft shading,
> or fine texture rather than flat fills, and ensure every text-on-background pairing clears WCAG AA
> contrast.

**C2 — Layout / spacing / hierarchy** *(prescriptive only)*
> Open with the most characteristic element of the subject so the page announces what it is at a
> glance. Establish a clear visual hierarchy on a consistent spacing scale, aligning elements to a
> small set of shared edges so the composition reads as engineered. Favor intentional, sometimes
> asymmetric arrangements over uniform grids, and give the layout generous, purposeful white space
> so it can breathe.

**C3 — Typography** *(prescriptive only)*
> Pair a characterful display typeface, used sparingly for headings, with a clean, highly readable
> body typeface and a compact utility face for small labels and data. Set a clear modular type scale
> with a few deliberate sizes and weights, and let the typography carry real personality — expressive
> at large sizes, quietly legible at small ones — instead of neutrally delivering text.

**C4 — Component patterns** *(prescriptive only)*
> Design one well-chosen signature element — an unexpected section, a distinctive card treatment, or
> a considered navigation — that anchors the page's identity. Add at most one orchestrated motion
> moment, such as a single page-load reveal or a refined hover state, and make it feel deliberate.
> Vary corner radii, borders, and shadows with intent so that depth and emphasis track the
> importance of the content.

**C5 — Negative constraints** *(ALL negatives, ADR-009)*
> Avoid AI slop defaults: purple or indigo gradients; Inter and Roboto typefaces; fully centered
> hero layouts built around one big headline and stat; three identical icon cards in a row; uniform
> rounded corners on everything; and scattered or excessive animation. Never default to generic
> template palettes or cream with terracotta serif and near black with acid green looks, unless the
> brief calls for them. Cut any decoration that serves no purpose.

### II.1.2 Final token counts and the ±15 % rule
Target ≈ **85 tokens/component** (nominal); full skill = **391 exact tokens** (nominal ≈ 425).
Counts are measured **exactly** with the `Qwen2.5-Coder` tokenizer (recorded in the manifest); the
words × ≈1.33 estimate (whitespace-split) is the documented fallback when the tokenizer is
unavailable. The ±15 % band is around the observed mean of the five exact counts
(**m = 78.2 → band [66.5, 89.9]**):

| Component | words | est. tokens | exact Qwen tokens | in ±15 % of m? |
|---|---:|---:|---:|:--:|
| C1 color | 63 | ~84 | 75 | ✓ |
| C2 layout | 64 | ~85 | 73 | ✓ |
| C3 typography | 62 | ~82 | 75 | ✓ |
| C4 patterns | 65 | ~86 | 80 | ✓ |
| C5 negatives | 71 | ~94 | 88 | ✓ |

*Pre-freeze revision (sanctioned):* C5 was reworded before the `prereg-v1` tag — the original
phrasing measured **104 exact tokens** (~28 % over the mean) because BPE fragments semicolon lists
and long hyphen chains (`cream-and-terracotta-serif` = 7 tokens) that the ×1.33 estimate masked.
All semantic constraints preserved (six slop tells, generic template palettes, both named looks,
the escape clause, the cut-purposeless-decoration rule); hyphen chains broken into BPE-friendly
phrasing. `research/skill_exemplars/canonical_skill_v1.md` §2 carries the same table and note.

`src/skill_assembly` **asserts** `0.85·m ≤ len(Cᵢ) ≤ 1.15·m` (m = mean); pads short components with a
trailing clause from the matched filler, trims long ones at a sentence boundary. Hard unit test.

### II.1.3 Neutral filler pool + LOO padding rule
Five design-irrelevant **source-hygiene** blocks, each **token-length-matched to the component it
replaces** (Filler-i ↔ Cᵢ). The rule and filler texts below are **verbatim-identical** to
`canonical_skill_v1.md` §3 (enforced by a unit test that diffs the two).

**Filler inertness rule (binding).** Fillers must be design-irrelevant AND **render-inert**: a filler
may not mandate anything that changes the rendered DOM tree, the choice of elements or attributes, or
the render outcome — nothing any objective metric could detect (semantic landmarks, `html-has-lang`,
`document-title`, tag closure, and event-handler attributes are all visible to axe-core or the
render-success gate in families V/A, so mandating them would let fillers move the oracle). Allowed
filler topics: source formatting (indentation, line width, blank lines), comment style and placement,
naming conventions for classes/ids/variables, CSS declaration ordering/grouping within rules, and JS
source organization (small single-purpose functions, `const`/`let`, declaration order). This
render-inertness restriction deliberately tightens ADR-003's illustrative "code hygiene" examples
(semantic tags and event-handler style are metric-visible, so they are excluded here).
`src/skill_assembly` runs a build-time **filler audit**, parallel to the prompt leakage audit: assert
zero case-insensitive whole-word matches in any filler of the banned-topic term list — semantic/
structural element mandates (header, nav, main, footer, aside, article, section, landmark, semantic),
document metadata (lang, title, meta), ARIA/accessibility, validation and tag closure (valid,
validate, validation, well-formed, closed, closure, unclosed, lint, linter), event attachment
(addEventListener, onclick, handler, event), and error/exception guarding — hard unit test
(`config/skill.yaml: filler_banned_topics`).

**Filler-1** (↔C1): Write the markup in a consistent source style: use lowercase for tag and
attribute names, quote every attribute value with double quotes, and keep a stable attribute order
within each tag. Break long lines at a consistent indent so no line grows unwieldy, and keep quoting
and casing choices uniform across the whole file so the source reads cleanly.

**Filler-2** (↔C2): Indent the markup consistently with two spaces per level and keep lines to a
reasonable width so the source stays legible. Group related rules together, order the CSS
declarations predictably, and leave a short comment above each major part of the stylesheet
describing what it styles. Avoid trailing whitespace and keep a single blank line between logical
blocks.

**Filler-3** (↔C3): Name classes and identifiers with clear, lowercase, hyphen-separated words that
describe purpose rather than appearance, and keep the naming scheme consistent across the file.
Avoid abbreviations that are not obvious, do not reuse one name for two purposes, and prefer a
short, stable vocabulary of names over inventing a new term for every element on the page.

**Filler-4** (↔C4): Organize any JavaScript into small, single-purpose functions with descriptive
names, each declared before the point where it is used, and keep the logic shallow rather than
deeply nested. Prefer const and let over var, keep variable declarations near their first use, group
related functions together in the script, and leave a brief comment explaining any step whose intent
is not obvious.

**Filler-5** (↔C5): Comment the code where intent is not obvious, but avoid restating what the code
plainly does; a good comment explains why, not what. Keep comments short, place each one directly
above the line or block it describes, and use a consistent comment style throughout. Remove
commented-out fragments and leftover notes to self before finishing, so only purposeful comments
remain in the final file.

**Filler token counts** (exact Qwen tokenizer, words × ≈1.33 as fallback; enforced at build time
against the matched component's token count): raw F1 67 t (C1 75); F2 65 t (C2 73); F3 69 t
(C3 75); F4 71 t (C4 80); F5 75 t (C5 88) — every raw filler within ±15 % of its matched component;
all equally imperative in mood. Build-time equalization (below) then makes the match exact:
equalized F1 75, F2 74, F3 76, F4 81, F5 87 — each within ±2 tokens of its component.

**Padding pool (frozen; build-time equalization).** `src/skill_assembly.equalize_fillers` makes the
length match exact at build time: each Filler-i is deterministically padded (appending pool clauses
in the fixed order below, skipping any that would overshoot) or trimmed (at sentence boundaries
only) until |tokens(Fᵢ) − tokens(Cᵢ)| ≤ 2 under the exact Qwen2.5-Coder tokenizer; per-filler final
counts are recorded in the manifest. Pool clauses are render-inert, imperative, on-topic for their
filler, and pass the same banned-topic audit as the fillers.

**Pad-1a** (↔F1): Apply the same wrapping style to every long tag so no line stands out.

**Pad-1b** (↔F1): Break attribute lists at a consistent width.

**Pad-1c** (↔F1): Keep tag casing uniform throughout.

**Pad-2a** (↔F2): Keep spacing between rule blocks even so the stylesheet reads in a steady rhythm.

**Pad-2b** (↔F2): Order declarations the same way in every rule.

**Pad-2c** (↔F2): Keep rule blocks tidy and short.

**Pad-3a** (↔F3): Prefer plain descriptive words over clever coinages when a name must be introduced.

**Pad-3b** (↔F3): Keep names short, plain, and easy to scan.

**Pad-3c** (↔F3): Keep the vocabulary of names small.

**Pad-4a** (↔F4): Group constants near the top of the script so their values are easy to locate.

**Pad-4b** (↔F4): Keep the script's functions in one predictable order.

**Pad-4c** (↔F4): Prefer flat logic over nesting.

**Pad-5a** (↔F5): Delete stale comments rather than letting them drift out of date.

**Pad-5b** (↔F5): Keep comment punctuation simple and consistent.

**Pad-5c** (↔F5): Prefer one clear comment over three vague ones.

**Padding rule:** in LOO-Cᵢ, Filler-i occupies Cᵢ's original slot; in AOI-Cᵢ, the other four slots
hold their fillers. Thus every factorial cell (16 res-V runs + 5 LOO) has **constant prompt mass —
FULL = 391 exact Qwen2.5-Coder tokens, every cell within ±10 of it after filler equalization
(≈425 nominal on the estimate path) — and constant slot order**; only content varies.
**NEUTRAL = Filler-1‖…‖Filler-5** = the all-filler `(−,−,−,−,−)` corner.

### II.1.4 Constant output constraint (never ablated; in the USER turn)
Appended verbatim to every task prompt in all cells including NOSYS:
> "Return a single self-contained HTML file: put all CSS in one `<style>` tag and all JavaScript in
> one `<script>` tag, inline, with no external network requests — no external fonts, stylesheets,
> scripts, images, or CDNs. Use only system or generic fonts, and inline SVG or CSS for any graphics.
> Output only the HTML file."

Placing it in the user turn keeps hermeticity enforced even when there is no system prompt (NOSYS).

### II.1.5 Prompt assembly (ChatML)
`tokenizer.apply_chat_template` with roles: **system** = {skill | fillers | beauty line | absent},
**user** = task brief + output constraint. NOSYS omits the system message entirely (not an empty
string). Recorded per generation in the results schema (`system_variant`, `cell_id`).

## II.2 Prompt set (the corpus)

**Design (D11).** 10 task types; 58 prompts; realistic briefs describing *domain and function* only;
difficulty tags E(easy)/M(medium)/H(hard) by element count and interaction complexity.

**Leakage-audit rule (mechanical).** Case-insensitive **whole-word** matching (regex `\b…\b`) of the
frozen `banned_words` list against the 58 task briefs. **Scope** = the user-turn brief text only —
the constant output constraint and the system-prompt cell texts are excluded (the latter *are* the
manipulated variable; BEAUTY1 deliberately contains design directives). **Rationale:** the list bans
*style adjectives/directives and design-family words* that would leak design guidance into the task
prompt, so the system-prompt treatment is the only design signal in context; domain and occupational
nouns are otherwise permitted. `banned_words` = {beautiful, modern, clean, sleek, elegant,
minimalist, aesthetic, stylish, polished, premium, vibrant, colorful, gradient, purple, gorgeous,
stunning, slick, professional-looking, cutting-edge, design, designer, designed, redesign} — zero
whole-word matches in the frozen corpus below.

**Split (frozen by id).** **Dev = 40** (8 development types × 5). **Held-out = 18** = 8 "within-seen-
type" prompts (1 per development type) + **10 "unseen-type"** (2 OOD types × 5). The two OOD types —
**settings-panel (ST)** and **admin-data-table (AT)** — are entirely absent from dev. *Why these two:*
they are control-dense / information-dense layouts structurally unlike the marketing- and content-
oriented development types; they stress the skill's layout/hierarchy guidance in a regime it was not
tuned on, giving a genuine out-of-distribution generalization test for steering
(`tan2024analysing` OOD; D11).

### II.2.1 Full prompt table (id · type · text · difficulty · split)
All briefs implicitly carry the constant output constraint (II.1.4).

| id | type | prompt text | diff | split |
|---|---|---|---|---|
| L01 | landing | Landing page for a mobile app that tracks home water usage and flags leaks; headline, how-it-works, three feature highlights, download call. | E | dev |
| L02 | landing | Landing page for a regional apple-cider producer selling seasonal boxes; product story, what's in a box, delivery areas, order button. | M | dev |
| L03 | landing | Landing page for a B2B API that turns shipping documents into structured data; hero statement, integration steps, a code sample, request-access form. | H | dev |
| L04 | landing | Launch page for an independent documentary about deep-sea mining; synopsis, trailer placeholder, screening dates, newsletter signup. | H | dev |
| L05 | landing | Landing page for a neighborhood bicycle-repair co-op; hours, services, a pricing note, location. | E | dev |
| L06 | landing | Landing page for a language-exchange meetup pairing learners for weekly conversation; how pairing works, supported languages, join button. | M | held(seen) |
| D01 | dashboard | Dashboard for a solar-panel owner; today's generation, home consumption, battery level, 7-day history chart placeholder. | M | dev |
| D02 | dashboard | Operations dashboard for a bike-share system; station occupancy, bikes in transit, low-battery e-bikes, alerts list. | H | dev |
| D03 | dashboard | Personal-finance dashboard; account balances, monthly spending by category, upcoming bills, savings-goal tracker. | M | dev |
| D04 | dashboard | Dashboard for a small warehouse; inventory by aisle, orders awaiting pick, staff on shift, throughput chart placeholder. | H | dev |
| D05 | dashboard | Dashboard for a habit-tracking app; streaks for four habits, a weekly completion grid, today's checklist. | E | dev |
| D06 | dashboard | Fleet dashboard for a delivery company; vehicles active, deliveries completed, fuel usage, map placeholder with status pins. | M | held(seen) |
| F01 | form | Multi-step signup form for a coding bootcamp; personal details, program choice, payment plan, progress indicator. | E | dev |
| F02 | form | Grant-application form for a community arts fund; applicant info, project description, budget table, file-upload fields. | M | dev |
| F03 | form | Booking form for a pottery studio; class selection, date and time, seats, contact details. | M | dev |
| F04 | form | Renters-insurance quote form; address, coverage options, valuables to insure, a summary step before submitting. | H | dev |
| F05 | form | Contact form for a wedding photographer; names, event date, venue, package interest, message. | E | dev |
| F06 | form | Patient-intake form for a dental clinic; personal and insurance details, medical-history checkboxes, consent. | M | held(seen) |
| P01 | pricing | Pricing page for a note-taking app; three tiers (free/personal/team), monthly-annual toggle, feature comparison. | E | dev |
| P02 | pricing | Pricing page for a car-wash membership; three plans, what each includes, an FAQ section. | M | dev |
| P03 | pricing | Pricing page for a freelance illustrator; service packages, add-ons, turnaround times, booking link. | M | dev |
| P04 | pricing | Pricing page for a cloud-storage service; usage-based tiers, an interactive cost estimate, enterprise contact option. | H | dev |
| P05 | pricing | Pricing page for a yoga studio; drop-in, class packs, unlimited monthly, a short note on each. | E | dev |
| P06 | pricing | Pricing page for a project-management tool; four plans across a long feature matrix with category groupings. | M | held(seen) |
| PF01 | portfolio | Portfolio home for a furniture maker; project grid, short bio, contact details. | E | dev |
| PF02 | portfolio | Portfolio for a film-score composer; reel placeholder, selected credits, a list of instruments and tools used. | M | dev |
| PF03 | portfolio | Portfolio for an architecture studio; three built projects with descriptions, a studio statement. | M | dev |
| PF04 | portfolio | Portfolio for a data journalist; long-form interactive pieces, each with a synopsis and a role note. | H | dev |
| PF05 | portfolio | Portfolio for a tattoo artist; a gallery, studio location, a booking enquiry link. | E | dev |
| PF06 | portfolio | Portfolio for a motion-graphics freelancer; work organized into categories, a short about section. | M | held(seen) |
| B01 | blog | Article page about restoring a vintage typewriter; headings, image placeholders, an author note. | E | dev |
| B02 | blog | Blog index for a gardening site; recent articles by season, tags, a search field. | M | dev |
| B03 | blog | Long-form article on the history of the tea trade; table of contents, pull quotes, footnotes. | M | dev |
| B04 | blog | Magazine-style feature profiling a wildlife photographer; full-width imagery placeholders mixed with narrative columns. | H | dev |
| B05 | blog | Blog post reviewing three noise-cancelling headphones; a verdict box, pros and cons. | E | dev |
| B06 | blog | Recipe article for a sourdough loaf; ingredients, step-by-step method, timing notes. | M | held(seen) |
| E01 | ecommerce | Product page for a stainless-steel water bottle; image gallery, price, size and color options, add-to-cart. | E | dev |
| E02 | ecommerce | Product page for a mechanical keyboard; switch options, specifications, reviews summary, related products. | M | dev |
| E03 | ecommerce | Product listing for a bookstore's staff picks; filters by genre, sort options, a grid of titles. | M | dev |
| E04 | ecommerce | Configurator page for a made-to-order desk; material, dimensions, cable options, live price, order. | H | dev |
| E05 | ecommerce | Product page for single-origin coffee; roast details, tasting notes, grind selection, subscribe option. | E | dev |
| E06 | ecommerce | Product listing for a plant nursery; filtered by light and care level, each card showing name and price. | M | held(seen) |
| A01 | auth | Login screen for a budgeting app; email and password, remember-me, reset-password link. | E | dev |
| A02 | auth | Registration screen for a co-working booking site; email, password-strength meter, terms acceptance. | M | dev |
| A03 | auth | Two-factor screen prompting for a six-digit code; resend option, a help note. | M | dev |
| A04 | auth | Account-recovery flow screen; multiple verification methods, explanation of what happens next. | H | dev |
| A05 | auth | Sign-in for a library catalog; card number and PIN, a guest-access option. | E | dev |
| A06 | auth | Single-sign-on chooser screen; pick an organization before continuing to log in. | M | held(seen) |
| ST01 | settings | Settings page for a chat app; notifications, privacy, appearance, connected devices, using labeled toggles and selects. | M | held(unseen) |
| ST02 | settings | Account settings for a streaming service; profile, subscription, playback quality, parental controls, downloads. | H | held(unseen) |
| ST03 | settings | Workspace settings for a team tool; members, roles and permissions, billing, integrations. | M | held(unseen) |
| ST04 | settings | Notification-preferences page; choose channels (email/push/SMS) per category, a save bar. | E | held(unseen) |
| ST05 | settings | Device settings for a smart thermostat; schedules, temperature units, eco mode, sensor calibration. | H | held(unseen) |
| AT01 | admin-table | Admin users table; name, email, role, status, last-active columns, search, row actions. | M | held(unseen) |
| AT02 | admin-table | Admin orders table; filterable columns, status badges, bulk selection, pagination, detail-drawer trigger. | H | held(unseen) |
| AT03 | admin-table | Admin content-moderation queue; reported items with reason, reporter, date, approve/remove actions. | M | held(unseen) |
| AT04 | admin-table | Admin inventory table; SKU, product, stock, price, an edit action per row, a filter bar. | E | held(unseen) |
| AT05 | admin-table | Admin analytics table; campaigns with sortable metric columns, sparkline placeholders, an export control. | H | held(unseen) |

**Split freeze (by id).**
- **Dev (40):** L01–L05, D01–D05, F01–F05, P01–P05, PF01–PF05, B01–B05, E01–E05, A01–A05.
- **Held-out seen-type (8):** L06, D06, F06, P06, PF06, B06, E06, A06.
- **Held-out unseen-type (10):** ST01–ST05, AT01–AT05.

**Leakage audit procedure (run in `src/prompts` as a test):** assert zero case-insensitive
whole-word matches of `banned_words` (`config/prompts.yaml`) over every brief; assert each brief
names a concrete domain and ≥3 functional sections; a second reviewer sign-off is recorded in the
manifest. Frozen in PREREGISTRATION.

## II.3 Seeds & sampling

**One fixed sampling config (all cells, both engines; recorded per run).**
`temperature = 0.7`, `top_p = 0.9`, `top_k = 40`, `repetition_penalty = 1.05`,
`max_new_tokens = 4096`, `seed ∈ {0,1,2,3,4}`.
- *Rationale.* Single-file HTML runs ≈2–4k tokens (`03_colab_feasibility`), so 4096 covers it.
  Temperature 0.7 (nucleus 0.9) gives genuine seed-to-seed variation so the ≥3-seed distributional
  analysis has signal; **greedy (T=0) would collapse seeds to one output**, defeating the seed
  discipline and the MixedLM's seed random effect. 0.7/0.9 is the standard "creative-but-coherent"
  setting for code/UI generation and keeps render-success high. Same config on vLLM (Stage-1) and HF
  (Stage-2); engine + version + config hashed into every row (ADR-002).

**Seed allocation (which cells are "headline").**
- **Headline cells → 5 seeds** {0..4}: the 4 controls (FULL, NEUTRAL, BEAUTY1, NOSYS) + 5 LOO + 5
  AOI = **14 cells**. Rationale: these carry every confirmatory RQ1/RQ2/RQ4 claim and the Stage-2
  extraction corpus (FULL, NEUTRAL) / base (NOSYS).
- **Interaction cells → 3 seeds** {0..2}: the 10 three-component res-V runs = **10 cells** (they feed
  the factorial 2FI estimates, which pool across the 16 runs and tolerate unbalanced seeds under the
  mixed model).

**Generation unit (atomic results row).** A *generation unit* = one **(cell_id, prompt_id, seed)**
triple → one HTML file → rendered to one desktop PNG (1440×900) [+ one mobile PNG 390×844 for the
RQ7 responsiveness subset] → one DOM-JSON → one objective-metrics row. Everything downstream keys on
`(cell_id, prompt_id, seed)`.

---

# PART III — Stage-1 ablation design (lifecycle phases 4–6)

Factor↔letter map for the DOE: **A = C1 (color), B = C2 (layout), C = C3 (typography),
D = C4 (patterns), E = C5 (negatives)**. A `+` means the real component is present; a `−` means its
matched filler occupies the slot (constant mass, §II.1.3).

## III.1 Cell table (every cell enumerated; deduped)

**24 distinct cells.** Verified by enumeration (`scratchpad` check reproduced in THEORY §T1). The
2⁵⁻¹ resolution-V fraction (generator **E = ABCD**, defining relation **I = ABCDE**, principal
fraction) yields 16 runs; **6 of them coincide with already-named cells** (the all-`+` run *is* FULL;
the five single-`+` runs *are* the five AOI cells), so the fraction contributes **10 new** three-
component cells. Neither the 5 LOO cells (four `+`, odd parity → product −1) nor NEUTRAL (all `−`,
odd parity) lie in the principal fraction; they are separate cells.

| # | cell_id | C1 | C2 | C3 | C4 | C5 | tier | seeds | purpose / RQ | in 16-run fraction? |
|---:|---|:--:|:--:|:--:|:--:|:--:|---|:--:|---|:--:|
| 1 | **FULL** | + | + | + | + | + | control | 5 | intact skill; reference; Stage-2 skill side | ✓ (all-`+`) |
| 2 | **NEUTRAL** | − | − | − | − | − | control | 5 | length-matched neutral; Stage-2 contrast side; AOI baseline (ADR-003) | ✗ |
| 3 | **BEAUTY1** | · | · | · | · | · | control | 5 | 5-word nudge (RQ4) | ✗ |
| 4 | **NOSYS** | · | · | · | · | · | control | 5 | bare baseline; Stage-2 "no-prompt" base | ✗ |
| 5 | **LOO-C1** | − | + | + | + | + | LOO | 5 | necessity of C1 (RQ1) | ✗ |
| 6 | **LOO-C2** | + | − | + | + | + | LOO | 5 | necessity of C2 (RQ1) | ✗ |
| 7 | **LOO-C3** | + | + | − | + | + | LOO | 5 | necessity of C3 (RQ1) | ✗ |
| 8 | **LOO-C4** | + | + | + | − | + | LOO | 5 | necessity of C4 (RQ1) | ✗ |
| 9 | **LOO-C5** | + | + | + | + | − | LOO | 5 | necessity of C5 (RQ1; expected large) | ✗ |
| 10 | **AOI-C1** | + | − | − | − | − | AOI | 5 | sufficiency of C1 (RQ2) | ✓ (run +−−−−) |
| 11 | **AOI-C2** | − | + | − | − | − | AOI | 5 | sufficiency of C2 (RQ2) | ✓ (run −+−−−) |
| 12 | **AOI-C3** | − | − | + | − | − | AOI | 5 | sufficiency of C3 (RQ2) | ✓ (run −−+−−) |
| 13 | **AOI-C4** | − | − | − | + | − | AOI | 5 | sufficiency of C4 (RQ2) | ✓ (run −−−+−) |
| 14 | **AOI-C5** | − | − | − | − | + | AOI | 5 | sufficiency of C5 (RQ2) | ✓ (run −−−−+) |
| 15 | **F-123** | + | + | + | − | − | interaction | 3 | 2FI block (RQ3) | ✓ |
| 16 | **F-124** | + | + | − | + | − | interaction | 3 | 2FI block (RQ3) | ✓ |
| 17 | **F-125** | + | + | − | − | + | interaction | 3 | 2FI block (RQ3) | ✓ |
| 18 | **F-134** | + | − | + | + | − | interaction | 3 | 2FI block (RQ3) | ✓ |
| 19 | **F-135** | + | − | + | − | + | interaction | 3 | 2FI block (RQ3) | ✓ |
| 20 | **F-145** | + | − | − | + | + | interaction | 3 | 2FI block (RQ3) | ✓ |
| 21 | **F-234** | − | + | + | + | − | interaction | 3 | 2FI block (RQ3) | ✓ |
| 22 | **F-235** | − | + | + | − | + | interaction | 3 | 2FI block (RQ3) | ✓ |
| 23 | **F-245** | − | + | − | + | + | interaction | 3 | 2FI block (RQ3) | ✓ |
| 24 | **F-345** | − | − | + | + | + | interaction | 3 | 2FI block (RQ3) | ✓ |

(· = not applicable: BEAUTY1/NOSYS are not factorial cells. The **16-run factorial** = {FULL, AOI-C1…
C5, F-123…F-345}.)

**Generation counts (reconciled; THEORY §T1).**
- **Dev (40 prompts), all 24 cells:** 14 headline × 5 + 10 interaction × 3 = 70 + 30 = **100
  units/prompt × 40 = 4,000**.
- **Held-out (18 prompts), reduced set** {4 controls + 5 LOO}: 4 × 5 + 5 × 3 = 20 + 15 = **35
  units/prompt × 18 = 630**. (AOI and interaction cells are dev-scope: sufficiency and 2FIs are
  in-domain questions; held-out is reserved for the confirmatory necessity replication + Stage-2.)
- **Stage-1 total = 4,630 generation units.**

**Compute-budget table (Stage-1 generation, vLLM; full project budget in Part VI).**

| quantity | value | basis |
|---|---|---|
| generations | 4,630 | table above |
| tokens/gen (out) | ≈3,000 avg (2–4k) | `03_colab_feasibility` |
| output tokens total | ≈13.9 M | 4,630 × 3,000 |
| vLLM throughput (L4/A100, batched) | ≈1.5 k tok/s aggregate | `04_generation_hooks_tooling` |
| wall-clock (compute only) | ≈2.6 h | 13.9 M / 1.5 k / 3600 |
| wall-clock (with prefill/batch overhead, checkpointing) | **≈6 L4-hours** | ×~2 headroom |
| storage / unit | ≈0.47 MB (HTML 10 KB + PNG 400 KB + DOM-JSON 60 KB) | §VI |
| Stage-1 storage | ≈2.2 GB (+ mobile subset) | 4,630 × 0.47 MB |

Colab sessions are 12 h (Pro) / 24 h (Pro+) with ~90-min idle disconnect (`03_colab_feasibility`) →
Stage-1 generation fits **one** L4 session with checkpointing every 200 units to Drive.

## III.2 Aliasing statement (resolution-V fraction)

Half-fraction **2⁵⁻¹**, generator **E = ABCD**, defining relation **I = ABCDE** (`montgomery2017doe`
Ch. 8; `04_experimental_design_stats`). Resolution **V** ⇒:
- **All five main effects** (C1…C5) are aliased only with **four-factor interactions**
  (e.g. A = BCDE), assumed negligible.
- **All ten two-factor interactions** are aliased only with **three-factor interactions**
  (e.g. AB = CDE, AC = BDE, …, DE = ABC), assumed negligible.

**⇒ Main effects and all 2FIs are cleanly estimable** under the standard "3FI-and-higher negligible"
assumption — a defensible assumption for five prescriptive design components. Full alias chains
(one representative each): A=BCDE, B=ACDE, C=ABDE, D=ABCE, E=ABCD; AB=CDE, AC=BDE, AD=BCE, AE=BCD,
BC=ADE, BD=ACE, BE=ACD, CD=ABE, CE=ABD, DE=ABC. Tabulated in THEORY §T2.

**Model-matrix construction rule.** Code each cell as a ±1 vector `x = (x_A,…,x_E)`; the model matrix
columns are `[1, x_A, x_B, x_C, x_D, x_E, x_Ax_B, x_Ax_C, …, x_Dx_E]` (intercept + 5 mains + 10 2FIs
= 16 columns) evaluated on the **16 factorial runs only** (FULL + 5 AOI + 10 F-cells; NEUTRAL and LOO
are analyzed by direct contrast, not inside this matrix). Because E = ABCD, the E column equals the
product of the A,B,C,D columns — never add both an explicit E and ABCD term (perfect collinearity).
`src/mixedlm` builds the matrix from the frozen sign table and asserts column rank 16.

## III.3 Objective-metric suite (the deterministic oracle half)

Computed on the **rendered DOM + screenshot**, never raw code (CLAUDE.md). Reported as a **vector**
(no raw aggregation; `si2024design2code` lesson) organized into **six families** + auxiliary.
Formulas in THEORY §T7; implemented in `src/metrics_dom` (Playwright `boundingBox()`/computed styles)
and `src/metrics_visual` (screenshot pixels).

| family | metrics | source |
|---|---|---|
| **V — Validity/hermeticity** | render-success (binary gate), external-fetch count (hermeticity), overflow count, overlap count, axe-core total violations (by impact) | `deque2024axecore`, `wu2024uicoder`, ADR-006 |
| **A — Accessibility/contrast** | WCAG 2.x contrast per text node → fraction < 4.5:1, min, median; axe contrast violations; APCA Lc (secondary) | `07_accessibility_contrast_survey`, `w3c2018wcag21` |
| **L — Layout** | Ngo balance BM, equilibrium EM, symmetry SYM, alignment/grid regularity (#distinct x/y edges, gap entropy), white-space ratio, density | `ngo2003modelling`, `miniukovich2015computation` |
| **T — Typography** | #distinct font-sizes, #distinct families, modular-scale adherence (geometric-spacing fit) | `03_computational_aesthetics` |
| **C — Color** | Hasler colorfulness M, #dominant colors, figure-ground contrast, **purple-slop-index** subcomponents | `hasler2003colorfulness`, `reinecke2013predicting` |
| **X — Complexity** | edge/quadtree visual complexity | `reinecke2013predicting` |
| aux (learned, secondary) | UIClip design-quality score; CLIP prompt↔screenshot relevance | `wu2024uiclip`, `wu2024uicoder` |

**Purple-slop index (PSI), principled composite** (`03_computational_aesthetics`; validated before
use, §III.3.1): `PSI = w₁·hueFrac[260°,290°] + w₂·gradientBgPrevalence + w₃·InterRobotoShare +
w₄·centeredHeroFlag`, each subcomponent ∈ [0,1], default weights `w = (0.3,0.3,0.25,0.15)`; report
subcomponents **and** composite. Lower PSI = less "AI slop." **The skill's own C5 negatives define
these subcomponents** — the skill tells us exactly what to measure.

### III.3.1 Oracle validation (must pass before any RQ uses a metric as evidence)
- **PSI validation:** on the human-labeled subset (§III.8), collect a human "looks AI-generated" 1–5
  rating per screenshot; **admit PSI only if** Spearman ρ(PSI, human-AI-rating) ≥ 0.4 with bootstrap
  CI excluding 0. If it fails, PSI is demoted to a descriptive diagnostic (not evidence) **and the
  confirmatory POC is recomputed without its −PSI term per the pre-specified conditional in §III.4.**
- **UIClip validation:** admit UIClip as an auxiliary quality signal only if Spearman ρ(UIClip, human
  preference win-rate) ≥ 0.3 on the human subset; else drop (mobile-distribution risk, `wu2024uiclip`).
- **Metric-correlation matrix (F4):** report pairwise correlations across all metrics to expose
  redundancy; the POC (below) z-scores and averages a *pre-registered* subset, not all metrics.

## III.4 Primary endpoints & the Primary Objective Composite (POC)

To have **one** primary objective number per cell for the confirmatory family while respecting
"don't aggregate raw," we pre-register a single composite from *oriented, z-scored* core metrics:

**POC** = mean of z-scores (z over all dev generation units) of, oriented so higher = better:
`+align_regularity, +whitespace_score, +type_scale_consistency, +contrast_pass_rate,
−overflow_overlap_count, −PSI, −|colorfulness − c*|` where `c*` = the human-appeal-optimal
colorfulness calibrated on the human subset (default = median Hasler-M of the human-preferred pages,
`reinecke2013predicting` moderate-optimum). **Render-failed units are excluded from POC** and counted
in family V (a non-rendering page is a validity null regardless of aesthetics, `wu2024uicoder`).

**Pre-specified POC conditionals (frozen with the endpoint; not post-hoc amendments).**
(i) **PSI term:** if PSI fails its §III.3.1 admission gate, the confirmatory POC is recomputed as the
same composite **without the −PSI term** (a **6-term POC**), and every confirmatory decision uses
that 6-term POC; the 7-term variant is then reported descriptively only. (ii) **c\* anchor:** `c*` =
median Hasler-M of the human-preferred pages **iff ≥ 30 human-preferred pages** are available from
the §III.8 subset; otherwise `c*` defaults to the **median Hasler-M of the dev FULL-cell
generations** (pre-stated: the skill-on distribution operationalizes "moderate colorfulness" without
human data; one of seven z-scored terms, fixed before any confirmatory analysis). Whichever branch
fires is recorded in the manifest before the first confirmatory test is run.

**Primary endpoints per RQ:** (1) **preference** = style-controlled BT utility (§III.5); (2)
**objective** = POC (confirmatory) + the family-wise objective decision (§III.6). The full metric
vector and PSI subcomponents are **secondary/diagnostic** (BH-controlled scans).

## III.5 Preference protocol — comparison graph + style-controlled Bradley-Terry

**Why a graph, not all pairs.** 24 cells ⇒ 276 unordered pairs; judging all × 40 prompts × seeds
explodes past budget. We judge a **designed comparison graph** whose edges are exactly the
confirmatory contrasts, hub-connected through FULL and NEUTRAL so the Bradley-Terry graph is
connected and every cell has a path to the reference.

**Comparison graph (dev; each edge judged both orders; seed-pairs = # randomly seed-matched
generation pairs per (edge, prompt)):**

| edge (cellA vs cellB) | RQ | prompts | seed-pairs | judgments | rationale |
|---|---|---:|---:|---:|---|
| FULL – NEUTRAL | H-skill | 40 | 5 | 200 | headline skill effect (well-powered) |
| FULL – LOO-Cᵢ (×5) | RQ1 | 40 | 3 | 600 | necessity (confirmatory, ~120 pairs each) |
| FULL – NOSYS | RQ4/base | 40 | 3 | 120 | skill vs bare |
| FULL – BEAUTY1 | RQ4 | 40 | 3 | 120 | content vs nudge |
| NEUTRAL – AOI-Cᵢ (×5) | RQ2 | 40 | 2 | 400 | sufficiency (~80 pairs each) |
| NEUTRAL – NOSYS | ADR-003 | 40 | 2 | 80 | isolates prompt-mass effect |
| BEAUTY1 – NEUTRAL | RQ4 | 40 | 2 | 80 | nudge vs neutral |
| **dev confirmatory subtotal** | | | | **1,600** | |
| F-cell – NEUTRAL (×10) | RQ3 (expl.) | 10 (subset) | 1 | 100 | interaction cells vs baseline (BH) |
| held-out FULL – NEUTRAL | replication | 18 | 2 | 36 | OOD skill effect |
| held-out FULL – LOO-Cᵢ (×5) | RQ1 repl. | 18 | 2 | 180 | OOD necessity |
| **Stage-1 total** | | | | **1,916** | |

A **judgment** = one `(cellA, cellB, prompt, seed-pair)` comparison adjudicated over **both
presentation orders** (2 judge calls). Seed-matching: for each (edge, prompt) draw seed-pairs by
pairing seed *k* of A with seed *k* of B (k = 0…seed-pairs−1); this ties out prompt but leaves seed
free, so the BT sees within-prompt seed variance. Stage-2 adds 96 (sweep) + 198 (verification) =
**294** judgments (Part IV). **Grand total ≈ 2,210 judgments (~4,420 primary both-order calls)** —
within the 2–4k judgment budget (D6). Judge cost (§III.8): **≈$14** total.

**Power alignment (§III.7):** the necessity edges get 3 seed-pairs → ~120 informative pairs each,
sufficient to detect a **60/40** preference split at 80 % power (≈200 needed for 60/40; ≈80 for
65/35); the headline FULL–NEUTRAL gets 200 pairs (detects even a 55/45 shift). Small expected effects
(some AOI) are lightly powered on the *preference* signal on purpose — their non-null status can still
be established via the **objective** signal (fully powered: 5 seeds × 40 prompts per cell), per the
two-signal null rule. If a confirmatory preference edge is under-powered after the fact, its
seed-pairs are increased (pre-stated contingency, up to the 4k budget) rather than reinterpreted.

**Style-controlled Bradley-Terry (`bradley1952rank`, `chiang2024stylecontrol`; C3 note).**
For cells i,j with strengths βᵢ and per-page style covariates s:
$$P(i \succ j) = \sigma\!\big((\beta_i-\beta_j) + \gamma^{\top}(s_i - s_j)\big),\qquad \sigma(z)=\tfrac{1}{1+e^{-z}}.$$
- **Covariates s** (remove length/verbosity/colorfulness confounds the judge is biased by, `zheng2023mtbench`): `log(DOM node count)`, `log(output token length)`, `element count`,
  `Hasler colorfulness`, `text density`. Reference cell **NEUTRAL** (β=0).
- **Ties:** order-inconsistent verdicts → tie; ties modeled with a **Davidson** tie term (not
  half-win/half-loss).
- **Estimation:** MLE (logistic) in `src/bt_model`; **cluster-bootstrap CIs over prompts, B = 2,000**
  (resample whole prompts, refit) — respects shared-prompt correlation.
- **Effect sizes:** BT utility difference (logits) with CI **and** raw preference win-rate with CI.

## III.6 Analysis plan per RQ (decision-complete)

**Objective metrics → MixedLM (`04_experimental_design_stats`; `src/mixedlm`, statsmodels).**
For a continuous metric y (POC or a family metric) over units (cell c, prompt p, seed s):
$$y_{cps} = \mu + \tau_c + u_p + v_{cp} + \epsilon_{cps},\quad u_p\sim N(0,\sigma_p^2),\ v_{cp}\sim N(0,\sigma_{cp}^2),\ \epsilon\sim N(0,\sigma^2),$$
`τ_c` fixed cell effects. Formula: `y ~ C(cell)`, `groups = prompt`, `re_formula = "1"` (random prompt
intercept); add random cell-by-prompt slope `v_{cp}` where it converges. **Factorial subset (16
runs):** `y ~ C1+C2+C3+C4+C5 + (all 10 two-way)` fixed (the §III.2 matrix), `groups = prompt`, random
prompt intercept — gives main effects + 2FIs with proper SEs on unbalanced seeds. **Binary metric
(render-success):** GLMM binomial (`BinomialBayesMixedGLM`, or `bambi`/`pymer4` fallback).
**Convergence fallbacks, in order:** (1) drop random slope → intercept-only; (2) REML→ML; (3)
per-prompt cluster-bootstrap of the cell-mean contrast (non-parametric), reported with the same CI
machinery. The fallback actually used is recorded per model.

**Effect-size definitions.** Per metric: **standardized δ** = `(mean_cellA − mean_cellB)/σ_pooled`
(within-prompt pooled SD), with cluster-bootstrap CI. Preference: **win-rate** (with CI) and **BT
utility Δ** (logits, with CI). Necessity/sufficiency rankings use standardized δ on the POC.

**Objective-signal decision (per contrast).** The objective signal **moves** iff the POC contrast is
significant after Holm (confirmatory family) **OR** ≥2 of the 6 metric families show a concordant,
BH-significant shift. Otherwise the objective signal is **null** for that contrast.

**Multiplicity (`holm1979`, `benjamini1995fdr`).**
- **Confirmatory family → Holm–Bonferroni, FWER = 0.05**, applied **separately** to the POC family and
  the preference family. Confirmatory tests (12 each): {FULL−NEUTRAL; 5×(FULL−LOO-Cᵢ);
  5×(AOI-Cᵢ−NEUTRAL); FULL−BEAUTY1}.
- **Exploratory → Benjamini–Hochberg, FDR = 0.10**: the 10 two-factor interactions; per-family metric
  scans; auxiliary metrics; per-task-type breakdowns; the F-cell preference edges; the MIXED
  robustness cell.
- Pre-registered which is which (PREREGISTRATION §4).

**Per-RQ mapping.**
- **RQ1 (necessity):** Holm over {FULL−LOO-Cᵢ} on POC; parallel gated preference; rank by δ. Fig F1
  (forest), F2 (necessity×sufficiency scatter).
- **RQ2 (sufficiency):** Holm over {AOI-Cᵢ−NEUTRAL} on POC; the "distributed" rule (§RQ2). F1/F2.
- **RQ3 (interactions):** BH over the 10 2FIs from the factorial MixedLM. Fig F3 (heatmap).
- **RQ4 (nudge):** ordered contrasts FULL>BEAUTY1>NEUTRAL. Reported as a small table + F1.
- **RQ7 black-box slice:** per-task-type FULL−NEUTRAL deltas (BH), incl. the OOD held-out types.

**The preregistered null rule (verbatim; = §0.2):** *An ablated component's effect, or a steering
direction's effect, is reported as null unless it moves an objective-metric endpoint (POC Holm-
significant, or ≥2 concordant BH-significant families) OR a preference delta that passes both the
reliability gate and the power gate. Aesthetic claims not backed by the objective half are
inadmissible.*

## III.7 Power (McNemar paired sizing; `04_experimental_design_stats`; `src/power`)

Preference deltas are paired (same prompt, cellA vs cellB). Normal approximation to McNemar:
$$n \approx \frac{\big(z_{1-\alpha/2}\sqrt{p_d} + z_{1-\beta}\sqrt{p_d - \delta^2/p_d}\big)^2}{\delta^2},$$
`p_d` = P(discordant pair), `δ` = P(A wins) − P(B wins). Planning results (α=.05, power=.80):
**60/40 → ~200 informative pairs; 65/35 → ~80; 55/45 → ~780.**

**Decisive-vs-judged clarification (THEORY T6.1–T6.2).** The sizing numbers count **decisive**
(order-consistent, non-tie) pairs — the canonical computation is THEORY (T6.2), the one-sample
split test among decisive pairs; do **not** plug the marginal δ together with a p_d < 1 into the
two-parameter formula (that mis-plug yields ≈93, neither reading). The §III.5 allocations count
**judged** pairs; at tie rate t an edge yields ≈ (1−t)·judged decisive pairs. Between
well-separated cells ties should be uncommon, but the assumption is checkable, not assumed: if an
edge's decisive count falls below the required N_dec at the observed δ, the post-hoc power gate
below rules it under-powered and the pre-stated seed-pair top-up (§III.5) applies. Consequences baked into
§III.5: headline gets 200; necessity gets ~120 (powered for ≥60/40); BT utilities get **simulation-
based power** (assume plausible β gaps + noise, simulate pairwise data at the planned n, require
detection ≥ 80 %) in `src/power`, run on **synthetic data now** (CPU) so the budget is validated
pre-freeze. **Power gate:** a preference delta counts only if its contrast met its planned pair count
for the effect size observed (post-hoc: recompute required n at the observed δ; if achieved n < that,
the delta is "under-powered" → not admissible as the sole signal).

## III.8 Judge protocol (`05_vlm_judge_pricing`, `01_llm_vlm_judge`, `jeon2025gfocus`, `zhang2025artifactsbench`)

**Judges.** Primary = **Gemini 2.5 Flash** (cheap, high-RPM, different family from Qwen → avoids
self-enhancement, `zheng2023mtbench`). Secondary = **GPT-4o** on a **15 % random audit subset** (cross-
family check). Never Qwen-VL as primary. Cost: primary ≈ $6.9, audit ≈ $7.1, **total ≈ $14** (D6).

**Screenshot spec (fixed).** Primary = **desktop viewport 1440×900**, full-page capture with width
pinned at 1440, **device-scale-factor 1**, `animations:'disabled'`, caret hidden, `document.fonts.ready`
awaited, network blocked/offline, `networkidle` + fixed settle delay, pinned Chromium+Playwright
versions (`06_playwright_determinism`). *(This fixes 1440×900 as primary, overriding the note's
1280×800 example, because 1440 is a standard design breakpoint and gives the judge more layout to
assess.)* Secondary = **mobile 390×844**, used **only** for the RQ7 responsiveness robustness slice
(a subset), not for the headline BT.

**Pairwise prompt template (write-out; `src/judge`).**
- **Role:** "You are a senior product designer evaluating two rendered web UIs built for the *same
  brief*. Judge overall design quality for that brief. Ignore which looks longer or more colorful per
  se; judge whether choices are deliberate and fit the brief."
- **Inputs:** the brief text; screenshot A; screenshot B (both desktop 1440×900).
- **Checklist anchors** (from the six metric families, forces reliability, `zhang2025artifactsbench`):
  color/palette coherence; layout & visual hierarchy; typography; component/pattern quality; restraint
  (absence of generic "AI-slop" tells); overall fit-to-brief.
- **Output JSON schema:**
  `{"winner":"A"|"B"|"tie", "confidence":1-5, "per_criterion":{"color":"A"|"B"|"tie", "layout":…,
  "typography":…, "components":…, "restraint":…, "fit":…}, "rationale":"≤40 words"}`.
- **Both-orders logic:** each pair judged as (A,B) and (B,A); **winner counts only if consistent
  across orders**, else **tie** (position-bias control, `jeon2025gfocus`). Confidence averaged across
  orders.
- **Tie handling:** feeds the Davidson tie term in BT (§III.5).
- **Determinism:** judge temperature 0, rubric cached as a system prompt, batched with backoff.

**Human-validation subset (the reliability ground truth; ADR-005, C2).**
- **Sean labels N = 100 pairs**, sampled to span contrasts and the skewed marginal (stratified: 30
  FULL–NEUTRAL, 35 FULL–LOO, 20 AOI–NEUTRAL, 15 Stage-2 steered–unsteered), **both orders**, same
  rubric. An optional second human rater enables a human–human check.
- **Compute** judge-vs-Sean **Krippendorff α (ordinal)** and **Gwet AC1**, each with **bootstrap 95 %
  CIs** (`src/agreement`, runs on synthetic labels now). Report the **marginal distribution** (to make
  the skew visible; the skill usually wins → kappa-paradox risk, `gwet2008ac1`).
- **Gate (preregistered):** proceed to trust the preference signal iff **α ≥ 0.667 OR (AC1 ≥ 0.80 with
  α depressed by demonstrable marginal skew)**.
- **Fallback cascade if the gate fails:** (1) revise the rubric/checklist wording, re-run the judge on
  the same 100; (2) switch primary judge to GPT-4o or Claude-Sonnet-class, re-validate; (3) escalate
  human labeling to **N = 300** and down-weight the judge to a tie-breaker; (4) if still failing,
  report the preference signal as **low-reliability** and rely on the **objective** signal for the
  null rule (an effect can still be non-null via objective). Each step dated in an amendment
  (PREREGISTRATION §7).

## III.9 Pilot (gate zero — before the full factorial)

**Design.** 2 prompts (one dev-easy L01, one dev-hard D02) × {FULL, NOSYS} × 3 seeds = **12
generations** (vLLM), rendered + metric'd + eyeballed.

**Pass criteria (ALL must hold):**
1. **Renders:** render-success ≥ 11/12 (hermetic, no external fetch).
2. **Skill visibly changes output:** FULL vs NOSYS differ on **PSI and ≥2 objective families**, and a
   manual side-by-side confirms a visible aesthetic change (documented with the 12 screenshots).
3. **Metrics move the right way:** the FULL−NOSYS POC gap is **positive on the majority of prompt×seed
   pairs** and its sign is consistent with the skill helping.

**Fail → fallback (pre-stated).** (a) **Prompt-format fixes first:** verify ChatML application, system
vs user placement, that the skill is not truncated, tokenizer special-tokens; re-run the pilot. (b)
**Only if the skill still has no visible effect after format fixes**, trigger the **ADR-001 model
fallback** to `meta-llama/Llama-3.1-8B-Instruct` (the *only* sanctioned trigger for the model swap;
requires the ADR note and restarts both stages). The pilot is the single gate that de-risks the whole
project's core assumption ("the model can apply a 5-part skill", D1 caveat) before spending the
generation budget.

---

# PART IV — Stage-2 interpretability pipeline (the committed second stage)

All Stage-2 activation/steering work runs on **HF `transformers` + the custom hook module**
(`src/hooks`, ADR-002); vLLM cannot inject mid-decode. Residual stream is the **layer output hidden
state**, `model.model.layers[i]` output `[0]`, shape `[batch, seq, 3584]`; hooks handle the tuple
output, per-decode-step firing (seq_len==1), running-mean capture (`04_generation_hooks_tooling`,
`01_qwen_model_facts`). d = 3584, L = 28 layers; focus band ≈ layers 11–20. Engine/version/seed
recorded per run; **never** compare a vLLM baseline to an HF steered output — any Stage-1↔Stage-2
numeric comparison re-generates the baseline in HF (ADR-002). Common notation (shared with THEORY):
`h_l(t)` = residual at layer l, token t; `\bar h_l^{(skill)}` = mean over response tokens, skill side.

For **every** experiment below: **inputs · procedure · outputs · compute · outcome-interpretations
(incl. null).**

## S2.0 — Extraction corpus
- **Inputs.** The Stage-1 **FULL** and **NEUTRAL** generations on the **40 dev prompts × 5 seeds** =
  **200 per side, 200 matched pairs** (reuse P1 artifacts; `system_variant∈{FULL,NEUTRAL}`).
- **Procedure.** For each generation, HF **teacher-forced forward pass** over `[chat-template prompt ‖
  generated response]`; capture the **mean residual over response tokens** at every layer
  (running-mean accumulation, `chen2025persona`). Store per-(example, layer) mean vectors (28×3584
  floats/example ≈ 0.4 MB → ≈160 MB total, means only). Teacher-forcing (not re-generation) keeps this
  cheap and reuses the exact Stage-1 text; activations are HF-side, so all downstream steering stays
  within-engine.
- **Stability check.** Running-mean **cosine-similarity plateau**: as n grows 20→200, track
  `cos(v_l(n), v_l(n−Δ))`; **require Δcos < 0.01 over the last 20 % of examples** at the focus layers.
  If not plateaued at 200, extend FULL/NEUTRAL dev generations by seeds 5–7 (contingency), re-check.
- **Outputs.** `results/activations_meta.parquet` (per-layer means, pair index); the stability figure
  (F13).
- **Compute.** 400 forward passes (~3k tok) ≈ **<0.5 A100-h**.
- **Interpretations.** Plateau reached → corpus is adequate. Plateau not reached even at 300 → the
  contrast is high-variance (flag; extraction directions will be noisy; expect weak steering).

## S2.1 — Locate (probing · diffing · patching)
- **(a) Per-layer linear probes.** Logistic probe on the **mean-response residual** (skill vs neutral),
  **5-fold CV by prompt** (folds split on prompt, never leaking a prompt across folds). Report **AUC
  per layer** + **control-task selectivity** (`hewitt2019control`): a random-but-fixed label per prompt
  defines the control task; `selectivity = AUC_real − AUC_control`. Use **linear** probes (higher
  selectivity than MLP). Output: per-layer AUC & selectivity curve.
- **(b) Activation diffing.** Per-layer diff-in-means norm `‖v_l‖`, and the cosine structure across
  layers (`cos(v_l, v_{l'})`) to see whether one direction persists through the band.
- **(c) Denoising activation patching (neutral→skill).** On a **small subset** (8 dev prompts × 3
  seeds), patch the **skill-side mean-response residual** into the **neutral** run at (layer, position)
  sites. **Metric for long generation** (no single answer token): the **design-token logit-difference
  proxy** — `Δ = logit(t⁺) − logit(t⁻)` at the first response position where the model commits to a
  style token, with `t⁺` a non-default choice (e.g. a non-`Inter` `font-family` token, a non-purple hex
  digit pattern) and `t⁻` the default; **report % of the clean−corrupted gap recovered** (`zhang2024patching`,
  `heimersheim2024patching`). Denoising (not noising) avoids self-repair confounds. Corruption =
  the length-matched neutral run (already our confound control).
- **Outputs.** **Localization figure F5** (probe AUC + selectivity + patching %-recovered by layer);
  the **chosen layer band** = the RQ5 decision rule (§I RQ5). Cross-check: probe-peak ≈ patch-peak ≈
  diff-in-means max-‖v_l‖ layer.
- **Compute.** Probes: negligible (CPU on cached means, runs *now* on synthetic activations to test
  the code). Patching: ~48 forward/partial passes ≈ **~0.5 A100-h**.
- **Interpretations.** Concordant mid-band peak → clean localization, feeds S2.3 focus layers.
  Probe-high but patch-low → the signal is **decodable but not causally used at that site** (probe/
  cause gap, `alain2017probes`) → rely on steering-selection, not probing. No peak anywhere → diffuse
  representation (RQ5 null; expect to need multi-layer injection in S2.3).

## S2.2 — Extract (diff-in-means + cross-checks)
- **Inputs.** The S2.0 per-layer means.
- **Procedure.** Diff-in-means per layer, unit-normalized:
  $$v_l = \bar h_l^{(\text{FULL})} - \bar h_l^{(\text{NEUTRAL})},\qquad \hat v_l = v_l/\lVert v_l\rVert.$$
  Three **position variants** (all over the same generations): **(i) mean-response** (primary,
  `chen2025persona`); **(ii) last-prompt-token** (for the projection monitor); **(iii) first-k response
  tokens with k = 64** (early commitment). Cross-checks: **PCA-of-paired-differences** top component
  (LAT-style, `zou2023repe`) and report `cos(\hat v_l, \text{PC1})` (expect high); optionally the
  **probe weight direction** vs `\hat v_l`.
- **Outputs.** `\hat v_l` for all layers × 3 variants; the cosine-agreement table (diff-in-means vs
  PCA vs probe direction).
- **Compute.** CPU on cached means (runs now on synthetic).
- **Interpretations.** High cosine agreement across methods → the direction is robust/linear (proceed).
  Low agreement (diff-in-means ⟂ PC1) → the contrast is not a single clean axis → flag possible
  multi-dimensional structure (`engels2024notlinear`), plan the 2–4D subspace fallback (S2.3).

## S2.3 — Dev selection (sweep → freeze the operating point)
- **Inputs.** `\hat v_l`; **dev prompts only** (12-prompt sweep subset spanning ≥6 types); the NOSYS
  base (steer with no design prompt).
- **Procedure.** Steer by adding at **all generated positions** (`rimsky2024caa`):
  `h_l ← h_l + c·\hat v_l`. **Sweep grid:**
  - **layer ℓ** ∈ the S2.1 focus band (default candidates {11,13,15,17,20}; ≤5).
  - **coefficient c** parameterized **two ways**, both reported: **absolute** `c = m·‖v_l‖`,
    `m ∈ {1,2,4,8,16}`; **norm-relative** `c = ρ·\overline{‖h_l‖}`, `ρ ∈ {0.05,0.1,0.2,0.3,0.5,0.7,1.0}`
    (`ρ` is the primary axis — transfers across layers, `12_steering_variants_survey`). Include two
    negative points `ρ∈{−0.2,−0.5}` as a sanity check (should degrade).
  - **variant** ∈ {mean-response, last-prompt-token, first-k=64}.
  Two-stage to bound cost: **coarse** (5 layers × 7 ρ × mean-response variant × 12 prompts × 2 seeds),
  then **refine** (best 2 layers × best 3 ρ × 3 variants × 12 prompts × 2 seeds). Score each config by
  objective metrics (POC on dev) + a **cheap judge subset** (§III.5: 96 judgments over the 8
  shortlisted configs).
- **Guardrails (define precisely).**
  - **KL/coherence guardrail:** on a **fixed 512-token eval text** (a generic neutral HTML+prose
    snippet, frozen in `config/`), compute the **mean per-token KL** between steered and unsteered
    next-token distributions; **require mean KL ≤ 0.30 nats.**
  - **Render/coherence guardrail:** steered dev-subset **render-success ≥ 0.90**.
- **Selection criterion (pre-stated).** `(ℓ*, ρ*, variant*) = argmax POC-gain on dev` **subject to**
  `mean-KL ≤ 0.30` **and** `render-success ≥ 0.90`. Ties broken by lower KL (prefer the gentler
  operating point). If **no** single-layer config clears the POC-gain threshold (POC-gain > 0 with
  bootstrap CI > 0) under the guardrails, escalate to **multi-layer injection** (add at 2–3 focus
  layers simultaneously, `vanderweij2024broad`) or the **2–4D subspace** (PCA of per-component
  diffs) — both pre-stated fallbacks, then re-select.
- **Outputs.** the **α×layer steering heatmap (F6)**; the **dose-response curve (F7)** spec (POC &
  render-success vs ρ, with failure shading); the frozen `(ℓ*, ρ*, variant*)` written to
  `config/steering_frozen.yaml` (hashed; **git-tagged before any held-out generation**).
- **Compute.** coarse ≈ 5·7·12·2 = 840 gens; refine ≈ 2·3·3·12·2 = 432 gens; capped at 1,500 tokens
  for the sweep → HF batched ≈ **~4 A100-h**.
- **Interpretations.** A clear guardrail-satisfying optimum with non-monotone dose-response
  (`taimeskhanov2026strength`) → healthy; proceed to freeze. Optimum only above the KL threshold →
  the direction steers only by breaking coherence → **weak/incoherent steering** warning (expect S2.4
  to fail or the effect to ride on artifacts). No positive POC-gain at any config → single-direction
  steering fails on dev → try multi-layer/subspace; if those also fail, the RQ6 honest-null branch is
  likely.

## S2.4 — Held-out causal verification (THE BAR)
- **Inputs.** **Frozen** `(ℓ*, ρ*, variant*)`; **held-out prompts (18, incl. 10 unseen types)**; NOSYS
  base. Touch held-out **once**.
- **Arms (n per arm = 18 prompts × 3 seeds = 54 gens each; random has k=5 draws):**
  1. **unsteered-NOSYS** (base).
  2. **steered-NOSYS** (add `ρ*·\overline{‖h_{ℓ*}‖}·\hat v_{ℓ*}`, no design prompt).
  3. **norm-matched random control** — a random Gaussian direction re-normalized to `‖v_{ℓ*}‖`, **k=5
    independent draws**, same injection (specificity vs non-identifiability, arXiv:2602.06801).
  4. **FULL-skill reference (HF-generated)** — the skill in-prompt, HF engine (within-engine anchor).
- **Both oracle signals:** objective families + POC via MixedLM; preference via style-controlled BT on
  the S2.4 edges (steered–unsteered, steered–random, steered–FULL, unsteered–FULL).
- **Success criterion (preregistered, verbatim):** the design direction is a **causally sufficient
  design direction** iff, on held-out, **steered-NOSYS beats unsteered-NOSYS on ≥1 objective family
  after Holm** (across the 6 families) **AND** the **reliability-gated** preference delta
  (steered ≻ unsteered) has BT-utility cluster-bootstrap CI **> 0**; **AND** the norm-matched random
  control does **not** satisfy both (specificity); **AND** the flip test (S2.5) attenuates the skill's
  gain (necessity). If addition succeeds but the flip test does not → report "**sufficient, not
  demonstrably necessary**."
- **Reproduction fraction.** Report `%skill-reproduced = (POC_steered − POC_unsteered) /
  (POC_FULL − POC_unsteered) × 100 %`, with cluster-bootstrap CI; also per-family.
- **Outputs.** the **held-out causal bar chart with controls (F8)**; the reproduction-fraction table.
- **Compute.** 54+54+270+54 = **432 HF gens** batched ≈ **~1.5 A100-h**.
- **Interpretations.** Criterion met → **the differentiated headline result** (first causal design
  direction for UI code). Addition works but random control *also* works → non-identifiability;
  downgrade to "norm effect, not a specific design direction." Nothing beats unsteered → **RQ6 honest
  null**: design behavior is not linearly steerable in this model / is distributed — reported honestly
  (BRIEF sanctions this), with the tight CIs from the power gate to show it is a real null, not
  under-powering.

## S2.5 — Necessity flip test
- **Inputs.** The **FULL-skill** condition (skill present); `\hat v_{ℓ*}` (and, robustness, `\hat v` at
  all focus layers).
- **Procedure.** **Directional ablation / weight orthogonalization** (`arditi2024refusal`): project
  `\hat v` **out** of the residual stream at **every layer and position** while the skill is present:
  `h ← h − \hat v\,\hat v^{\top}h`. Prefer the **weight-orthogonalization** bake-in (replace each
  residual-writing `W_out ← (I − \hat v\hat v^{\top})W_out`) so no inference hook is needed and the
  ablation is global. Compare FULL vs FULL-with-`\hat v`-ablated on both signals, held-out.
- **Success.** the skill's quality gain is **significantly attenuated**: report **attenuation %** =
  `(POC_FULL − POC_FULL-ablated)/(POC_FULL − POC_unsteered-NOSYS) × 100 %`, CI > 0 to claim necessity.
- **Outputs.** attenuation table; contribution to the F8 story.
- **Compute.** 18×3 (+ variants) ≈ **~0.7 A100-h**.
- **Interpretations.** Large attenuation → the direction is **necessary** for the skill's effect (the
  strong two-arm result). No attenuation → the skill routes its effect through **other directions**
  too (a cone/multi-direction, `wollschlager2025cones`); the added direction is sufficient but not the
  unique carrier — reported as such.

## S2.6 — Specificity & side-effects
- **Inputs.** the frozen steering config; a **fixed set of 20 non-UI algorithmic coding prompts**
  (`config/noncode_probe.yaml`: array/string/graph/DP tasks with unit tests) and a **general-coherence
  eval set** (the S2.3 KL text + 10 held prose/HTML snippets).
- **Procedure.** Run steered vs unsteered on the 20 algorithmic prompts; measure **pass-rate** (unit
  tests) and **syntactic validity**. Measure **general coherence** via the KL guardrail numbers on the
  eval set (mean per-token KL) and perplexity proxy.
- **Tolerances (pre-stated).** steering must not drop algorithmic **pass-rate by > 10 %** absolute vs
  unsteered, nor push **mean KL > 0.30 nats** on general text. Optional **CAST-style conditional
  gating** (`lee2024cast`) fires the vector only when the hidden state aligns with a UI-prompt condition
  vector — reported as a side-effect-bounding option if tolerances are exceeded.
- **Outputs.** the specificity table (pass-rate & KL, steered vs unsteered).
- **Compute.** ~120 HF gens + KL passes ≈ **~0.8 A100-h**.
- **Interpretations.** Within tolerance → the design direction is **specific** (doesn't wreck general
  ability). Out of tolerance → steering is a blunt instrument here → recommend conditional gating and
  flag the trade-off honestly.

## S2.7 — Failure surface & generalization (RQ7)
- **Inputs.** all S2.4 steered held-out generations.
- **Procedure.** **Per-task-type** steering deltas (POC & preference), separating seen vs the two
  unseen types; **anti-steerable fraction** = share of held-out prompts with steered POC < unsteered
  POC (`tan2024analysing`); **dose-response instability** from the S2.3 curve (non-monotonicity index);
  a **break-mode taxonomy** (renders-broken, layout-collapsed, over-saturated color, gibberish text)
  coded from screenshots.
- **Outputs.** the **failure map (F7 shading + F12 anti-steerable-by-type bars)**; honest per-type
  verdict {robust/partial/brittle}.
- **Compute.** analysis only (no new gens).
- **Interpretations.** Positive unseen-type delta + anti-steerable < 50 % → **generalizes** (the OOD
  claim). Unseen-type collapse → steering is in-distribution only; report the boundary precisely.

## S2.8 — Correspondence (stretch, planned; RQ8)
- **Inputs.** the **AOI-Cᵢ** and **NEUTRAL** dev generations (from Stage-1) → per-component contrasts.
- **Procedure.** Component sub-vectors `v_{Cᵢ} = \bar h_{ℓ*}^{(AOI-Cᵢ)} − \bar h_{ℓ*}^{(NEUTRAL)}`,
  unit-normalized. **(a) Geometry:** the **cosine matrix** among {v_C1…v_C5} and with `\hat v_full`
  (near-orthogonal? aligned?). **(b) Signature match:** steer each `\hat v_{Cᵢ}` (at ρ* on a dev/held
  subset) and compute its **steering metric-signature** (which objective family moves most); compare to
  the component's **Stage-1 ablation signature** (which family the LOO/AOI of Cᵢ moved most). Match =
  argmax family agreement, e.g. v_C1 moves the **color** family, v_C2 the **layout** family.
- **Decision rule (§I RQ8):** **found** if mean |cos(v_Cᵢ,v_Cⱼ)| < 0.3 AND ≥3/5 signatures match;
  **partial** if 1–2 match; **absent** otherwise.
- **Outputs.** the **correspondence cosine matrix + signature-match figure (F9)**.
- **Compute.** 5 sub-vectors × ~14 prompts × 3 seeds ≈ 210 HF gens ≈ **~1 A100-h**.
- **Interpretations.** Found → the ablation components map to a steering **basis** (the paper's
  strongest bridge, predicted by `park2024geometry`). Absent → "clean design" is one entangled
  direction, not a component basis — still a clean, informative result.

## S2.9 — Early-token localization (stretch)
- **Inputs.** frozen config; held-out subset.
- **Procedure.** Steer **only the first k ∈ {16, 64, 256}** generated tokens (then release), compare to
  full-generation steering on both signals.
- **Outputs.** early-vs-full steering comparison table.
- **Compute.** 3 k-values × 18 × 3 ≈ 162 HF gens ≈ **~0.7 A100-h**.
- **Interpretations.** Early-only ≈ full → design is **committed early** (the skill sets a trajectory in
  the first tokens); a tidy mechanistic story. Early-only ≪ full → design is maintained throughout
  generation (distributed over the sequence).

**Stage-2 HF-generation subtotal:** ≈ 400 fwd (S2.0) + ~1,270 (S2.3) + 432 (S2.4) + ~110 (S2.5) +
~120 (S2.6) + ~210 (S2.8) + ~162 (S2.9) ≈ **~2,300 generations + 400 forward passes**;
≈ **~9 A100-h** of steering compute (Part VI reconciles the full GPU budget).

---

# PART V — Evaluation & visualization plan (lifecycle phases 7–8)

## V.1 Figure list (id · content · axes · RQ)

| id | content | axes / encoding | RQ / role |
|---|---|---|---|
| **F1** | Ablation forest plot | y = cells (LOO-Cᵢ, AOI-Cᵢ, BEAUTY1, NOSYS); x = standardized δ vs reference, with Holm-CIs; twin panels POC & BT-utility | RQ1, RQ2, RQ4 |
| **F2** | Necessity × sufficiency scatter | x = sufficiency δ (AOI-Cᵢ−NEUTRAL); y = necessity δ (FULL−LOO-Cᵢ); point per component | RQ1, RQ2 |
| **F3** | Interaction heatmap | 5×5 matrix of 2FI coefficients (from factorial MixedLM), BH-significant cells starred | RQ3 |
| **F4** | Metric-correlation matrix | objective-metric × objective-metric Spearman ρ; blocks by family | oracle validation |
| **F5** | Localization by layer | x = layer 0–27; lines = probe AUC, selectivity, patching %-recovered; band shaded | RQ5 |
| **F6** | Steering α×layer heatmap | x = layer, y = ρ; color = dev POC-gain; guardrail-violating cells hatched | RQ6 (S2.3) |
| **F7** | Dose-response w/ failure shading | x = ρ; y = POC-gain & render-success; shade where render < 0.9 or KL > 0.3 | RQ6, RQ7 |
| **F8** | Held-out causal bar chart | bars = {unsteered, steered, random×5 mean±range, FULL}; y = POC (& per-family insets); %-reproduced annotated | RQ6 (S2.4) |
| **F9** | Correspondence cosine matrix + signature match | left: 6×6 cosine matrix {v_Cᵢ, v_full}; right: signature-match grid (steer family × ablation family) | RQ8 (S2.8) |
| **F10** | Purple-slop-index validation | x = human "AI-generated" rating; y = PSI; regression + ρ; per-cell PSI distributions | oracle validation |
| **F11** | Judge reliability | judge-vs-human α & AC1 with bootstrap CIs; marginal-skew bar; per-criterion agreement | reliability gate |
| **F12** | Anti-steerable fraction by task type | bars per task type (seen vs unseen); horizontal 50 % line | RQ7 |
| **F13** | Running-mean cosine stability | x = n examples; y = cosine of running mean; plateau threshold line | S2.0 |

## V.2 Table list

| id | content |
|---|---|
| **T1** | The 24-cell table (sign vectors, tier, seeds, purpose) — §III.1 |
| **T2** | Prompt corpus (58 rows, split-frozen) — §II.2.1 |
| **T3** | Objective-metric definitions + formulas + family — §III.3 / THEORY §T7 |
| **T4** | Res-V alias structure (16 alias chains) — §III.2 / THEORY §T2 |
| **T5** | Per-RQ endpoints, decision rules, multiplicity, outcomes — Parts I & III |
| **T6** | Reliability results (α, AC1, marginals, per-criterion) — §III.8 |
| **T7** | Compute & cost budget (GPU-hours by session, judge $, storage) — Part VI |
| **T8** | Stage-2 experiment summary (S2.0–S2.9: inputs/outputs/compute/interpretation) — Part IV |
| **T9** | Risk register with triggers — Part VIII |
| **T10** | Effect-size + power table (planned vs achieved n per contrast) — §III.7 |

## V.3 Notebook ↔ figure/section mapping (notebooks import `src/`, carry narrative)

The delivered series (`notebooks/00–08`) organizes the same content as a DS-lifecycle
narrative arc: CPU notebooks ship **executed** (real fixture renders, live audits,
synthetic pipeline-validation runs with planted ground truth); GPU notebooks are
**scaffolds** (banner-marked cells, unexecuted until the RUNBOOK sessions). Rendering,
judging, and analysis batch phases run via `scripts/` (RUNBOOK P2–P3) with results
flowing into `05`/`07b`; final paper-figure export re-runs `p19.figures` on real data.

| notebook | phase / status | produces |
|---|---|---|
| `00_overview` | CPU-now (executed) | project map; RQ table; execution-status badges |
| `01_problem_and_data` | CPU-now (executed) | skill + all build-time audits live; 24-cell table + token masses; corpus EDA; split rationale |
| `02_oracle_metrics` | CPU-now (executed) | metric stack on fixtures; POC + frozen conditionals demo; F4, F10 |
| `03_oracle_preference` | CPU-now (executed) | judge template + mock dry-run; α/AC1 + kappa-paradox demo; power tables (T10); F11 |
| `04_stage1_generation` | GPU P0–P1 (scaffold) | pilot 12-gen gate (§III.9); 4,630-gen manifest; per-session acceptance checks |
| `05_stage1_analysis` | analysis (synthetic-validated now; re-run on real data post P2–P3) | MixedLM + style-controlled BT; F1, F2, F3; RQ1–RQ4 decisions incl. null-rule demo |
| `06a_stage2_locate_extract_synthetic` | CPU-now (executed) | planted-direction recovery; probe AUC + selectivity; stability plateau; F5, F13 previews |
| `06b_stage2_locate_extract_gpu` | GPU P4 (scaffold) | S2.0–S2.2 real; F5, F13 |
| `07a_stage2_steer_verify_synthetic` | CPU-now (executed) | S2.3–S2.8 analysis paths validated end-to-end; F6, F7, F8, F9, F12 previews |
| `07b_stage2_steer_verify_gpu` | GPU P5–P7 (scaffold) | S2.3 sweep + `(ℓ*,ρ*,variant*)` freeze; S2.4–S2.9; F6–F9, F12 real |
| `08_results_and_conclusions` | outcome-contingent skeleton (executed) | per-RQ decision slots; honest-null templates; paper hooks |

---

# PART VI — Engineering & reproducibility (lifecycle phase 9)

## VI.1 Repo layout — `src/` modules (one-line specs)

| module | spec |
|---|---|
| `src/config` | load/validate YAML configs; freeze-hash; typed dataclasses |
| `src/skill_assembly` | build system prompts from components+fillers; ADR-009 ±15 % token assertion; filler render-inertness audit (banned-topic list, §II.1.3); PLAN↔skill-file filler-text identity check; LOO/AOI padding; cell→sign-vector map |
| `src/prompts` | prompt corpus loader; leakage audit (case-insensitive whole-word `banned_words` test, §II.2); split freeze by id |
| `src/generation_vllm` | Stage-1 bulk generation (vLLM); fixed sampling; engine/version/seed stamping; checkpoint/resume |
| `src/generation_hf` | HF `.generate` (batched) for Stage-2 steering/verification; same sampling; hookable |
| `src/hooks` | forward/pre-hooks on `model.model.layers[i]`; tuple-output handling; per-decode firing; running-mean capture; add-vector & project-out ops (~200 LOC, unit-tested with mocked modules) |
| `src/activations` | mean-response / last-prompt / first-k capture; per-layer means; stability (cosine plateau) |
| `src/steering` | diff-in-means, PCA/LAT direction, unit-norm; add/ablate; α (abs & norm-relative); KL guardrail; weight-orthogonalization |
| `src/rendering` | Playwright render (determinism recipe §VI.5); desktop 1440×900 + mobile 390×844; DOM-JSON export |
| `src/metrics_dom` | render-success, hermeticity, overflow/overlap, WCAG contrast, Ngo balance/equilibrium/symmetry/regularity, white-space, type-scale |
| `src/metrics_visual` | Hasler colorfulness, dominant colors, figure-ground, visual complexity, PSI |
| `src/judge` | pairwise VLM judge (Gemini primary, GPT-4o audit); both-orders; JSON schema; dry-run/mock mode |
| `src/agreement` | Krippendorff α (ordinal) + Gwet AC1 + bootstrap CIs; marginal report |
| `src/bt_model` | style-controlled Bradley-Terry (Davidson ties); MLE; cluster-bootstrap over prompts |
| `src/mixedlm` | statsmodels MixedLM/GLMM wrappers; factorial model-matrix builder (rank check); convergence fallbacks |
| `src/power` | McNemar sizing; BT simulation power; achieved-n checker |
| `src/figures` | all figures F1–F13 from results tables (matplotlib) |
| `src/manifest` | artifact registry + SHA-256 hashing; config/version pinning; results schema validation |

Tests in `tests/` with fixtures in `tests/fixtures/` (hand-authored HTML pages spanning good/slop/
broken/overflow so every metric has a known-answer case). GPU code unit-tested with **mocked model
objects** (fake `Qwen2DecoderLayer` returning known tuples) so hook logic is verified without weights.

## VI.2 Config schema (YAML keys)

```yaml
# config/model.yaml
model: {name: Qwen/Qwen2.5-Coder-7B-Instruct, dtype: bfloat16, d_model: 3584, n_layers: 28}
sampling: {temperature: 0.7, top_p: 0.9, top_k: 40, repetition_penalty: 1.05, max_new_tokens: 4096, seeds: [0,1,2,3,4]}
# config/skill.yaml
components: {C1: "...", C2: "...", C3: "...", C4: "...", C5: "..."}   # frozen v1 text
fillers:    {F1: "...", F2: "...", F3: "...", F4: "...", F5: "..."}
output_constraint: "..."; beauty_line: "Make it beautiful and well-designed."
token_balance: {target: 85, tol: 0.15}
filler_banned_topics: [header, nav, main, footer, aside, article, section, landmark, semantic,
                       lang, title, meta, aria, accessibility, valid, validate, validation,
                       well-formed, closed, closure, unclosed, lint, linter, addEventListener,
                       onclick, handler, event, guard, error, exception]   # whole-word, fillers only
# config/cells.yaml   (24 cells: id -> sign vector over [C1..C5] or control-type; seeds)
# config/prompts.yaml (58 prompts: id, type, text, difficulty, split); banned_words: [...]  # whole-word, briefs only (§II.2)
# config/steering_grids.yaml  (layers, rho_grid, abs_multipliers, variants, kl_threshold: 0.30, render_min: 0.90)
# config/judge.yaml   (primary: gemini-2.5-flash, audit: gpt-4o, audit_frac: 0.15, temp: 0, rubric_ref)
# config/render.yaml  (desktop: [1440,900], mobile: [390,844], dsf: 1, animations: disabled, network: offline)
# config/steering_frozen.yaml  (WRITTEN by S2.3; layer*, rho*, variant*; hash)   # git-tagged
```

## VI.3 Results schema (JSONL/Parquet columns)

- **generations** `results/generations.parquet`: `gen_id, cell_id, prompt_id, seed, system_variant,
  engine, engine_version, sampling_hash, prompt_tokens, output_tokens, html_path, ts`.
- **metrics** `results/metrics.parquet`: `gen_id, render_success, hermetic, n_overflow, n_overlap,
  axe_violations_by_impact{}, contrast_frac_below_4_5, contrast_min, contrast_median, ngo_balance,
  ngo_equilibrium, ngo_symmetry, align_regularity, whitespace_ratio, density, n_font_sizes,
  n_font_families, type_scale_adherence, colorfulness, n_dominant_colors, figure_ground,
  visual_complexity, psi, psi_hue, psi_gradient, psi_inter, psi_centered, uiclip, clip_relevance, poc`.
- **judgments** `results/judgments.parquet`: `judgment_id, edge, cellA, cellB, prompt_id, seedA, seedB,
  order, judge_model, winner, confidence, per_criterion{}, rationale, consistent, ts`.
- **activations_meta** `results/activations_meta.parquet`: `example_id, cell_id, prompt_id, seed,
  layer, variant, mean_vec_path, norm`.
- **steering_runs** `results/steering_runs.parquet`: `run_id, stage(S2.x), layer, rho, abs_mult,
  variant, arm, prompt_id, seed, kl, render_success, poc, html_path`.

## VI.4 Artifact manifest + hashing
`src/manifest` records every artifact (HTML, PNG, DOM-JSON, activation shard, results file) with a
**SHA-256**, its producing config hash, engine+version, and git commit. Artifacts live under
`artifacts/` (gitignored, `.gitignore` already excludes `artifacts/`, `results/raw/`, `*.safetensors`,
`*.pt`). The manifest itself is committed. Re-running with an unchanged config+seed must reproduce
identical hashes for CPU artifacts (render determinism) and identical generations within-engine.

## VI.5 Determinism policy
- **Engine split (ADR-002):** vLLM = Stage-1 bulk only; HF = all activation/steering; never
  cross-compare; every comparison within-engine; engine+version+sampling hashed per row.
- **Seeds** explicit everywhere (config); Torch/NumPy/Python seeded; `do_sample=True` with fixed seed.
- **Render determinism (`06_playwright_determinism`):** fixed viewport 1440×900 (+390×844), DSF 1,
  `animations:'disabled'`, caret hidden, `document.fonts.ready` awaited, offline/network-blocked,
  `networkidle` + settle delay, **pinned Chromium** (`/opt/pw-browsers`, do not `playwright install`)
  + pinned Playwright; all screenshots generated in one environment.
- **Pinned versions** (recorded in `env.lock`): torch, transformers, vllm, playwright, chromium,
  statsmodels, numpy, scipy, scikit-learn, pingouin (α/AC1), choix/custom BT.

## VI.6 RUNBOOK.md outline (Colab session-by-session; GPU phase)

Each session: **GPU · est. time · inputs · outputs · checkpointing · resume · acceptance check**
(the orchestrator eyeballs the acceptance numbers before proceeding — the execution-phase review gate).

| # | session | GPU | est. | inputs | outputs | acceptance check (eyeball before next) |
|---|---|---|---|---|---|---|
| 1 | **Pilot** | L4 | 0.5 h | skill+prompts | 12 gens, screenshots | render ≥ 11/12; FULL≠NOSYS visibly; POC gap > 0 (§III.9) → else fallback |
| 2 | **Stage-1 gen A** | L4 | 3 h | cells, dev prompts | ~2,000 dev gens | render-success ≥ 0.9 overall; no engine errors; checkpoints on Drive every 200 |
| 3 | **Stage-1 gen B** | L4 | 3 h | remaining dev + held gens | ~2,630 gens | cumulative 4,630; spot-render 20 pages OK |
| 4 | **Render + metrics** | **CPU** | 2 h | all HTML | metrics.parquet; F4, F10 | PSI validates (ρ≥0.4) or demote; metric ranges sane |
| 5 | **Judging** | **CPU/API** | 2 h | screenshots | judgments; α/AC1; BT | reliability gate passes (α≥0.667 or AC1≥0.80) → else fallback cascade |
| 6 | **Extract + locate** | A100 | 2 h | FULL/NEUTRAL dev gens | v_l, probes, patching; F5, F13 | cosine plateau reached; a mid-band probe AUC ≥ 0.80 |
| 7 | **Dev sweep** | A100 | 4 h | v_l, dev subset | F6, F7; freeze (ℓ*,ρ*,var) | a guardrail-satisfying POC-gain>0 config exists → tag `steer-frozen` |
| 8 | **Held-out verify** | A100 | 3 h | frozen config, held-out | S2.4–S2.7; F8, F12 | success criterion evaluated; controls behave (random ≠ steered) |
| 9 | **Stretch** | A100 | 2 h | AOI vectors, subsets | S2.8–S2.9; F9 | correspondence decision; early-token comparison |
| — | **buffer/re-runs** | A100 | 3 h | — | — | contingency (contrast noise, under-power, sweep re-do) |

**Resume logic:** every session reads the manifest, skips already-hashed units, resumes from the last
checkpoint (≤90-min idle kills expected). All artifacts to Drive, never VM disk.

## VI.7 Cost table (reconciled; T7)

| item | quantity | rate | cost |
|---|---|---|---|
| Stage-1 vLLM generation | ~6 L4-h | ~5 CU/h | 30 CU |
| Stage-2 A100 (capture+sweep+verify+stretch+buffer) | ~14 A100-h | ~15 CU/h | 210 CU |
| Pilot | 0.5 L4-h | ~5 CU/h | 3 CU |
| **Colab compute units total** | | | **≈243 CU** → Pro+ (500 CU/$50) covers it; **≈$50–65** |
| Judge — Gemini 2.5 Flash primary | ~4,420 both-order calls | $0.30/$2.50 per 1M | **≈$7** |
| Judge — GPT-4o audit (15 %) | ~664 calls | $2.50/$10 per 1M | **≈$7** |
| **Judge total** | ~5,084 calls | | **≈$14** |
| Storage (HTML+PNG+DOM-JSON+activations) | ~6,900 units + means | | **≈4–5 GB Drive** |
| **Grand total (compute + judge)** | | | **≈$65–80** |

Render + all objective metrics + judge dry-run + statistics run on **CPU/API (no GPU)**; only
sessions 1–3, 6–9 need a GPU. Judge cost is trivial; two judges on the full set would still be < $120
(D6) if desired.

---

# PART VII — Statistical appendix hooks (what THEORY.md must derive)

`THEORY.md` shares symbols with this PLAN so the two files are cross-readable. Each item lists the
derivation and the exact notation to use.

- **§T1 — DOE estimability.** Enumerate the 2⁵⁻¹ principal fraction (I = ABCDE); prove the 24-cell
  dedup (all-`+` = FULL; single-`+` = AOI; LOO/NEUTRAL excluded by odd parity). Symbols: factors
  A…E = C1…C5, sign vector `x∈{±1}⁵`.
- **§T2 — Aliasing.** Derive the full alias chains from I = ABCDE; show mains ⟂ 4FI and 2FI ⟂ 3FI ⇒
  resolution V; state the "3FI+ negligible" assumption. Tabulate all 16 chains (T4).
- **§T3 — MixedLM.** Write the crossed/nested model `y_{cps}=μ+τ_c+u_p+v_{cp}+ε`; derive REML
  estimation intuition; justify random prompt (& seed-in-prompt) effects vs pseudoreplication; state
  the factorial model matrix and rank.
- **§T4 — Chance-corrected agreement.** Krippendorff α = 1 − D_o/D_e (ordinal distance); Gwet AC1 with
  `p_e^γ = (1/(q−1))Σπ_k(1−π_k)`; the kappa paradox under skew; why AC1 is stable; bootstrap-CI
  procedure. Symbols match §III.8.
- **§T5 — Bradley-Terry with covariates.** `P(i≻j)=σ((β_i−β_j)+γ^⊤(s_i−s_j))`; MLE = logistic
  regression with item indicators + style covariates; Davidson tie term; identifiability (β_NEUTRAL=0);
  cluster-bootstrap over prompts. Symbols: β strengths, s style vector, γ style coefficients.
- **§T6 — Power.** Derive the McNemar paired-proportion `n`-formula (reproduce **~200 pairs for 60/40**,
  ~80 for 65/35, ~780 for 55/45 at α=.05, power=.80); BT simulation-power protocol. Symbols: p_d, δ.
- **§T7 — Objective-metric formulas.** WCAG relative luminance + contrast ratio; Ngo balance BM,
  equilibrium EM, symmetry; Hasler colorfulness M (rg, yb opponent); PSI composite; POC definition
  (oriented z-scores). Cross-index to §III.3/§III.4.
- **§T8 — Diff-in-means as optimal linear discriminant.** Show that under **shared class covariance
  Σ**, the Bayes-optimal linear discriminant direction is `Σ⁻¹(μ_skill−μ_neutral)`, and diff-in-means
  `(μ_skill−μ_neutral)` is its whitening-free counterpart — the causal mean shift Arditi/CAA rely on;
  discuss when Σ≈I makes them coincide. Symbols: `v_l=\bar h_l^{skill}−\bar h_l^{neutral}`.
- **§T9 — Activation addition/ablation formalism.** Addition `h←h+α v̂`; directional ablation
  `h←h−v̂v̂^⊤h`; weight-orthogonalization `W_out←(I−v̂v̂^⊤)W_out`; norm-relative α; the KL-guardrail
  objective. Relate to LRH (`park2023lrh`).
- **§T10 — What the causal test establishes.** Frame steering as a `do`-operator on activations:
  `do(h_{ℓ*} := h_{ℓ*}+α v̂)`; the held-out addition = an interventional test of sufficiency, the flip
  test = interventional necessity; the norm-matched random control addresses non-identifiability;
  internal-validity threats (self-repair, interpretability illusion `heimersheim2024patching`, spurious
  extraction cues `tan2024analysing`) and how each control neutralizes them. State what can and cannot
  be concluded ("a causally sufficient/necessary direction," not "the unique design direction").

---

# PART VIII — Risk register & timeline

## VIII.1 Risk register with triggers (T9)

| risk (source) | trigger (observable) | action |
|---|---|---|
| Model can't apply a 5-part skill (`D1`) | pilot: FULL≈NOSYS, POC gap ≈ 0 after format fixes | ADR-001 fallback to Llama-3.1-8B; restart both stages (only sanctioned swap) |
| Skill effect is real but small | FULL−NEUTRAL POC δ < 0.2, preference < 55/45 | keep (still measurable); the *components* may still differ; report modest effect honestly |
| Judge unreliable (`gwet2008ac1`) | α < 0.667 **and** AC1 < 0.80 | §III.8 fallback cascade (rubric→judge-swap→more humans→objective-only) |
| Kappa paradox (skew) | α low, marginals very skewed | report AC1 (gate accepts under demonstrable skew) — designed-for |
| Under-power on a confirmatory edge (`04_stats`) | achieved n < required n at observed δ | raise seed-pairs (pre-stated, up to 4k budget); else objective-only null decision |
| Extraction mean unstable (`chen2025persona`) | cosine plateau not reached at 300 | high-variance contrast; expect weak steering; report; try first-k variant |
| No clean localization (`engels2024notlinear`) | no layer with AUC≥0.8 & patch≥25 % | RQ5 "diffuse"; go multi-layer/subspace in S2.3 |
| Steering doesn't beat unsteered (`tan2024analysing`) | S2.4 criterion unmet | **RQ6 honest null** (design not linearly steerable); tighten CIs to show real null |
| Non-identifiability (arXiv:2602.06801) | random control also lifts POC | downgrade to "norm effect"; do not claim a specific direction |
| Not-unique direction (`wollschlager2025cones`) | flip test no attenuation | "sufficient, not necessary"; test 2–4D cone |
| Anti-steerable inputs (`tan2024analysing`) | anti-steerable fraction ≥ 50 % | report failure map (F12); scope the claim to steerable regime |
| Steering breaks coherence (`taimeskhanov2026strength`) | optimum only above KL 0.30 | keep guardrail; report Pareto; no "win by gibberish" |
| Side-effects on non-UI code (`lee2024cast`) | algorithmic pass-rate drops > 10 % | conditional (CAST) gating; report trade-off |
| Render nondeterminism (`06_playwright`) | screenshot hash drift | pinned Chromium+viewport; regenerate all together on version change |
| Engine mismatch (`04_hooks`) | vLLM/HF numbers compared | forbidden; re-generate baseline in HF for any Stage-1↔2 compare |
| Forking paths over metrics/cells | post-hoc metric picking | PREREGISTRATION freeze (git tag) before GPU; Holm/BH split fixed |
| Colab session kill (~90 min idle) | disconnect mid-run | resumable, manifest-skip, Drive checkpoints every 200 units |

## VIII.2 Effort estimates per phase (engineering hours)

| phase | work | hours |
|---|---|---|
| P-CPU | `src/` (18 modules) + tests + fixtures + CPU execution (ADR-007) | 60–80 |
| Prereg | freeze PREREGISTRATION, git tag | 4 |
| P0 pilot | run + evaluate | 3 |
| P1 gen | Stage-1 generation orchestration | 6 (mostly GPU wall-clock) |
| P2 metrics | render + metrics at scale | 6 |
| P3 judge | judging + reliability + BT | 10 |
| Analysis | MixedLM + BT + figures F1–F4 | 16 |
| P4–P7 Stage-2 | extract/locate/sweep/verify/stretch + figures F5–F13 | 40 |
| P8 paper | two-part write-up + outcome templates | 30 |
| **total** | | **≈175–200 h** |

## VIII.3 Definition-of-done checklist (per artifact)

- **`src/` package:** every module has unit tests; all CPU-safe code **runs and passes here**; GPU code
  import-guarded + mock-tested; `env.lock` pinned; leakage-audit + filler-inertness-audit +
  filler-text-identity + token-balance + factorial-rank + render-determinism tests green.
- **PREREGISTRATION.md:** hypotheses, 24-cell table, endpoints, all gates, null rule, Holm/BH split,
  power targets, amendments policy — **git-tagged `prereg-v1` before any GPU run**.
- **Notebooks:** each imports `src/`, runs end-to-end on available data, GPU cells clearly marked
  unexecuted with exact run instructions; narrative + acceptance checks inline.
- **RUNBOOK.md:** 9 sessions with GPU/time/inputs/outputs/checkpoint/resume/acceptance filled.
- **Figures/tables:** F1–F13, T1–T10 generated from results by `src/figures` (no hand-editing);
  outcome-contingent captions.
- **Paper:** two-part scaffold with result templates for **every** RQ outcome branch (incl. nulls);
  novelty statement (`SYNTHESIS §6`) stated precisely; all method choices cite `refs.bib`.
- **Oracle validated:** PSI ρ≥0.4 (or demoted); UIClip ρ≥0.3 (or dropped); reliability gate passed or
  fallback documented — **before** any quality claim is admitted.

---

## Appendix A — Reconciliation summary (all numbers agree)

- **Distinct cells:** 24 = 4 controls + 5 LOO + 5 AOI + 10 three-component. Res-V 16-run fraction =
  FULL + 5 AOI + 10 F-cells (6 of the 16 coincide with named cells; deduped).
- **Stage-1 generations:** dev 4,000 (14×5×40 + 10×3×40) + held-out 630 (4×5×18 + 5×3×18) = **4,630**.
- **Stage-2 generations:** ≈2,300 HF + 400 forward passes.
- **Extraction pairs:** 200/side (40 dev prompts × 5 seeds), cosine-plateau-gated.
- **Judgments:** 1,916 (Stage-1) + 294 (Stage-2) = **2,210 pairs ≈ 4,420 primary calls** (+664 audit);
  within the 2–4k budget.
- **Compute:** ~6 L4-h + ~14 A100-h ≈ **243 CU ≈ $50–65**. **Judge ≈ $14.** Storage ≈ 4–5 GB.
- **Model:** `Qwen/Qwen2.5-Coder-7B-Instruct` (locked, ADR-001), both stages; fallback Llama-3.1-8B
  only on pilot failure.

---

## Appendix B — Exact objective-metric formulas (self-contained; implements §III.3)

Computed on the **rendered** DOM/screenshot only (CLAUDE.md). `src/metrics_dom` uses Playwright
`boundingBox()` + `getComputedStyle`; `src/metrics_visual` uses the desktop PNG pixels.

**B.1 Render success / hermeticity (family V).** Binary. `render_success = 1` iff the page loads,
paints, and throws no console error under offline context. `hermetic = 1` iff zero external network
requests are attempted (route-abort count = 0). A non-hermetic page has `render_success` re-scored 0
for POC (ADR-006).

**B.2 WCAG 2.x contrast (family A).** For an sRGB channel `C∈[0,1]`:
`C_lin = C/12.92 if C≤0.03928 else ((C+0.055)/1.055)^2.4`; luminance
`L = 0.2126 R_lin + 0.7152 G_lin + 0.0722 B_lin`; ratio between lighter L₁, darker L₂:
`CR = (L₁+0.05)/(L₂+0.05) ∈ [1,21]`. Per text node compute CR(text, effective background); report
`contrast_frac_below_4_5`, `contrast_min`, `contrast_median`. AA thresholds 4.5 (normal) / 3.0 (large).

**B.3 Ngo layout (family L)**, from bounding boxes; each ∈ [0,1], higher = better:
`BM = 1 − (|BM_v| + |BM_h|)/2` (balance; BM_axis = normalized signed difference of Σ(area×dist-to-axis)
on the two sides); `EM = 1 − (|EM_x| + |EM_y|)/2` (equilibrium; EM = normalized center-of-mass offset
from frame center); `SYM` = normalized reflected-object-measure agreement across vertical/horizontal/
diagonal axes. `align_regularity = 1 − (n_distinct_edges / n_elements)` over x- and y-edge positions
(fewer shared edges → more regular); `whitespace_ratio = 1 − occupied_area/viewport_area`;
`density = occupied_area/viewport_area`.

**B.4 Typography (family T).** `n_font_sizes`, `n_font_families` from computed styles;
`type_scale_adherence` = fraction of adjacent size ratios within ±10 % of a common modular ratio r
(fit r∈{1.125,1.2,1.25,1.333,1.414,1.5} by best adherence).

**B.5 Hasler colorfulness (family C).** In opponent space `rg = R−G`, `yb = ½(R+G) − B`:
`σ_rgyb = √(σ_rg² + σ_yb²)`, `μ_rgyb = √(μ_rg² + μ_yb²)`, `M = σ_rgyb + 0.3·μ_rgyb`. Also
`n_dominant_colors` (quantized palette size), `figure_ground` (fg vs bg mean-color distance).

**B.6 Visual complexity (family X).** Edge/quadtree density: `complexity = quadtree_leaf_count`
(space-based decomposition to a fixed threshold) normalized by max; inverted-U prior
(`reinecke2013predicting`).

**B.7 Purple-slop index (composite; validate per §III.3.1).**
`PSI = 0.30·hueFrac[260°,290°] + 0.30·gradientBgPrevalence + 0.25·InterRobotoShare +
0.15·centeredHeroFlag`, each subcomponent ∈ [0,1]: `hueFrac` = share of salient pixels with HSV hue
in [260°,290°]; `gradientBgPrevalence` = fraction of large/hero elements with a `linear-gradient`
background; `InterRobotoShare` = fraction of text using Inter/Roboto/system-ui; `centeredHeroFlag` = 1
if a large centered flex block sits in the top viewport third. Report subcomponents + composite.

**B.8 Primary Objective Composite (POC).** Over dev units, z-score each core metric, orient so higher
= better, average: `POC = mean_z(+align_regularity, +whitespace_ratio, +type_scale_adherence,
+contrast_pass_rate, −overflow_overlap_count, −PSI, −|colorfulness − c*|)`, where
`contrast_pass_rate = 1 − contrast_frac_below_4_5`, `overflow_overlap_count = n_overflow + n_overlap`,
and `c*` = median Hasler-M of human-preferred pages (calibrated on the §III.8 subset). Render-failed
units excluded (counted in family V). **Pre-specified conditionals (§III.4, part of the frozen
endpoint):** PSI failing its admission gate ⇒ the confirmatory POC drops the −PSI term (6-term POC);
fewer than 30 human-preferred pages ⇒ `c*` = median Hasler-M of the dev FULL-cell generations.

## Appendix C — Verbatim judge prompt template (implements §III.8; `src/judge`)

**System message (cached):**
> You are a senior product designer evaluating two rendered web user interfaces, A and B, that were
> built for the SAME brief. Judge which is the better-designed interface FOR THAT BRIEF. Base your
> judgment on deliberate, brief-appropriate design choices — not on which page is merely longer, more
> colorful, or more filled-in. A page is not better for having more elements or brighter colors; it is
> better for coherent color, clear layout and hierarchy, considered typography, quality component
> patterns, restraint (absence of generic "AI-slop" tells such as purple gradients, Inter/Roboto,
> centered hero-with-a-big-number, three identical icon cards, uniform rounded corners, excessive
> animation), and fit to the brief. Return ONLY valid JSON in the specified schema. Do not add prose
> outside the JSON.

**User message (per pair):**
> BRIEF: "{brief_text}"
>
> You are shown two screenshots: image A (first) and image B (second), both rendered at 1440×900.
> Evaluate each on: color/palette coherence; layout & visual hierarchy; typography; component/pattern
> quality; restraint (absence of AI-slop tells); overall fit to the brief.
>
> Return JSON exactly:
> ```json
> {"winner": "A" | "B" | "tie",
>  "confidence": 1-5,
>  "per_criterion": {"color":"A|B|tie","layout":"A|B|tie","typography":"A|B|tie",
>                    "components":"A|B|tie","restraint":"A|B|tie","fit":"A|B|tie"},
>  "rationale": "<=40 words"}
> ```

**Adjudication (both orders):** call once as (A,B), once as (B,A). Map the second call's winner back to
true labels. If the two calls disagree on the winner → record **tie** (position-bias control). Store
both raw verdicts, the consistency flag, and mean confidence. Judge temperature = 0.

---

*End of PLAN.md. Freeze the confirmatory subset into `PREREGISTRATION.md` and git-tag before any GPU
execution.*




