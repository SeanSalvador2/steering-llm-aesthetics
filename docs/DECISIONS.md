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
method. **Status: provisional** — research dossier must confirm feasibility facts
(license, architecture dims, tooling support, VRAM); becomes `accepted` before any code
depends on model internals.

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
layer patch) are ~200 lines of auditable code. **Status: provisional** — research agent
verifies no Qwen2-specific hooking gotchas.

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
baselines are competitive or better for causal steering. Research dossier must confirm
this evidence before the plan freezes. **Status: provisional.**
