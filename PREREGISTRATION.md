# PREREGISTRATION.md — Project 19 (Anatomy of a Design Skill)

**This document freezes every confirmatory decision before any GPU run.** It is extracted from
`PLAN.md` (authoritative detail) and must be **git-tagged `prereg-v1`** before the first Colab GPU
session (the pilot, P0). Anything not fixed here as confirmatory is exploratory and BH-controlled.
Subject model **locked**: `Qwen/Qwen2.5-Coder-7B-Instruct`, both stages (ADR-001). No GPU/model
inference has been executed at freeze time (CLAUDE.md compute policy).

**Status:** DRAFT-FROZEN candidate. Tag after (a) the CPU `src/` stack passes all tests, (b) power
simulations on synthetic data confirm the judgment budget, (c) the split and skill text are final.

---

## 1. Hypotheses (confirmatory unless marked exploratory/stretch)

- **H-skill.** FULL ≻ NEUTRAL on both oracle signals (skill works; it is design *content*, not prompt
  mass, because NEUTRAL is length-matched).
- **H1ᵢ (RQ1 necessity, i∈1..5).** μ(FULL) − μ(LOO-Cᵢ) > 0. Directional prior: C5 (negatives) and C1
  (color) largest.
- **H2ᵢ (RQ2 sufficiency).** μ(AOI-Cᵢ) − μ(NEUTRAL) > 0 and μ(AOI-Cᵢ) < μ(FULL); sufficiency is
  distributed (no single component reaches within 30 % of the FULL−NEUTRAL POC gap).
- **H3 (RQ3 interactions, exploratory).** ≥1 two-factor interaction is non-zero.
- **H4 (RQ4 nudge).** μ(FULL) > μ(BEAUTY1) > μ(NEUTRAL).
- **H5 (RQ5 locate).** The FULL-vs-NEUTRAL signal peaks (probe + patching) in a contiguous mid-band
  (layers ≈ 11–20 of 28).
- **H6 (RQ6 causal steer — the bar).** Steering the diff-in-means direction with **no design prompt**
  raises held-out quality on both signals.
- **H7 (RQ7 failure surface).** Steering generalizes to unseen task types with anti-steerable
  fraction < 50 % and a non-monotone dose-response.
- **H8 (RQ8 correspondence, stretch).** Component sub-vectors are near-orthogonal and each steers its
  own metric family.

Every hypothesis has a preregistered **honest-null branch** (PLAN Part I); a clean null is a reported
result, never forced (BRIEF, CLAUDE.md).

---

## 2. Independent variable (frozen skill v1, ADR-009)

`research/skill_exemplars/canonical_skill_v1.md` is the frozen text: **C1–C4 prescriptive only, C5
holds ALL negatives**, five components token-balanced within ±15 % of the ~85-token mean (build-time
assertion). Neutral filler pool (Filler-1…5) is token-matched to C1…C5 and **render-inert** by rule:
fillers mandate only source-level conventions (formatting, comments, naming, CSS declaration
ordering, JS source organization) and may not mandate anything that changes the rendered DOM tree,
element/attribute choices, or render outcome — no semantic-element, lang/title/meta, ARIA,
validation/tag-closure, or event-attachment content (else fillers would move metric families V/A and
bias component effects downward). A build-time **filler audit** against a banned-topic term list
(PLAN §II.1.3) enforces this, parallel to the whole-word prompt leakage audit. **NEUTRAL = all five
fillers** = the (−,−,−,−,−) corner. Constant output constraint (hermetic single-file HTML) sits in
the **user** turn, never ablated. Controls: FULL, NEUTRAL, BEAUTY1 ("Make it beautiful and
well-designed."), NOSYS (no system message). LOO padding: removed Cᵢ → Filler-i in the same slot, so
all 16 factorial runs + 5 LOO carry constant ≈425-token prompt mass.

---

## 3. The exact cell table (24 distinct cells; frozen sign vectors)

Factor map A..E = C1..C5. `+` = real component; `−` = matched filler. Res-V 2⁵⁻¹, generator **E=ABCD**,
`I=ABCDE`. Seeds: headline = 5 {0..4}; interaction = 3 {0..2}.

| cell_id | C1 | C2 | C3 | C4 | C5 | tier | seeds |
|---|:--:|:--:|:--:|:--:|:--:|---|:--:|
| FULL | + | + | + | + | + | control | 5 |
| NEUTRAL | − | − | − | − | − | control | 5 |
| BEAUTY1 | · | · | · | · | · | control | 5 |
| NOSYS | · | · | · | · | · | control | 5 |
| LOO-C1 | − | + | + | + | + | LOO | 5 |
| LOO-C2 | + | − | + | + | + | LOO | 5 |
| LOO-C3 | + | + | − | + | + | LOO | 5 |
| LOO-C4 | + | + | + | − | + | LOO | 5 |
| LOO-C5 | + | + | + | + | − | LOO | 5 |
| AOI-C1 | + | − | − | − | − | AOI | 5 |
| AOI-C2 | − | + | − | − | − | AOI | 5 |
| AOI-C3 | − | − | + | − | − | AOI | 5 |
| AOI-C4 | − | − | − | + | − | AOI | 5 |
| AOI-C5 | − | − | − | − | + | AOI | 5 |
| F-123 | + | + | + | − | − | interaction | 3 |
| F-124 | + | + | − | + | − | interaction | 3 |
| F-125 | + | + | − | − | + | interaction | 3 |
| F-134 | + | − | + | + | − | interaction | 3 |
| F-135 | + | − | + | − | + | interaction | 3 |
| F-145 | + | − | − | + | + | interaction | 3 |
| F-234 | − | + | + | + | − | interaction | 3 |
| F-235 | − | + | + | − | + | interaction | 3 |
| F-245 | − | + | − | + | + | interaction | 3 |
| F-345 | − | − | + | + | + | interaction | 3 |

**16-run factorial** (main effects + all 2FIs clean; 2FI aliased only with 3FI): {FULL, AOI-C1..C5,
F-123..F-345}. **Generation counts (frozen):** dev 40 prompts × all 24 cells = **4,000**; held-out 18
prompts × {4 controls@5 + 5 LOO@3} = **630**; **Stage-1 total 4,630**.

**Prompt split (frozen by id).** Dev (40): L01–L05,D01–D05,F01–F05,P01–P05,PF01–PF05,B01–B05,E01–E05,
A01–A05. Held-out seen-type (8): L06,D06,F06,P06,PF06,B06,E06,A06. Held-out **unseen-type (10):**
ST01–ST05, AT01–AT05 (settings-panel, admin-data-table — absent from dev; the OOD generalization
test). Full text: PLAN §II.2.1. Leakage audit (case-insensitive **whole-word** `banned_words` match
over the briefs only — style adjectives/directives + the design-word family; PLAN §II.2) must pass
before freeze.

---

## 4. Endpoints, decision rules, multiplicity (per RQ)

**Two-signal oracle.** Objective = **POC** (PLAN Appendix B.8) + family-wise decision. The POC
endpoint carries two **pre-specified conditionals frozen with it** (PLAN §III.4; firing either is
*not* an amendment): (i) if PSI fails the §9 admission gate, the confirmatory POC is the same
composite **without the −PSI term** (a 6-term POC), used for every confirmatory decision; (ii) if
fewer than 30 human-preferred pages are available for calibration, the colorfulness anchor `c*`
defaults to the pre-stated value = **median Hasler-M of the dev FULL-cell generations**. Preference =
**style-controlled Bradley-Terry utility** (Davidson ties; covariates: log DOM size, log token
length, element count, colorfulness, text density; reference NEUTRAL; cluster-bootstrap over prompts,
B=2000). An effect is **non-null** iff it moves the objective signal (POC Holm-significant, OR ≥2 of
6 families concordant under BH) **OR** a preference delta passing both the reliability gate (§5) and
the power gate (§6).

| RQ | primary endpoints | decision rule | multiplicity | outcomes |
|---|---|---|---|---|
| H-skill | POC + BT (FULL vs NEUTRAL) | non-null per oracle; report δ, %-gap | in confirmatory family | works / null |
| RQ1 | POC + BT (FULL vs LOO-Cᵢ) | Cᵢ necessary if δ>0 & Holm-sig (POC) OR gated BT CI>0; rank by δ | **Holm** FWER .05 over the 12-test family | necessary(ranked)/null/negative |
| RQ2 | POC + BT (AOI-Cᵢ vs NEUTRAL) | sufficient-partial if δ>0 & Holm-sig/gated; distributed if none ≥30 % gap | **Holm** (same family) | one-carries/distributed/null |
| RQ3 | 2FI coefs (factorial MixedLM on POC) | pair interacts if BH-sig & concordant on ≥1 other family | **BH** FDR .10 | additive/interacting(pairs) |
| RQ4 | ordered FULL>BEAUTY1>NEUTRAL | content matters if FULL−BEAUTY1>0 gated; nudge-suffices if BEAUTY1≥70 % gap & FULL−BEAUTY1 null | in confirmatory family | content/nudge/neither |
| RQ5 | probe AUC+selectivity, patch %-recovered | band = contiguous layers AUC≥.80 & selectivity≥.15 & patch≥25 % | descriptive | localized/diffuse |
| RQ6 | S2.4 arms, both signals | **success criterion §7** | Holm over 6 families | sufficient(&/or necessary)/null |
| RQ7 | per-type deltas, anti-steerable frac | generalizes if unseen-type delta>0 gated & anti-steer<50 % | BH | robust/partial/brittle |
| RQ8 | cosine matrix + signature match | found if mean|cos|<.3 & ≥3/5 signatures match | descriptive/BH | found/partial/absent |

**Confirmatory family (Holm, FWER .05), applied separately to POC and to BT:** {FULL−NEUTRAL;
5×(FULL−LOO-Cᵢ); 5×(AOI-Cᵢ−NEUTRAL); FULL−BEAUTY1} = 12 tests. **Everything else is exploratory (BH,
FDR .10).** No post-hoc metric selection; the POC formula and the 6 families are fixed here.

---

## 5. Reliability gate (judge validity)

Sean labels **N=100** pairs (stratified: 30 FULL–NEUTRAL, 35 FULL–LOO, 20 AOI–NEUTRAL, 15 Stage-2
steered–unsteered), both orders. Compute judge-vs-human **Krippendorff α (ordinal)** and **Gwet AC1**
with bootstrap 95 % CIs, and report marginal skew. **Gate:** trust the preference signal iff
**α ≥ 0.667 OR (AC1 ≥ 0.80 with α depressed by demonstrable marginal skew).** Fail → cascade: revise
rubric → swap judge (GPT-4o/Claude) → escalate humans to N=300 & down-weight judge → objective-only
null decisions. Primary judge Gemini 2.5 Flash; GPT-4o audit on 15 %. Both orders; order-inconsistent
→ tie.

---

## 6. Power gate

Paired McNemar sizing (PLAN §III.7): 60/40 needs ~200 informative pairs; 65/35 ~80; 55/45 ~780 (α=.05,
power=.80). Frozen allocation: FULL–NEUTRAL 200 pairs (5 seed-pairs×40); each FULL–LOO-Cᵢ 120
(3×40); each AOI-Cᵢ–NEUTRAL 80 (2×40); others 80–120. **Gate:** a preference delta counts only if its
contrast achieved ≥ the required n recomputed at the *observed* δ; otherwise it is "under-powered" and
cannot be the sole signal. BT-utility power validated by simulation on synthetic data pre-freeze.
Total judgments ≈ **2,210 pairs (~4,420 both-order calls)**, within the 2–4k budget.

---

## 7. Stage-2 success criterion (RQ6 — the bar) and flip-test criterion

**Freeze `(ℓ*, ρ*, variant*)` on the dev sweep** (PLAN S2.3), selected as `argmax dev POC-gain s.t.
mean-KL ≤ 0.30 nats on the fixed 512-token eval text AND steered render-success ≥ 0.90`; write to
`config/steering_frozen.yaml`, **git-tag `steer-frozen` before touching held-out.**

**Success criterion (verbatim).** On held-out prompts (incl. 10 unseen-type), the direction is a
**causally sufficient design direction** iff: steered-NOSYS beats unsteered-NOSYS on **≥1 objective
family after Holm** AND the reliability-gated preference delta (steered ≻ unsteered) has BT-utility
cluster-bootstrap CI **> 0**; AND the **norm-matched random control (k=5 draws)** does **not** satisfy
both (specificity); AND the **flip test** attenuates the skill's gain (necessity). If addition
succeeds but the flip test does not → "**sufficient, not demonstrably necessary**." Report
`%skill-reproduced = (POC_steered − POC_unsteered)/(POC_FULL − POC_unsteered)×100 %` with CI.

**Flip-test criterion (S2.5).** Project `v̂` out at every layer/position (weight-orthogonalization)
while FULL is present; **necessity claimed** iff `attenuation% = (POC_FULL − POC_FULL-ablated)/
(POC_FULL − POC_unsteered)×100 %` has CI > 0.

**Side-effect tolerances (S2.6).** Steering must not drop non-UI algorithmic pass-rate by > 10 %
absolute nor push general-text mean KL > 0.30 nats; else report the trade-off / apply CAST gating.

---

## 8. The null rule (verbatim; non-negotiable, CLAUDE.md/BRIEF)

> An ablated component's effect, or a steering direction's effect, is reported as **null** unless it
> moves an objective-metric endpoint (POC Holm-significant, or ≥2 concordant BH-significant families)
> **OR** a preference delta that passes both the reliability gate and the power gate. Aesthetic claims
> not backed by the objective half are inadmissible. Stage-2 bar: a "design direction" is real only if
> steering it with **no design prompt** causally reproduces a measurable quality gain on held-out
> prompts; a direction that correlates but does not causally steer is a hypothesis, not a finding. If
> no clean steerable direction exists, that null is a result and is written up honestly.

---

## 9. Oracle validation gates (before any metric is used as evidence)

- **PSI** admitted as evidence only if Spearman ρ(PSI, human "AI-generated" rating) ≥ 0.4 (CI > 0) on
  the human subset; else demoted to descriptive diagnostic **and the confirmatory POC is recomputed
  without the −PSI term** (the §4 pre-specified conditional — not an amendment).
- **c\*** (POC colorfulness anchor): median Hasler-M of human-preferred pages **iff ≥ 30 such pages**
  exist in the human subset; else the pre-stated default = median Hasler-M of the dev FULL-cell
  generations (§4).
- **UIClip** admitted as auxiliary only if ρ(UIClip, human win-rate) ≥ 0.3; else dropped.
- Render-success is a hard gate feeding POC exclusion.

---

## 10. Pilot gate (P0, before the full factorial)

2 prompts × {FULL, NOSYS} × 3 seeds = 12 gens. **PASS iff** render ≥ 11/12 AND FULL≠NOSYS on PSI+≥2
families with a visible manual difference AND FULL−NOSYS POC gap > 0 on the majority of prompt×seed.
**FAIL →** fix prompt formatting and re-pilot; only if still no effect, trigger the **ADR-001 model
fallback to Llama-3.1-8B** (the sole sanctioned trigger; restarts both stages).

---

## 11. Determinism & engine policy (frozen)

vLLM = Stage-1 bulk generation; HF = all activation/steering; never cross-compare engines; any
Stage-1↔Stage-2 numeric comparison re-generates the baseline in HF (ADR-002). Sampling fixed:
T=0.7, top_p=0.9, top_k=40, rep_penalty=1.05, max_new_tokens=4096, seeds {0..4}. Render fixed: desktop
1440×900 (+mobile 390×844 for the RQ7 slice), DSF 1, animations disabled, offline, fonts-ready,
pinned Chromium/Playwright. Engine+version+sampling+config hashes recorded per row.

---

## 12. Amendments policy

Any change after the `prereg-v1` tag requires a **dated, numbered entry below** with: what changed,
why, and whether it affects a confirmatory decision (a confirmatory change forks a new tag
`prereg-v2` and is reported as a deviation in the paper). Exploratory additions are logged but do not
require a new tag. The frozen null rule (§8), the cell table (§3), the confirmatory family (§4), and
the Stage-2 success criterion (§7) may not be weakened post-freeze.

### Amendments log
*(none — freeze pending `prereg-v1` tag)*
