# CLAUDE.md — Project 19: Anatomy of a Design Skill

Two-stage research study on a single open-weights code model. **Stage 1 (black-box):**
factorial ablation of a frontend-design skill — which components of the guidance carry
the causal weight on UI quality. **Stage 2 (white-box):** mechanistic interpretability —
locate where the guidance acts in the model's activations, extract a "clean-design"
steering vector, and causally verify it by steering with **no design prompt**. Full brief:
`docs/BRIEF.md`. Authoritative plan: `PLAN.md` (once written). Decision log: `docs/DECISIONS.md`.

## The model (locked)

**`Qwen/Qwen2.5-Coder-7B-Instruct`** — used for BOTH stages. Stage 2 requires white-box
activation access, so the subject model is open-weights and self-hosted; Stage 1 must run
on the same model or the ablation↔interpretability link is severed. Do not swap models
silently. Changing the model requires an ADR in `docs/DECISIONS.md` and restarts both
stages. Recorded fallback (same rule applies): `meta-llama/Llama-3.1-8B-Instruct`.

API models (e.g. GPT/Claude/Gemini) may be used ONLY as evaluation judges — never as the
subject model.

## Commit policy (strict)

- **No AI attribution of any kind** in commits, PRs, code, comments, or docs: no
  `Co-Authored-By: Claude`/any-AI trailer, no "Generated with …", no model identifiers,
  no session links. Plain, professional commit messages only (imperative subject,
  explanatory body when warranted).
- Develop on branch `claude/design-skill-ablation-interp-s1jvet`; push with
  `git push -u origin <branch>`.
- Commit at meaningful milestones; never commit broken tests or half-written files.

## Compute policy (current phase)

- **No GPU / no subject-model inference is executed in this environment.** Anything that
  loads Qwen weights, generates UI code, or extracts activations must be complete, tested
  for logic where possible (mocks/fixtures), import-guarded, and documented with exact run
  instructions (`RUNBOOK.md`) — but left unexecuted. It will be run later on Colab Pro.
- Everything CPU-safe MUST actually run here and pass: Playwright rendering of fixture
  HTML, the objective-metrics stack, judge harness in dry-run/mock mode, statistics on
  synthetic data, all unit tests.
- Chromium for Playwright is preinstalled at `/opt/pw-browsers` (do not `playwright install`).

## The correctness oracle (non-negotiable — may not be weakened)

Every quality claim (an ablation delta OR a steering delta) requires **two independent
signals**:

1. **Objective, computable metrics on the rendered output** (headless browser, rendered
   DOM — never raw code strings): render success, WCAG/axe violations, color-contrast
   ratios, alignment consistency, spacing regularity, overflow/overlap counts, palette
   statistics. Deterministic and unfoolable.
2. **A pairwise preference protocol** (VLM judge, human-validated subset) gated behind
   chance-corrected inter-rater agreement and a power check. A preference delta that
   fails reliability or power gates does not count.

An effect that moves neither signal is reported as **null**. **Stage 2's bar:** a claimed
"design direction" is real only if steering it with no design prompt causally reproduces a
measurable quality gain on held-out prompts. A direction that correlates but does not
causally steer is a hypothesis, not a finding. If no clean steerable direction exists,
that null is itself a result and is written up honestly — never forced, never buried.

## Analysis discipline

- Every generation cell runs with **≥ 3 seeds** (headline cells 5). Report distributions
  and effect sizes with uncertainty — never single outputs.
- Statistics: mixed-effects / clustered analyses respecting the prompt×seed structure;
  multiple-comparison control across components; preregistered decision rules
  (`PREREGISTRATION.md`) frozen before any GPU run.
- Confound controls are part of the design: length-matched neutral-instruction cell and
  a "make it beautiful" one-liner cell, in addition to skill-absent and full-skill.
- Generated pages must be **hermetic**: single-file HTML, inline CSS/JS, no external
  network fetches at render time (deterministic rendering).

## Orchestration rules

- One heavy-lifting subagent at a time — never a concurrent swarm. The orchestrator
  plans, directs, and reviews; subagents implement.
- Subagents do not run `git commit`/`push` unless explicitly instructed; the orchestrator
  reviews diffs before anything lands.
- Notebooks carry narrative + orchestration + visualization; reusable machinery lives in
  `src/` with unit tests. Notebooks import from `src/`.
- Configs in YAML; seeds explicit everywhere; results as JSONL/Parquet with a versioned
  schema; artifacts (HTML, screenshots, activations) under `artifacts/` (gitignored,
  manifest-tracked).

## Repo map (grows as the project is built)

- `docs/BRIEF.md` — original project brief (do not edit).
- `docs/DECISIONS.md` — ADR-style decision log (why choices were made).
- `research/` — literature dossier: per-paper notes, synthesis, `refs.bib`.
- `PLAN.md` — the authoritative, self-contained master plan (both stages).
- `THEORY.md` — derivations: experimental-design statistics + interpretability math.
- `src/` — Python package (metrics, rendering, judging, stats, hooks, steering).
- `notebooks/` — the scaffolded DS-lifecycle notebooks (unexecuted GPU cells clearly marked).
- `paper/` — the two-part paper scaffold with outcome-contingent result templates.
- `SEAN-README.md` — plain-language companion explaining everything.
- `RUNBOOK.md` — exact Colab execution instructions for the GPU phase.
