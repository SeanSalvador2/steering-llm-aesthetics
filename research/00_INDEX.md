# 00_INDEX — Project 19 Research Dossier

Map, reading order, and one-line verdict per source. All notes end with **Borrow/Avoid**. Citations resolve in [`refs.bib`](refs.bib).

## Read in this order
1. [`SYNTHESIS.md`](SYNTHESIS.md) — the decision document: 10 load-bearing findings, assembled Stage-1 & Stage-2 recipes, objective-metric shortlist (formulas), risks→mitigations, honest novelty statement.
2. [`DECISIONS_INPUT.md`](DECISIONS_INPUT.md) — recommendations on D1–D12 with evidence + confidence (confirms ADR-001/002/003/005/006/007/008; sizes prompts/seeds/judge budget).
3. Cluster notes below (DEEP first, then survey).
4. [`skill_exemplars/`](skill_exemplars/) — the independent variable: real skill texts + our canonical adaptation.

## Deliverable map
```
research/
├── 00_INDEX.md              ← you are here
├── SYNTHESIS.md             ← cross-cutting decision document
├── DECISIONS_INPUT.md       ← D1–D12 recommendations
├── refs.bib                 ← 55 verified BibTeX entries
├── notes/
│   ├── stage1_ui/           ← 8 notes (UI gen, aesthetics, the skill)
│   ├── stage2_interp/       ← 12 notes (steering, probing, patching, SAEs)
│   ├── methods_stats/       ← 4 notes (judge, agreement, BT, DOE)
│   └── engineering/         ← 6 notes (Qwen, Llama, Colab, hooks, judge cost, Playwright)
└── skill_exemplars/         ← 4 files + SOURCES.md
```

---

## Cluster B — Stage 2: interpretability & steering ([notes/stage2_interp](notes/stage2_interp))
- [01_arditi_refusal_direction](notes/stage2_interp/01_arditi_refusal_direction.md) — **B1 DEEP.** THE template: diff-in-means, layer/position selection, addition + directional-ablation, coherence checks. *Our Stage-2 skeleton.*
- [02_caa_actadd](notes/stage2_interp/02_caa_actadd.md) — **B2 DEEP.** CAA (layer 13/32, multipliers −2..+2, all post-prompt positions) + ActAdd. *Our injection mechanics.*
- [03_style_vectors](notes/stage2_interp/03_style_vectors.md) — **B3 DEEP.** Closest setting: activation-based style vectors, mean-over-tokens, λ sweep, style-vs-content Pareto. *Our nearest neighbor; de-risks free-form extraction.*
- [04_tan_reliability](notes/stage2_interp/04_tan_reliability.md) — **B4 DEEP.** Steerability variance, ~50% anti-steerable, OOD brittleness. *Why we report distributions + failure surface.*
- [05_axbench](notes/stage2_interp/05_axbench.md) — **B5 DEEP.** DiffMean > SAEs; prompting > all for steering; harmonic-mean multi-axis metric. *Gates ADR-008.*
- [06_activation_patching](notes/stage2_interp/06_activation_patching.md) — **B6 DEEP.** Denoising vs noising, logit-diff metric, self-repair/illusion pitfalls. *Our localization arm.*
- [07_probing](notes/stage2_interp/07_probing.md) — **B7 DEEP.** Linear probes + control-task selectivity (linear>MLP). *Localization + honesty guardrail.*
- [08_repe](notes/stage2_interp/08_repe.md) — **B8 DEEP.** LAT reading vectors, projection-monitoring, representation control. *Cross-check + monitor idea.*
- [09_persona_vectors](notes/stage2_interp/09_persona_vectors.md) — **B9 DEEP.** Automated diff-in-means on **Qwen2.5-7B**, mid layers, projection predicts behavior r≈0.75–0.83. *Strongest de-risk; same family.*
- [10_foundations_survey](notes/stage2_interp/10_foundations_survey.md) — LRH, superposition, function/task vectors, geometry. *Why linear diff-in-means is principled; multi-direction caveat.*
- [11_sae_line_survey](notes/stage2_interp/11_sae_line_survey.md) — Bricken/Templeton, Gemma/Llama/Qwen Scope, SAE skepticism + rebuttals. *No Qwen2.5-Coder SAEs → stretch only.*
- [12_steering_variants_survey](notes/stage2_interp/12_steering_variants_survey.md) — CAST, strength theory, broad-skill/code steering, non-identifiability, concept cones. *Controls + novelty check.*

## Cluster A — Stage 1: UI generation, design skills, aesthetics ([notes/stage1_ui](notes/stage1_ui))
- [01_design2code](notes/stage1_ui/01_design2code.md) — **A1 DEEP.** 484 pages; block-match/text(Dice)/position/color(CIEDE2000)/CLIP metrics; hermetic render. *Objective-metric machinery (reference-free adaptation).*
- [02_uicoder](notes/stage1_ui/02_uicoder.md) — **A2 DEEP.** Compiler + multimodal-relevance automated feedback. *Render-success as a gating metric.*
- [03_computational_aesthetics](notes/stage1_ui/03_computational_aesthetics.md) — **A3 DEEP.** Ngo (balance/equilibrium/symmetry formulas), Miniukovich (8 metrics, ≤49% var), Reinecke (colorfulness/complexity, ~½ var), Hasler colorfulness. *Formulas we implement + the ½-variance ceiling.*
- [04_uiclip](notes/stage1_ui/04_uiclip.md) — **A4 DEEP.** Learned UI design-quality scorer; best vs 12 designers. *Auxiliary (learned) metric; validate first.*
- [05_skill_phenomenon](notes/stage1_ui/05_skill_phenomenon.md) — **A5 DEEP.** The frontend-design skill, "purple slop" default, **5-component decomposition**. *The independent variable + ablation factors (D10).*
- [06_ui_benchmarks_survey](notes/stage1_ui/06_ui_benchmarks_survey.md) — WebSight, Web2Code, ArtifactsBench (94.4% vs WebDev Arena), DesignBench, Vision2Web, UI-Bench, DesignArena. *Oracle patterns; our ablation/interp gap.*
- [07_accessibility_contrast_survey](notes/stage1_ui/07_accessibility_contrast_survey.md) — axe-core (~57% coverage), WCAG contrast formula, APCA, DOM metrics. *Deterministic oracle backbone.*
- [08_prompt_ablation_methodology](notes/stage1_ui/08_prompt_ablation_methodology.md) — with/without-instruction contrasts, confound regression, control conditions, DOE. *Stage-1 methodology precedents.*

## Cluster C — Evaluation & statistics ([notes/methods_stats](notes/methods_stats))
- [01_llm_vlm_judge](notes/methods_stats/01_llm_vlm_judge.md) — **C1 DEEP.** Zheng biases (position/verbosity/self-enhancement), >80% agreement, pairwise>absolute; UI VLM judging ~90%. *Preference-half protocol.*
- [02_agreement_krippendorff_gwet](notes/methods_stats/02_agreement_krippendorff_gwet.md) — **C2 DEEP.** α formula + kappa paradox; Gwet AC1 fix; thresholds. *Reliability gate on skewed preferences.*
- [03_bradley_terry](notes/methods_stats/03_bradley_terry.md) — **C3 DEEP.** BT MLE, ties, + Arena style-control regression. *Cell utilities + confound removal.*
- [04_experimental_design_stats_survey](notes/methods_stats/04_experimental_design_stats_survey.md) — MixedLM, cluster bootstrap, Holm/BH, paired power, 2^(5-1) res-V, preregistration. *The inference stack.*

## Cluster D — Engineering feasibility ([notes/engineering](notes/engineering))
- [01_qwen_model_facts](notes/engineering/01_qwen_model_facts.md) — **D-a.** Apache-2.0; 3584/28/28/4-KV; bf16 ~15 GB; ChatML. *Confirms D1.*
- [02_llama_fallback](notes/engineering/02_llama_fallback.md) — **D-b.** Llama-3.1-8B: gated license, 4096/32/32/8-KV, has Llama-Scope SAEs, weaker code. *Fallback profile.*
- [03_colab_feasibility](notes/engineering/03_colab_feasibility.md) — **D-c.** T4/L4/A100 VRAM, compute units, 12–24h sessions, ~90-min idle, Drive persistence. *L4+A100 feasible.*
- [04_generation_hooks_tooling](notes/engineering/04_generation_hooks_tooling.md) — **D-d/e.** vLLM (bulk gen) vs HF (steering; vLLM can't inject mid-decode); Qwen2 hook mechanics; TL/nnsight. *Confirms ADR-002.*
- [05_vlm_judge_pricing](notes/engineering/05_vlm_judge_pricing.md) — **D-f.** July-2026 pricing; ~$10–15 (Gemini Flash) to ~$110 (GPT-4o/Claude) for 4k both-orders. *Confirms D6.*
- [06_playwright_determinism](notes/engineering/06_playwright_determinism.md) — **D-g.** Fixed viewport, animations off, fonts-ready, network blocked, pinned Chromium. *Deterministic render for the oracle.*

## Skill exemplars ([skill_exemplars](skill_exemplars))
- [SOURCES.md](skill_exemplars/SOURCES.md) — provenance/license table (Anthropic skills = Apache-2.0 example skills; adapt-don't-copy stance).
- [01_anthropic_frontend_design](skill_exemplars/01_anthropic_frontend_design.md) — faithful structured capture + 5-component mapping.
- [02_anthropic_web_artifacts_builder](skill_exemplars/02_anthropic_web_artifacts_builder.md) — the "AI slop" negative-constraint line (near-verbatim).
- [canonical_skill_v0](skill_exemplars/canonical_skill_v0.md) — **project-authored ~500-token skill, C1–C5 labeled** + control-cell texts. *What we actually run.*

---

## Source count
- **~55 verified sources** in `refs.bib` (arXiv ID / DOI / fetched-or-searched URL for each). **0 unverified entries in refs.bib.**
- **15 DEEP notes** (B1–B9, A1–A5, C1–C3) + 7 survey/cluster notes + 6 engineering notes.
- Items intentionally cited from web/proceedings (no arXiv): Ngo 2003 (Information Sciences DOI), Miniukovich 2015 (CHI DOI), Reinecke 2013 (CHI DOI), Hasler 2003 (SPIE/EPFL), Hewitt-Liang 2019 (ACL), Bradley-Terry 1952 (Biometrika DOI), Gwet 2008 / Hayes-Krippendorff 2007 (journal DOIs), Holm 1979 / Benjamini-Hochberg 1995, Templeton/Bricken (transformer-circuits.pub), Anthropic skills (GitHub), LMSYS style-control (blog), axe-core (GitHub), WCAG (W3C), WebDev Arena (blog).

## Known coverage gaps (deliberate)
- **arxiv.org / ar5iv / semanticscholar are egress-blocked (403) in this environment** → paper *full texts* were reconstructed from HF `paper_search` abstracts, HF paper pages, targeted web-search snippets (which returned specific numbers), and author blogs/GitHub. Exact per-paper minutiae (e.g. Style-Vectors' precise λ grid) should be re-verified against PDFs during PLAN.md build; the layer/α/position figures cited here are corroborated across ≥2 sources where load-bearing.
- Full verbatim of the Anthropic frontend-design SKILL.md not captured (fetcher quote-limit + MCP repo-scoping); a faithful structured capture is provided and we adapt rather than copy (license-safe).
