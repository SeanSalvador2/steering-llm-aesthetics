# Decision Log (ADR style)

Each entry: context → decision → rationale → status. Status is `accepted`,
`provisional` (pending evidence from the research dossier), or `superseded`.
Methodological choices here must be *defended* in `PLAN.md`/the paper with
experiments or literature, not assertion.

---

## ADR-001 — Subject model: Qwen2.5-Coder-7B-Instruct

**Context.** Stage 2 needs white-box activation access → open weights, self-hosted,
single Colab GPU. Stage 1 must use the same model. The model must (a) produce working
single-file HTML/CSS UIs reliably, (b) exhibit the stereotypical "default LLM aesthetic"
so the skill has an effect to move, (c) follow multi-part instructions well enough to
apply the skill, (d) be hookable with standard tooling.

**Decision.** `Qwen/Qwen2.5-Coder-7B-Instruct`, greedy-free sampling (temperature per
plan), bf16, for both stages.

**Rationale.** Strongest open-weights code specialist at a size that fits Colab
(≈15 GB bf16 → A100 40 GB comfortable; L4 24 GB workable; 4-bit fallback for
generation-only passes). Code-specialist instruction following; widely reported to
default to generic "bootstrap/purple-gradient" styling — an ideal subject. Apache-2.0.
Supported by HF Transformers hooks and TransformerLens-class tooling.

**Alternatives.** Llama-3.1-8B-Instruct (better public SAE ecosystem via Llama-Scope,
weaker code quality) — recorded fallback. Gemma-2-9B-it (best public SAEs via
Gemma-Scope, weakest frontend code) — rejected; SAEs are a stretch goal, not the primary
method. **Status: accepted** (dossier D1: Apache-2.0 ungated; standard `Qwen2ForCausalLM`,
fully hookable; config verified d=3584, 28 layers, GQA 28/4, ~15.2 GB bf16; Persona
Vectors demonstrated diff-in-means extraction on the same family, Qwen2.5-7B-Instruct).
Residual risk tracked in PLAN: pilot must confirm the model visibly applies a 5-part
skill; fallback triggers only on that pilot failing.

## ADR-002 — Interpretability tooling: HF Transformers + minimal custom hooks

**Context.** Stage 2 needs: capture residual-stream activations per layer, add a vector
during generation, run controlled patches. Colab memory is the binding constraint.

**Decision.** Plain `transformers` + a small, unit-tested hook module (`src/hooks/`)
as the primary mechanism (capture + steering via `register_forward_hook` /
`register_forward_pre_hook` on decoder layers). TransformerLens/nnsight optional for
exploratory analysis only, never on the critical path.

**Rationale.** Zero conversion overhead (TransformerLens roughly doubles load memory and
its KV-cache path is heavier), works identically with quantized fallbacks, transparent
enough to document in THEORY.md, and the operations we need (mean-capture, vector add,
layer patch) are ~200 lines of auditable code. **Status: accepted** (dossier D2: vLLM
cannot inject activations mid-decode, so steering must run on HF; decoder layers hook at
`model.model.layers[i]` with tuple outputs; capture running means, not full sequences).
**Engine policy (binding):** vLLM for Stage-1 bulk generation throughput; HF for all
activation capture/steering; never compare generations across engines — every comparison
is within-engine, with engine/version/sampling config recorded per run.

## ADR-003 — Contrast baseline: length-matched neutral instructions (not empty prompt)

**Context.** Comparing "skill present" vs "no system prompt" confounds *design content*
with *the mere presence of a long instruction block* (prompt mass changes attention
patterns, verbosity, compliance behavior).

**Decision.** The ablation includes, and Stage 2's difference-in-means contrasts
against, a **length-matched neutral-instruction control** (equally long, equally
imperative, design-irrelevant content, e.g. code-hygiene instructions that do not touch
visual style). Also included: a 5-word "make it beautiful" cell (does 500 tokens beat 5
words?) and the bare no-system-prompt cell.

**Rationale.** Isolates the *design* signal in both stages; the steering vector then
encodes "design guidance content," not "instruction-following mode." This is the
project's main added confound control. **Status: accepted.**

**Refinement (plan review).** Neutral/filler text must additionally be **render-inert**:
it may not mandate anything that changes the rendered DOM tree, element/attribute
choices, or render outcome — otherwise the control itself moves measured metrics
(semantic landmarks and `lang` are axe-visible; tag-closure affects render-success).
The illustrative "code hygiene" examples above are superseded by the binding filler
inertness rule + build-time banned-topic audit in PLAN §II.1.3 / canonical_skill_v1.

## ADR-004 — Ablation design: LOO + AOI + fractional interaction block (not naive 2^5)

**Context.** 5 skill components → 32 combinations × prompts × seeds explodes; most
combinations answer no specific question.

**Decision.** Three planned tiers: (1) **leave-one-out** (full skill minus each
component) → necessity; (2) **add-one-in** (each component alone) → sufficiency;
(3) a **fractional-factorial block** (resolution-V half fraction or targeted 2^3 on the
top components) → two-way interactions. Plus the four control cells (ADR-003). Exact
cell table, seed counts, and power analysis fixed in PLAN.md.

**Rationale.** Answers necessity, sufficiency, and interaction with ~⅔ fewer
generations than the full factorial; maps to a clean paper narrative. **Status:
accepted** (exact fraction: fixed in PLAN).

## ADR-005 — Preference protocol: VLM-judge pairwise + human-validated subset

**Decision.** Pairwise screenshot comparisons by a strong API VLM judge, both
presentation orders (position-bias control), anchored rubric; judge validated against a
human-labeled subset (target: chance-corrected agreement gate, e.g. Krippendorff's α ≥
0.67 provisional); Bradley-Terry aggregation to cell-level utilities; power analysis
gates every claimed delta. Judge model choice + cost table: research dossier.
**Status: accepted** (judge model TBD in dossier).

## ADR-006 — Hermetic single-file HTML outputs

**Decision.** The model is always instructed to emit one self-contained HTML file
(inline CSS/JS, no external assets/CDNs/fonts). Rendering in Playwright runs with
network disabled; a page that fetches anything external is scored as non-hermetic.

**Rationale.** Deterministic, offline-reproducible rendering; objective metrics never
depend on network state; render-failure is itself a metric. **Status: accepted.**

## ADR-007 — Build order: src/ machinery before notebooks; CPU half executed now

**Decision.** Supporting scripts (`src/` + tests + fixtures) are built and *executed*
(CPU-only: rendering, metrics, judge dry-run, stats on synthetic data) before the
notebooks are scaffolded; notebooks import `src/` and carry the narrative. GPU-dependent
code is written, unit-tested with mocked model objects where feasible, and left
unexecuted per compute policy.

**Rationale.** The oracle is load-bearing ("build and trust the metrics first" — brief's
trap list); notebooks stay readable; the user runs GPU cells later against tested code.
**Status: accepted.**

## ADR-008 — SAE route demoted to stretch extension

**Decision.** Primary Stage-2 method: difference-in-means steering vector (+ probing and
activation patching for localization). SAE-feature steering is an optional extension,
pursued only if the primary path lands and budget remains.

**Rationale.** No public SAE suite exists for Qwen2.5-Coder; training one is out of
scope on Colab; recent steering-benchmark evidence suggests simple mean-difference
baselines are competitive or better for causal steering. **Status: accepted** (dossier
D9: AxBench shows DiffMean ≥ SAE steering at scale; no Qwen2.5-Coder SAE suite exists —
Qwen-Scope covers Qwen3/3.5 only; SAE decompositions of steering vectors are unfaithful.
If ever pursued, it is a clearly-labeled cross-model transfer demo, off the critical path).

## ADR-009 — Component content-orthogonality (from dossier review)

**Context.** The drafted canonical skill embeds negative constraints inside C1–C4
("no purple gradients" in C1, "not a centered hero" in C2, "don't default to Inter" in
C3) while C5 is also a negative-constraint component — so ablating C5 would not remove
negative guidance, and component effects would not be attributable to distinct content.

**Decision.** Components must be content-orthogonal in the frozen skill: C1–C4 carry
only positive/prescriptive guidance for their topic; ALL negative constraints live in
C5. PLAN.md fixes the revised text (canonical_skill v1) and token-balance rules. A
"realistic mixed" variant (negatives interleaved as real skills write them) may be added
as a robustness cell, not the primary design. **Status: accepted.**

## ADR-010 — Skill text finalized under the exact tokenizer (pre-freeze)

**Context.** The skill's token accounting was originally estimated as words × 1.33.
Running the exact Qwen2.5-Coder tokenizer during the engineering stage revealed two
violations the estimate had masked: (1) C5 measured 104 tokens — ~28 % over the component
mean and outside the preregistered ±15 % band (ADR-009) — because BPE fragments its
semicolon list and hyphenated compounds; (2) fillers ran ~10 % lighter than their matched
components, so FULL (391 exact tokens) vs NEUTRAL (347) was not the length-match ADR-003
promises at cell level.

**Decision.** Pre-freeze (sanctioned: PREREGISTRATION's tag conditions include "the skill
text is final"): (1) C5 minimally reworded to 88 tokens — in-band — with all eleven
semantic constraints preserved and verified by a dedicated test; BPE-friendly phrasing
(hyphen chains broken), only the non-constraint adjective "overused" dropped. (2) Strict
build-time filler equalization: each Filler-i padded/trimmed deterministically to within
±2 tokens of its component using a frozen, inertness-audited padding-clause pool;
consequence tests assert every cell's system-prompt mass within ±10 tokens of FULL.
(3) All nominal token figures in PLAN/PREREGISTRATION/canonical_skill re-anchored to
exact counts (estimate path retained only as the documented no-tokenizer fallback).

**Rationale.** Widening the ±15 % band would weaken a preregistered rule to accommodate a
tokenization artifact; accepting the imbalance would make the C5 necessity contrast
incommensurable with C1–C4 and leave an 11 % mass gap inside the project's flagship
confound control. Fixing the text and enforcing equalization in code keeps both rules
intact before anything is frozen or run. **Status: accepted.**
