# SLOT_REGISTRY.md — the fill-in map

Every `\numslot{ID}` in the paper is an awaited number. This registry is the authoritative
map from each ID to (a) **what the number is**, (b) the **fill format** it will take,
(c) the **pipeline artifact** that produces it (results file + column, or notebook/script),
and (d) the **RUNBOOK session** (Sxx) that generates it. When the GPU phase lands, replace
`\numslot{ID}` with the value; the surrounding `\resultbranch` prose keeps exactly one branch
per RQ and needs no other edit.

- **Fill format** legend: `pt(CI)` = point estimate with 95% cluster-bootstrap CI, e.g.
  `0.42 (0.31, 0.53)`; `pct(CI)` = percentage with CI; `scalar` = single number;
  `label` = a categorical fill (a name, a ranking, PASS/DEMOTE, a band `13–19`, a variant).
- **RUNBOOK sessions** (see `RUNBOOK.md`): S1 pilot; S2–S3 Stage-1 generation; S4 render+metrics;
  S5 judging+reliability+BT; S6 extract+locate; S7 dev sweep+freeze; S8 held-out verify+flip+spec;
  S9 stretch (correspondence, early-token).
- **Analysis code**: Stage-1 objective deltas come from `p19.mixedlm` on `results/metrics.parquet`
  (column `poc`, per-cell contrasts); preference utilities from `p19.bt_model` on
  `results/judgments.parquet`; reliability from `p19.agreement`; power from `p19.power`;
  Stage-2 from `p19.steering`/`p19.probes`/`p19.patching` on `results/steering_runs.parquet` and
  `results/activations_meta.parquet`. Notebooks 05 (Stage-1) and 07b (Stage-2) orchestrate.

There are **79 distinct data slots** (107 uses). `EXAMPLE` in the introduction is an
**illustrative** placeholder that demonstrates the macro to the reader; it is not a data slot
and is filled by deleting the sentence's example or leaving it as pedagogy. (`\numslot{ID}`
appears only inside `main.tex` comments and never renders.)

---

## Headline / abstract (reuse body slots)

The abstract reuses body slot IDs for consistency; only `ABS-*` are abstract-specific.

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `ABS-SKILL-POC` → uses `HSKILL-POC` | FULL−NEUTRAL POC effect | pt(CI) | metrics.parquet:poc via mixedlm | S4 |
| `ABS-SKILL-WIN` → uses `HSKILL-WIN` | FULL win-rate vs NEUTRAL | pct(CI) | judgments.parquet via bt_model | S5 |
| `ABS-NEC-TOP` | the component(s) carrying most necessity weight | label | mixedlm necessity ranking (nb 05) | S4 |
| `ABS-LOC` | one-clause localization verdict (band, or "diffuse") | label | probes/patching (nb 06b) | S6 |
| `ABS-REPRO` → uses `STEER-REPRO` | % skill gain reproduced by steering | pct(CI) | steering_runs.parquet (nb 07b) | S8 |

## H-skill — does the skill work, and is it content?

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `HSKILL-POC` | FULL−NEUTRAL standardized δ on POC | pt(CI) | metrics.parquet:poc, mixedlm contrast | S4 |
| `HSKILL-BT` | FULL−NEUTRAL BT utility (logits) | pt(CI) | judgments.parquet, bt_model | S5 |
| `HSKILL-WIN` | FULL win-rate over NEUTRAL | pct(CI) | judgments.parquet, win-rate | S5 |
| `HSKILL-NOSYS-PCT` | % of the FULL−NOSYS gap that FULL closes over NOSYS | pct | metrics.parquet:poc, cell means | S4 |
| `NEU-NOSYS` | NEUTRAL−NOSYS POC contrast (prompt-mass control) | pt(CI) | metrics.parquet:poc, mixedlm | S4 |

## RQ1 — component necessity (FULL − LOO-Cᵢ)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `NEC-C1`…`NEC-C5` | necessity δ on POC for C1…C5 | pt(CI) | metrics.parquet:poc, mixedlm LOO contrasts | S4 |
| `NEC-C1-BT`, `NEC-C5-BT` | necessity BT utility for the two expected-large components | pt(CI) | judgments.parquet, bt_model | S5 |
| `NEC-NSURV` | # of 5 LOO contrasts surviving Holm on POC | scalar | multiplicity (nb 05) | S4 |
| `NEC-RANK` | necessity ranking of components (e.g. `C5 > C1 > C3 > C2 > C4`) | label | mixedlm δ ordering | S4 |
| `NEC-REPL-TOP` | held-out necessity δ of the top component (replication) | pt(CI) | metrics.parquet:poc (heldout split) | S4 |

## RQ2 — component sufficiency (AOI-Cᵢ − NEUTRAL)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `SUFF-C1`…`SUFF-C5` | sufficiency δ on POC for C1…C5 | pt(CI) | metrics.parquet:poc, mixedlm AOI contrasts | S4 |
| `SUFF-MAXPCT` | largest AOI lift as % of the FULL−NEUTRAL gap | pct(CI) | metrics.parquet:poc, cell means | S4 |
| `SUFF-NSURV` | # of 5 AOI contrasts surviving Holm | scalar | multiplicity (nb 05) | S4 |
| `SUFF-TOP` | component with the largest single-component lift | label | mixedlm δ ordering | S4 |

## RQ3 — interactions (2FIs from the factorial MixedLM)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `INT-NSURV` | # of 10 two-factor interactions surviving BH | scalar | mixedlm.fit_factorial (nb 05) | S4 |
| `INT-MAXPAIR` | the largest-magnitude surviving 2FI pair (e.g. `C1×C5`) | label | factorial coefficients | S4 |
| `INT-MAX` | that pair's 2FI coefficient βᵢⱼ (POC units) | pt(CI) | factorial coefficients | S4 |
| `INT-C1C5` | C1×C5 2FI coefficient (expected super-additive) | pt(CI) | factorial coefficients | S4 |
| `INT-C2C3` | C2×C3 2FI coefficient (expected sub-additive) | pt(CI) | factorial coefficients | S4 |

## RQ4 — nudge (FULL vs BEAUTY1 vs NEUTRAL)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `NUDGE-FB` | FULL−BEAUTY1 POC δ | pt(CI) | metrics.parquet:poc, mixedlm | S4 |
| `NUDGE-BN` | BEAUTY1−NEUTRAL POC δ | pt(CI) | metrics.parquet:poc, mixedlm | S4 |
| `NUDGE-BPCT` | BEAUTY1 as % of the FULL−NEUTRAL gap | pct(CI) | metrics.parquet:poc, cell means | S4 |
| `NUDGE-FBWIN` | FULL win-rate over BEAUTY1 | pct(CI) | judgments.parquet, bt_model | S5 |

## RQ7 (black-box slice) — per-task-type FULL−NEUTRAL

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `BB-SEEN` | mean seen-type FULL−NEUTRAL POC δ | pt(CI) | metrics.parquet:poc by task_type | S4 |
| `BB-UNSEEN` | mean unseen-type (OOD) FULL−NEUTRAL POC δ | pt(CI) | metrics.parquet:poc by task_type | S4 |

## Oracle validation (F4, F10)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `PSI-RHO` | Spearman ρ(PSI, human "AI-generated" rating) | pt(CI) | p19.oracle_validation on human_labels.csv | S4 |
| `POCVAR` | which POC fires: `7-term` or `6-term` | label | oracle_validation (PSI gate) | S4 |
| `CSTAR` | colorfulness anchor c* (Hasler M units) | scalar | oracle_validation (c* branch) | S4 |
| `UICLIP-RHO` | Spearman ρ(UIClip, human win-rate) | pt(CI) | oracle_validation | S5 |

## Reliability gate (F11)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `REL-ALPHA` | Krippendorff α_K (ordinal), judge vs human | pt(CI) | p19.agreement on human_labels.csv | S5 |
| `REL-AC1` | Gwet AC1, judge vs human | pt(CI) | p19.agreement | S5 |
| `REL-PIMAX` | marginal skew π_max of the preference labels | scalar | agreement.marginal_distribution | S5 |
| `REL-GATE` | gate outcome: `PASS (α)` / `PASS (AC1 under skew)` / `cascade` | label | agreement.reliability_gate | S5 |

## Power (T10)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `POW-TIE` | observed tie rate over judged pairs | pct | judgments.parquet:consistent | S5 |
| `POW-FN` | achieved decisive pairs on FULL−NEUTRAL | scalar | power.achieved_n on judgments | S5 |
| `POW-NEC` | achieved decisive pairs per necessity edge | scalar | power.achieved_n | S5 |
| `POW-UNDER` | # of confirmatory preference edges under-powered post-hoc | scalar | power gate (nb 05) | S5 |

## RQ5 — locate (F5, F13); stability (S2.0)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `STAB-DCOS` | Δcos of the running mean over the last 20% of examples | scalar | activations_meta.parquet, stability | S6 |
| `STAB-PLATN` | n examples at which the cosine plateau is reached | scalar | activations stability check | S6 |
| `LOC-BAND` | chosen layer band (e.g. `13–19`) or `diffuse` | label | probes+patching decision (nb 06b) | S6 |
| `LOC-AUCPEAK` | peak per-layer probe AUC | scalar | p19.probes AUC | S6 |
| `LOC-PEAKLAYER` | layer of the AUC peak | scalar | p19.probes | S6 |
| `LOC-SELPEAK` | peak control-task selectivity | scalar | p19.probes selectivity | S6 |
| `LOC-PATCHPEAK` | peak patch %-recovered of the clean−corrupt gap | pct | p19.patching | S6 |

## RQ6 — steer + freeze operating point (F6, F7)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `STEER-LSTAR` | frozen layer ℓ* | scalar | config/steering_frozen.yaml (S2.3) | S7 |
| `STEER-RHOSTAR` | frozen norm-relative coefficient ρ* | scalar | config/steering_frozen.yaml | S7 |
| `STEER-VARIANT` | frozen position variant (mean-response / last-prompt / first-k) | label | config/steering_frozen.yaml | S7 |
| `STEER-DEVGAIN` | dev POC-gain at the frozen point | pt(CI) | steering_runs.parquet:poc (dev sweep) | S7 |
| `STEER-KL` | mean per-token KL at ρ* on the eval text | scalar | steering_runs.parquet:kl | S7 |
| `STEER-RENDER` | steered render-success at ρ* | pct | steering_runs.parquet:render_success | S7 |

## RQ6 — held-out causal verification (F8)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `STEER-DELTA` | steered−unsteered POC δ (held-out) | pt(CI) | steering_runs.parquet:poc (arm contrast) | S8 |
| `STEER-DELTA-CI` | the null-branch CI on the steered−unsteered δ (explicit interval) | CI | steering_runs.parquet:poc | S8 |
| `STEER-BT` | steered≻unsteered BT utility | pt(CI) | judgments.parquet (S2.4 edges), bt_model | S8 |
| `STEER-NFAM` | # of 6 objective families where steered beats unsteered (Holm) | scalar | mixedlm over families (nb 07b) | S8 |
| `STEER-RAND` | norm-matched random-control POC δ (k=5 mean) | pt(CI) | steering_runs.parquet:poc (arm=random) | S8 |
| `STEER-REPRO` | % of the skill's POC gain reproduced by steering | pct(CI) | steering_runs.parquet, reproduction fraction | S8 |

## Flip test (necessity, S2.5) and specificity (S2.6)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `FLIP-ATTEN` | attenuation % of the skill gain when v̂ is projected out | pct(CI) | flip results (p19.steering weight-orth) | S8 |
| `SPEC-PASSDROP` | absolute drop in non-UI algorithmic pass-rate under steering | pct | spec results on noncode_probe.yaml | S8 |
| `SPEC-KL` | general-text mean per-token KL under steering | scalar | spec results (KL eval set) | S8 |

## RQ7 — failure surface (F12)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `FAIL-ANTI-OVERALL` | overall anti-steerable fraction (steered POC < unsteered) | pct | steering_runs.parquet, per-prompt | S8 |
| `FAIL-ANTI-UNSEEN` | anti-steerable fraction on unseen (OOD) types | pct | steering_runs.parquet, split=unseen | S8 |
| `FAIL-UNSEEN-D` | mean unseen-type steering POC δ | pt(CI) | steering_runs.parquet:poc by type | S8 |
| `FAIL-REPRO-UNSEEN` | % skill reproduced on unseen types | pct(CI) | reproduction fraction (unseen) | S8 |
| `FAIL-WORST-TYPE` | the most brittle task type | label | anti-steerable by type (nb 07b) | S8 |
| `FAIL-WORST-ANTI` | that type's anti-steerable fraction | pct | steering_runs.parquet by type | S8 |

## RQ8 — correspondence (F9, stretch)

| ID | what it is | format | artifact / column | session |
|---|---|---|---|---|
| `CORR-COSMEAN` | mean |cos| among component sub-vectors (off-diagonal) | scalar | correspondence cosine matrix (nb 07b) | S9 |
| `CORR-COSMAX` | max |cos| among sub-vectors (off-diagonal) | scalar | correspondence cosine matrix | S9 |
| `CORR-NMATCH` | # of 5 sub-vectors steering their own metric family | scalar | signature-match grid | S9 |

---

### Fill checklist (per RUNBOOK session)

- **After S4 (render+metrics):** all `HSKILL-*` (POC), `NEU-NOSYS`, `NEC-C*`, `SUFF-*`, `INT-*`,
  `NUDGE-*` (POC parts), `BB-*`, `PSI-RHO`, `POCVAR`, `CSTAR`, `NEC-RANK`, `NEC-NSURV`,
  `SUFF-NSURV`, `SUFF-TOP`, `NEC-REPL-TOP`.
- **After S5 (judging+reliability):** all BT slots (`HSKILL-BT`, `NEC-*-BT`, `NUDGE-FBWIN`),
  `UICLIP-RHO`, `REL-*`, `POW-*`.
- **After S6 (extract+locate):** `STAB-*`, `LOC-*`, `ABS-LOC`.
- **After S7 (sweep+freeze):** `STEER-LSTAR/RHOSTAR/VARIANT/DEVGAIN/KL/RENDER`.
- **After S8 (held-out verify):** `STEER-DELTA/DELTA-CI/BT/NFAM/RAND/REPRO`, `FLIP-ATTEN`,
  `SPEC-*`, `FAIL-*`, `ABS-REPRO`.
- **After S9 (stretch):** `CORR-*`.

### Which branch to keep (delete the others)

- H-skill: `works` | `null`
- RQ1: `necessary (ranked)` | `null` | `negative`
- RQ2: `distributed` | `one-carries` | `null`
- RQ3: `interacting` | `additive` | `dominated by a single main effect`
- RQ4: `content` | `nudge` | `neither`
- RQ5: `RQ5 localized` | `RQ5 diffuse`
- RQ6 (top level): Branch **A** (sufficient) | Branch **B** (null) | Branch **C** (one of C.1–C.4)
  - within A: `A.1 sufficient and necessary` | `A.2 sufficient, not demonstrably necessary`
  - within A: `RQ7 robust` | `RQ7 partial` | `RQ7 brittle`
  - within A: `RQ8 found` | `RQ8 partial` | `RQ8 absent`
- Discussion bridge: `bridge holds` | `bridge fails`
