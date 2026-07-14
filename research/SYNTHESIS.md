# SYNTHESIS — Project 19 Research Dossier

A decision document, not a summary. Sections: (1) load-bearing findings; (2) assembled Stage-2 recipe; (3) assembled Stage-1 recipe; (4) objective-metric shortlist with formulas; (5) risks→mitigations; (6) honest novelty statement. Citations are BibTeX keys in `refs.bib`.

---

## 1. The 10 most load-bearing findings (with implications)

1. **Diff-in-means is the strongest simple, interpretable steering/detection method** — it beats SAEs on the largest benchmark (`wu2025axbench`) and is the template that transfers across settings (`arditi2024refusal`, `rimsky2024caa`). → *Make diff-in-means the primary Stage-2 method; demote SAEs to stretch (confirms ADR-008).*

2. **The exact extraction pipeline already works on our model family.** Persona Vectors (`chen2025persona`) extract trait directions by diff-in-means over *response* activations at *middle layers* on **Qwen2.5-7B-Instruct**, and a projection at the final prompt token predicts behavior at **r≈0.75–0.83**. → *Stage-2 feasibility is de-risked; adopt mid-layer, response-token diff-in-means; add projection-as-quality-monitor as an auxiliary result.*

3. **Steering effects are heterogeneous and can be anti-directional.** Up to ~50% of inputs can be *anti-steerable* for some concepts (`tan2024analysing`); reliability varies in- and out-of-distribution (`dasilva2025steeringoff`). → *Report per-prompt distributions and the anti-steerable fraction, not means; hold out unseen task types for the generalization claim.*

4. **Two causal arms are needed, not one.** Necessity (directional ablation / weight orthogonalization) and sufficiency (activation addition) can disagree; a single direction may not be unique (`arditi2024refusal`, `wollschlager2025cones`; non-identifiability arXiv:2602.06801). → *Run addition + directional-ablation flip test + a norm-matched random-vector control; frame the result as "a causally sufficient/necessary direction," not "the unique design direction."*

5. **Objective aesthetic metrics explain at most ~half the variance in human appeal** (`miniukovich2015computation` ≤49%; `reinecke2013predicting` ~50%). → *The objective half is necessary but insufficient; the paired VLM-preference signal is mandatory — exactly the brief's two-signal oracle.*

6. **Rubric/checklist-anchored (V)LM judges reach ~90%+ human agreement on UIs** (`zhang2025artifactsbench` 94.4% vs WebDev Arena; UI pairwise with position-bias control in `jeon2025gfocus`). → *Use pairwise, both-orders, checklist-anchored judging; validate against a human subset; judge from a different family than Qwen.*

7. **Judges (and preferences) are biased by length/verbosity/style; this is removable.** Position/verbosity/self-enhancement biases (`zheng2023mtbench`); Chatbot Arena removes style confounds by **regressing length/markdown into the Bradley-Terry model** (`chiang2024stylecontrol`). → *Defense in depth: length-matched neutral control at the design level (ADR-003) **and** style-controlled BT at the analysis level (`bradley1952rank`).*

8. **Skewed preferences break Krippendorff's α (kappa paradox); Gwet's AC1 fixes it** (`hayes2007alpha`, `gwet2008ac1`). → *Because the skill will usually win, report α **and** AC1 with bootstrap CIs; the reliability gate must not false-fail on skew.*

9. **The skill's payload is multi-component and its negative-constraint core is emphasized as "very important"** (`anthropic2025frontendskill`; web-artifacts-builder). The community mechanism ("sampling the high-probability center of web training data") frames the effect as a **steerable distributional shift**. → *Ablate 5 components (color/layout/type/patterns/negatives); expect negative constraints to punch above their token weight; the distributional-shift framing motivates Stage-2 steering.*

10. **No public SAE suite exists for Qwen2.5-Coder, and SAE steering is fragile and doesn't even faithfully decompose steering vectors** (`deng2026qwenscope` covers Qwen3/3.5 only; `mayne2024decompose`; `ronge2026coffee`). → *SAE route is off the critical path; if ever pursued it breaks the same-model rule. Confirms ADR-008.*

---

## 2. Assembled Stage-2 recipe (literature best-practice composite)

**Contrast set (ADR-003).** Pairs = *(full-skill generation, length-matched-neutral generation)* on the same prompt+seed. Matched length/imperativeness isolates design content (`chen2025persona` uses matched contrastive system prompts; ActAdd shows a prompt-pair difference *is* a steering vector, `turner2023actadd`). Number of pairs: literature uses **hundreds** (Arditi few-hundred; CAA hundreds/behavior). Target **≥ ~256 effective pairs** = e.g. 40–60 prompts × 5 seeds × both cells; verify the mean direction has stabilized (cosine-similarity of the running mean across increasing n plateaus).

**Extraction (D3).** For each layer $l\in\{$scan 0–27, focus 11–20$\}$ compute the **mean over response tokens** of the residual stream (per `chen2025persona`/`konen2024style`, the right statistic for free-form generation), then diff-in-means:
$$v_l = \overline{h_l}^{\,(\text{skill})} - \overline{h_l}^{\,(\text{neutral})}, \qquad \hat v_l = v_l/\lVert v_l\rVert.$$
Also compute a **last-prompt-token** variant (for the projection-monitor) and a **first-k response tokens** variant (early commitment). Select the layer/position on a **dev split** by (a) probe/class separation (AUC of projection separating skill vs neutral — `tan2024analysing` says separation predicts steerability) and (b) downstream steering effect on dev prompts (`arditi2024refusal` selection discipline).

**Localization cross-checks.** Linear probes per layer with a **control-task selectivity** report (`hewitt2019control`, `alain2017probes`); **denoising activation patching** (neutral→skill) with a **logit-difference** metric on a design-discriminating token proxy (`zhang2024patching`, `heimersheim2024patching`); confirm the probe/patch-localized layer agrees with the diff-in-means steering layer. Cross-check the direction against **LAT/PCA-on-differences** (`zou2023repe`) — high cosine similarity expected.

**Steering (D5).** Add at all generated positions (`rimsky2024caa`):
$$h_l \leftarrow h_l + \alpha\,\hat v_l.$$
Parameterize $\alpha$ **both** absolutely and **relative to per-layer residual norm** $\lVert h_l\rVert$; sweep a symmetric band (start $\{-2,\dots,+2\}$ like CAA, extend until coherence breaks), expecting **non-monotonic** behavior (`taimeskhanov2026strength`) → pick the operating point on the dev set with a **KL/coherence guardrail** (cap steering where next-token KL from unsteered, or render-success, degrades). Try **single mid-layer** first; **multi-layer injection** as fallback if under-steering (`vanderweij2024broad`).

**Causal verification (the hard bar).** With **no design prompt**, steering must raise held-out quality on **both** oracle signals. Two required controls:
- **Directional-ablation flip test (necessity):** with the skill *present*, project $\hat v_l$ out of the stream at every layer/position (`arditi2024refusal` weight orthogonalization); the skill's quality gain should *disappear*.
- **Norm-matched random vector (specificity):** a random direction of equal norm must *not* reproduce the gain (guards against non-identifiability arXiv:2602.06801).
- **Held-out = unseen task types** (`tan2024analysing` OOD) for the generalization claim.

**Reporting.** Per-prompt delta distributions + anti-steerable fraction; the $\alpha$-vs-quality-vs-coherence Pareto (style-vs-content, `konen2024style`); the failure surface (which task types steer, which break). Optional: multiple sub-direction test (color/layout/type directions) mirroring Stage-1 components (`park2024geometry` orthogonality prediction).

---

## 3. Assembled Stage-1 recipe (ablation)

**Cells.** 5 components {C1 color, C2 layout, C3 type, C4 patterns, C5 negatives} → **LOO** (full − Cᵢ, necessity) + **AOI** (∅ + Cᵢ, sufficiency) + a **2^(5-1) resolution-V** block (E=ABCD, 16 runs, main effects + all 2FIs clean; `montgomery2017doe`) for interactions. Plus **4 controls** (full-skill, length-matched-neutral, "make it beautiful" one-liner, no-system-prompt) — ADR-003. Length-match every cell (pad removed components with neutral filler) so prompt mass is constant.

**Prompts & seeds.** Task taxonomy of ~10 types (landing/dashboard/form/pricing/portfolio/blog/e-commerce/auth/settings/admin-table); **~40–50 prompts** total, **dev/held-out split with unseen task TYPES in held-out** (for Stage-2 generalization). **≥3 seeds/cell (headline cells 5)**; single-file hermetic HTML (ADR-006). Generate on **vLLM** (throughput), fixed sampling config/seed recorded.

**Oracle (two signals).**
- *Objective:* render on Playwright (fixed viewport, animations disabled, network blocked, fonts-ready — `playwright2024screenshots`); compute the metric vector (§4) on the **rendered DOM + screenshot**, never raw code (`si2024design2code` machinery, reference-free adaptation). Render-success is a hard gate (`wu2024uicoder`).
- *Preference:* pairwise screenshots, **both orders**, checklist-anchored VLM judge (Gemini 2.5 Flash primary, GPT-4o/Claude secondary on a subset), tie-if-inconsistent (`zheng2023mtbench`, `zhang2025artifactsbench`, `jeon2025gfocus`). Validate vs a **human-labeled subset**; gate on **Krippendorff α ≥ 0.667 OR Gwet AC1 ≥ 0.80 under demonstrable skew** (`hayes2007alpha`, `gwet2008ac1`).

**Statistics.** Objective metrics → **MixedLM** (random prompt & seed, fixed cell) (`04_experimental_design_stats`). Preferences → **style-controlled Bradley-Terry** (covariates: DOM size, element count, colorfulness, text density) → cell utilities with **cluster-bootstrap CIs over prompts** (`bradley1952rank`, `chiang2024stylecontrol`). Multiplicity: **Holm** for confirmatory component effects, **BH** for exploratory scans. **Power:** paired McNemar sizing (≈200 pairs for 60/40, ≈80 for 65/35). **Preregister** the cell table, gates, and the **null rule** ("effect = null unless it moves an objective metric OR a reliability+power-gated preference delta") before any GPU run.

---

## 4. Objective-metric shortlist (formulas; feeds D7)

Report as a **vector** (don't aggregate raw), split deterministic-core vs auxiliary.

**Deterministic core (unfoolable):**
- **Render success / hermeticity** — binary: renders with network disabled, no external fetch (ADR-006).
- **WCAG contrast** — per text node $CR=\frac{L_1+0.05}{L_2+0.05}$, $L=0.2126R+0.7152G+0.0722B$ (sRGB-linearized); report fraction < 4.5:1, min, median.
- **axe-core violations** — counts by impact (catches ~57% of WCAG issues, reliable lower bound; `deque2024axecore`).
- **Overflow/overlap counts** — elements exceeding viewport / intersecting bounding boxes.
- **Alignment/grid regularity** — # distinct x/y edge positions; gap entropy (Ngo regularity, `ngo2003modelling`).
- **Balance** $BM=1-\frac{|BM_v|+|BM_h|}{2}$; **Equilibrium** $EM=1-\frac{|EM_x|+|EM_y|}{2}$ (center-of-mass offset); **symmetry** (`ngo2003modelling`).
- **White-space ratio** & **density** (`miniukovich2015computation`).
- **Typography-scale consistency** — # distinct font-sizes/families; adherence to a modular ratio.
- **Colorfulness** (Hasler, `hasler2003colorfulness`): $M=\sqrt{\sigma_{rg}^2+\sigma_{yb}^2}+0.3\sqrt{\mu_{rg}^2+\mu_{yb}^2}$, $rg=R-G$, $yb=\tfrac12(R+G)-B$.
- **# dominant colors**, **figure-ground contrast**, **visual complexity** (edge/quadtree density) (`miniukovich2015computation`, `reinecke2013predicting`).
- **Purple-slop index (principled composite):** weighted mix of (i) salient-pixel hue fraction in ~[260°,290°]; (ii) linear-gradient-background prevalence on large/hero elements; (iii) Inter/Roboto/system-ui text share; (iv) centered-hero flag. Report components + composite; **validate it correlates with human "looks AI-generated" ratings** before use.

**Which actually correlate with human appeal (literature):** colorfulness (moderate optimum) and visual complexity (inverted-U) are the empirically validated appeal predictors (`reinecke2013predicting`); balance/symmetry/contrast/white-space have measured but partial power (≤49% variance, `miniukovich2015computation`). → treat all as *diagnostics*; aesthetic *quality* claims ride on the preference signal.

**Auxiliary (learned, secondary):** UIClip quality score (`wu2024uiclip`) — validate correlation with the human subset first; CLIP prompt↔screenshot relevance (on-task check, `wu2024uicoder`); within-prompt cross-cell CLIP/CIEDE2000/Sørensen-Dice drift (`si2024design2code`).

---

## 5. Top risks the literature warns about → our mitigations

| Risk (source) | Mitigation |
|---|---|
| Steering unreliable / anti-steerable (`tan2024analysing`, `dasilva2025steeringoff`) | Report per-prompt distributions + anti-steerable fraction; pre-screen by class separation; OOD held-out task types |
| "Design direction" not unique / non-identifiable (`wollschlager2025cones`, arXiv:2602.06801) | Norm-matched random-vector control; directional-ablation necessity test; claim "a sufficient/necessary direction," test multi-direction |
| Design may be non-linear/distributed (`engels2024notlinear`) | If single direction under-steers, test 2–4D subspace; report the distributed null honestly (brief allows) |
| Objective metrics ≠ aesthetics (≤½ variance) (`miniukovich2015computation`, `reinecke2013predicting`) | Mandatory paired VLM-preference signal; metrics are diagnostics only |
| Judge biases: position/verbosity/self-enhancement (`zheng2023mtbench`) | Both orders + tie-if-inconsistent; length-matched control + style-controlled BT; judge ≠ Qwen family; checklist anchoring |
| Kappa paradox on skewed preferences (`gwet2008ac1`) | Report α **and** AC1 + bootstrap CIs; gate accepts AC1 under demonstrable skew |
| Prompt-mass confound (adding a component adds tokens) | Length-match all cells (pad on LOO) + BT length covariate |
| Steering strength non-monotonic / breaks fluency (`taimeskhanov2026strength`, `konen2024style`) | α sweep with KL/coherence guardrail; report style-vs-content Pareto; pick operating point on dev |
| Pseudoreplication (many seeds per prompt) | MixedLM random effects; cluster bootstrap over prompts; ≥3 seeds |
| SAE fragility / none for our model (`ronge2026coffee`, `deng2026qwenscope`, `mayne2024decompose`) | SAE off critical path (ADR-008); diff-in-means primary |
| Engine nondeterminism (vLLM vs HF) | Within-engine comparisons only; vLLM=Stage-1, HF=Stage-2; record engine/version/seed |
| Render nondeterminism | Fixed viewport, animations off, fonts-ready, network blocked, pinned Chromium (`playwright2024screenshots`) |
| Garden-of-forking-paths over many metrics/cells | Preregister hypotheses, cells, gates, null rule, Holm/BH split |

---

## 6. Honest novelty statement

**What is genuinely new:**
1. **First activation-level / steering-vector interpretability of UI-and-aesthetic code generation.** Activation steering has been applied to text, code *capability* (`vanderweij2024broad`), style/persona (`konen2024style`, `chen2025persona`), and multimodal understanding (arXiv:2505.14071) — but an exhaustive sweep found **no work extracting or steering a direction for the *visual/aesthetic quality* of generated frontend code.** This is the differentiated contribution and must be stated precisely as such (see DECISIONS_INPUT D12).
2. **First causal component-ablation of a "design skill."** Every UI benchmark (`si2024design2code`, `zhang2025artifactsbench`, `xiao2025designbench`, UI-Bench, DesignArena) scores *models/tools*; none decomposes the *guidance* and attributes quality to components with a rigorous two-signal oracle + factorial design.
3. **The Stage-1↔Stage-2 correspondence:** testing whether the components the ablation finds most causal map onto the activation structure (do "color/layout/type" ablation weights correspond to separable steering sub-directions?) — a novel bridge between prompt-level and representation-level explanations, predicted plausible by the linear-representation orthogonality result (`park2024geometry`).

**What is *not* new (and must be credited):** diff-in-means extraction (`arditi2024refusal`, `rimsky2024caa`), style/persona steering (`konen2024style`, `chen2025persona`), the two-signal UI oracle (metrics + judge exists piecewise across `si2024design2code`, `zhang2025artifactsbench`), and the objective aesthetic metrics (`ngo2003modelling`, `miniukovich2015computation`, `reinecke2013predicting`). Our contribution is the **synthesis pointed at a new target** (design skill → UI code → activations) with the causal rigor (both-arms steering, honest failure surface) the brief demands. The **honest-null option** (design is distributed/not linearly steerable) is itself a legitimate, publishable outcome.
