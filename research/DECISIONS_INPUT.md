# DECISIONS_INPUT — Evidence-backed recommendations on D1–D12

Each: recommendation · evidence (BibTeX keys / notes) · confidence (high/med/low). These feed the ADRs in `docs/DECISIONS.md` and PLAN.md.

---

## D1 — Confirm/overturn Qwen2.5-Coder-7B-Instruct as subject model
**Recommend: CONFIRM (ADR-001 → accepted).** **Confidence: HIGH.**
- **License Apache-2.0**, no gating; standard `Qwen2ForCausalLM` (fully HF-hookable). Config verified: $d=3584$, **28 layers**, 28 heads / 4 KV (GQA), SwiGLU, vocab 152064, bf16, ~15.2 GB → fits L4-24GB/A100 (`qwen2025modelcard`, config.json; `hui2024qwencoder`).
- **Same family as a validated interp result:** Persona Vectors extracted diff-in-means directions on **Qwen2.5-7B-Instruct** (`chen2025persona`) — hookability + extraction are demonstrated on the family.
- Code specialist → maximizes render-success and exhibits the "AI slop" default the skill moves (`05_skill_phenomenon`). Weaker general instruction-following than frontier chat models is acceptable: we measure *deltas*.
- **Only caveat:** confirm it *applies* a 5-part skill well enough (a quick pilot: does full-skill visibly change output vs neutral?). If the code model under-responds to multi-part design guidance, Llama-3.1-8B is the recorded fallback (weaker code, gated license, but has Llama-Scope SAEs). See D-a/D-b notes.

## D2 — Hook tooling: HF custom hooks vs TransformerLens/nnsight
**Recommend: CONFIRM HF `transformers` + small custom hook module as primary; TransformerLens/nnsight exploratory only (ADR-002 → accepted).** **Confidence: HIGH.**
- vLLM **cannot** do mid-generation activation injection (hooks disabled at decode; delta-injection explicitly deferred) → steering must be HF (`04_generation_hooks_tooling`). TransformerLens ~doubles load memory (costly for 7B on Colab); nnsight/baukit are fine alternatives for exploratory patching.
- HF hook facts encoded: hook `model.model.layers[i]`, output is a **tuple** (hidden = `[0]`), decode fires per-token (seq_len==1), capture **running means** not full sequences (~0.8 GB/example bf16 otherwise).
- **Use vLLM for Stage-1 bulk generation** (throughput), HF for all activation/steering work; never cross-compare engines (determinism).

## D3 — Activation site (positions + layer range) for LONG code generations
**Recommend:** primary extraction = **mean over response tokens**; layer **scan 0–27, focus band 11–20 (~40–70% depth)**; also compute a **last-prompt-token** variant (for the projection monitor) and **first-k response tokens** variant (early commitment). Select layer/position on a **dev split** by class-separation AUC + dev steering effect. **Confidence: MED-HIGH.**
- Mean-over-response-tokens is what worked for free-form style/persona generation (`konen2024style`, `chen2025persona`) — the right statistic when there's no single "answer token" (unlike CAA's A/B letter position, `rimsky2024caa`).
- Mid-band justified by CAA layer 13/32, persona layers ~12–16, function/task vectors' middle-layer causal locus (`todd2024fv`, `hendel2023task`); scaled to 28 layers → ~11–20.
- Selection discipline from `arditi2024refusal`; class-separation predicts steerability (`tan2024analysing`).
- *Caveat (med):* long generations may carry design signal at different positions than short-behavior tasks — validate empirically (probe accuracy per position; patching localization) rather than assuming.

## D4 — Contrast-pair construction + number of prompts×seeds for a stable mean
**Recommend:** contrast = **full-skill vs length-matched-neutral** (ADR-003, keep); **≥256 effective pairs** (~40–60 prompts × 5 seeds × both cells); confirm stability by plateau of the running-mean cosine similarity. **Confidence: HIGH (design), MED (exact n).**
- Length-matched neutral (not empty) isolates design content — matched-length contrastive prompts are standard (`chen2025persona`); ActAdd shows a prompt-pair difference *is* the vector (`turner2023actadd`).
- Sample-size norms: Arditi uses a few hundred per side; CAA hundreds per behavior; persona vectors similar. Hundreds of pairs is the field norm → our 256+ is defensible; verify empirically (mean stabilizes) rather than fixing blindly.

## D5 — Steering mechanics (layers, α, positions, controls)
**Recommend:** single mid-layer injection first (multi-layer fallback); add at **all generated positions**; **α parameterized both absolute and norm-relative** (fraction of $\lVert h_l\rVert$); sweep symmetric band from $\{-2..+2\}$ outward with a **KL/coherence guardrail**; include **directional-ablation flip test** (necessity) and **norm-matched random-vector control** (specificity). **Confidence: HIGH.**
- All-positions injection + CAA multiplier band (`rimsky2024caa`); non-monotonic strength → guardrail + dev-selected operating point (`taimeskhanov2026strength`); style-vs-content Pareto (`konen2024style`).
- Norm-relative α transfers across layers (persona/style practice). Multi-layer fallback if under-steering (`vanderweij2024broad`).
- **Two causal arms:** addition (sufficiency) + directional ablation / weight orthogonalization while skill present (necessity) — the flip test (`arditi2024refusal`); random norm-matched control guards non-identifiability (arXiv:2602.06801). Optional **CAST-style conditional gating** to fire only on UI prompts (`lee2024cast`).

## D6 — Judge choice + cost for ~2,000–4,000 pairwise judgments
**Recommend: primary = Gemini 2.5 Flash; secondary = GPT-4o or Claude Sonnet-class on a subset (+ human subset).** **Confidence: HIGH.**
- Arithmetic (both orders, ~3.5k in + 0.2k out per call, up to 8,000 calls): **Gemini 2.5 Flash ≈ $10–15** total; **GPT-4o ≈ $85**, **Claude Sonnet-class ≈ $110** for the full both-orders 4k set; ¼ that at the low end (`05_vlm_judge_pricing`). Cost is not a constraint — can run two judges on the full set.
- Flash = cheap + high rate limits + different family from Qwen (avoids self-enhancement, `zheng2023mtbench`). Avoid Qwen2.5-VL as primary (same family). Anchor with an ArtifactsBench-style checklist (`zhang2025artifactsbench`); both orders + tie-if-inconsistent; position-bias strategy from `jeon2025gfocus`.

## D7 — Objective metric suite (which to implement; which correlate with humans)
**Recommend:** the deterministic-core + auxiliary lists in SYNTHESIS §4. **Confidence: HIGH (implementation), MED (which predict appeal).**
- **Deterministic:** render-success, WCAG contrast distribution, axe violations, overflow/overlap, alignment/grid regularity, balance/equilibrium/symmetry (Ngo), white-space/density, typography-scale consistency, Hasler colorfulness, #dominant colors, figure-ground contrast, visual complexity, **purple-slop index** (hue-fraction + gradient-bg + Inter-share + centered-hero; validate vs human "AI-generated" ratings).
- **Literature says these actually track appeal:** colorfulness (moderate optimum) and visual complexity (inverted-U) (`reinecke2013predicting`); Ngo/Miniukovich metrics explain ≤49% variance (`miniukovich2015computation`) — diagnostics, not quality oracles.
- **Auxiliary (learned, secondary):** UIClip quality (`wu2024uiclip`, validate first), CLIP relevance (`wu2024uicoder`). All computed on **rendered DOM/screenshot**, never raw code.

## D8 — Ablation design (fraction, seeds, prompt-set size, power)
**Recommend:** LOO + AOI + **2^(5-1) resolution V (E=ABCD, 16 runs)** + 4 controls; **≥3 seeds/cell, 5 for headline**; **~40–50 prompts** (dev/held-out with unseen task types in held-out); power via paired McNemar. **Confidence: HIGH.**
- Res-V keeps **main effects + all 2FIs clean** (aliased only with 3FI+), the right cost/benefit for 5 components (`montgomery2017doe`; `04_experimental_design_stats`).
- Seeds: generation-quality work reports distributions; ≥3 (5 headline) with MixedLM (random prompt/seed) avoids pseudoreplication.
- **Power sketch:** detecting 60/40 preference split at 80%/α=.05 ≈ **~200 informative pairs**; 65/35 ≈ **~80** — sizes prompts×pairs and the 2–4k judgment budget. Length-match all cells (pad on LOO) + BT length covariate.

## D9 — SAE go/no-go
**Recommend: CONFIRM ADR-008 — SAE route is STRETCH-ONLY (effectively no-go for the primary paper).** **Confidence: HIGH.**
- **No public SAE suite for Qwen2.5-Coder** (Qwen-Scope covers Qwen3/3.5 only, `deng2026qwenscope`; training one is out of Colab scope). Using a different model breaks the same-model rule.
- **DiffMean ≥ SAE** on the largest benchmark (`wu2025axbench`); SAEs are fragile (`ronge2026coffee`) and **don't faithfully decompose steering vectors** (`mayne2024decompose`). Rebuttals (`arad2025saesteering`, Jørgensen 2026) show SAEs *can* work with heavy feature-selection infra we lack.
- If ever pursued: a *transfer* demo on a model that has SAEs (Llama-Scope / Gemma-Scope), clearly labeled off-critical-path.

## D10 — Skill source + license + 5-component decomposition
**Recommend:** **adapt** (not copy) the Anthropic `frontend-design` skill into project-authored `canonical_skill_v0.md` (5 labeled components, ~500 tokens); cite Anthropic provenance. **Confidence: HIGH.**
- Anthropic example skills are **Apache-2.0** but confirm per-folder LICENSE before verbatim reuse; adapting avoids redistribution ambiguity and gives a clean, length-controllable independent variable (`anthropic2025frontendskill`; SOURCES.md).
- 5-component split (grounded in the real text): **C1 color/palette, C2 layout/spacing/hierarchy, C3 typography, C4 component patterns/examples, C5 negative constraints** — sentence-level draft in `skill_exemplars/canonical_skill_v0.md`. Web-artifacts-builder's "very important" negative-constraint line suggests **C5 may dominate** — a headline hypothesis to test.

## D11 — Prompt set (taxonomy, size, split, single-file constraint)
**Recommend:** ~10 task types (landing, dashboard, form, pricing, portfolio, blog, e-commerce/product, auth, settings, admin-table); **~40–50 prompts**; **dev/held-out split where held-out contains ≥2 task TYPES unseen in dev** (for the Stage-2 generalization claim); constant output constraint = *"single self-contained HTML file, all CSS/JS inline, no external network requests."* **Confidence: HIGH.**
- Single-file HTML is an accepted arena format (DesignArena) and enforces hermetic render (ADR-006); `laurencon2024websight`/`si2024design2code` corpora confirm single-file HTML realism.
- Held-out-unseen-type is required because steering generalization must be tested OOD (`tan2024analysing`); held-out within-type only would overstate generalization.

## D12 — Anything 2025–26 that changes the design; and the novelty question
**Recommend:** design holds; incorporate the new controls below. **Novelty claim stands, stated precisely.** **Confidence: HIGH.**
- **Has anyone done steering-vector interpretability on UI/frontend code generation?** After a broad sweep (paper_search + web): **No.** Steering spans text/code-capability/style/persona/multimodal-understanding (`vanderweij2024broad`, `konen2024style`, `chen2025persona`, arXiv:2505.14071), and UI is studied only black-box (benchmarks/judges). **No located work extracts or steers a direction for the visual/aesthetic quality of generated frontend code.** → our differentiated contribution; state as "to our knowledge, first activation-level interpretability of aesthetic UI-code generation."
- **New work to fold in (already in dossier):**
  - Reliability/threats: `tan2024analysing`, `dasilva2025steeringoff`, non-identifiability (2602.06801), `wollschlager2025cones` → mandate distributions, random-vector + ablation controls, OOD held-out.
  - Strength theory `taimeskhanov2026strength` → guardrailed α sweep (non-monotonic).
  - Judge reliability for UIs `zhang2025artifactsbench` (94.4% vs WebDev Arena), `jeon2025gfocus` → checklist-anchored, position-bias-controlled pairwise.
  - SAE skepticism + Qwen-Scope (`wu2025axbench`, `ronge2026coffee`, `deng2026qwenscope`) → keep SAEs stretch.
  - New UI benchmarks (ArtifactsBench, DesignBench, Vision2Web, UI-Bench, DesignArena) → borrow their oracle patterns, none preempts our ablation/interp.
- **No 2025–26 result overturns the plan;** several *strengthen* it (persona vectors on Qwen2.5, ArtifactsBench judge reliability) and several *sharpen the honesty bar* (steering reliability critiques).
