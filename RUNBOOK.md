# RUNBOOK.md — Colab execution (GPU phase)

Session-by-session execution for everything that needs the subject model
(`Qwen/Qwen2.5-Coder-7B-Instruct`, locked, ADR-001). **Nothing here runs in the CPU dev
environment** (CLAUDE.md compute policy): all the code is written, unit-tested (mocks / a tiny
Qwen2 stand-in), import-guarded, and left unexecuted until Colab. The CPU-safe half (rendering,
metrics, judge dry-run, statistics, all tests) already runs and is green locally.

**Hard blocks (PLAN §0.5).** `PREREGISTRATION.md` git-tagged `prereg-v1` blocks all GPU work →
Pilot PASS blocks P1 → P1 blocks P2 blocks P3. The dev sweep (S2.3) must **freeze**
`(ℓ*, ρ*, variant*)` and git-tag `steer-frozen` **before** any held-out generation (P6); held-out
is touched exactly once.

**Golden rules.** Checkpoint to Drive every 200 units; every stage is resumable via the manifest
(`Manifest.hashed_paths()` → skip). Never compare a vLLM baseline to an HF steered output — any
Stage-1↔Stage-2 comparison re-generates the baseline in HF (ADR-002). Engine + version + sampling
+ config hashes are stamped on every row (`manifest.run_manifest`, PREREG §11).

---

## Environment setup cell (run first, every session)

```bash
# Colab. Chromium for rendering is only needed in the CPU render/metrics session (P2/4).
pip install -e ".[gpu,vllm,judge]"          # torch, transformers, accelerate, vllm, judge clients
# HF auth (model is Apache-2.0, ungated, but token avoids rate limits):
python -c "from huggingface_hub import login; login()"   # paste HF token
# One-time model fetch (~15.2 GB bf16):
python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-Coder-7B-Instruct')"
# Mount Drive; all artifacts/checkpoints go to Drive, NOT the ephemeral VM disk:
python -c "from google.colab import drive; drive.mount('/content/drive')"
export P19_ARTIFACTS=/content/drive/MyDrive/p19/artifacts
export P19_RESULTS=/content/drive/MyDrive/p19/results
```

Record `pip freeze > $P19_RESULTS/env.lock` at the start of each GPU session (determinism, PLAN §VI.5).

---

## Session table (PLAN §VI.6)

| # | session | GPU | est. | inputs | outputs | acceptance check (eyeball before next) |
|---|---|---|---|---|---|---|
| 1 | **Pilot (P0)** | L4 | 0.5 h | skill+prompts | 12 gens + screenshots | render ≥ 11/12; FULL≠NOSYS on PSI + ≥2 families; POC gap > 0 on majority — else fallback |
| 2 | **Stage-1 gen A (P1)** | L4 | 3 h | cells, dev prompts | ~2,000 dev gens | render-success ≥ 0.9; no engine errors; checkpoints every 200 |
| 3 | **Stage-1 gen B (P1)** | L4 | 3 h | remaining dev + held | cumulative 4,630 gens | spot-render 20 pages OK |
| 4 | **Render + metrics (P2)** | **CPU** | 2 h | all HTML | `metrics.parquet`; F4, F10 | PSI validates (ρ≥0.4) or demote to 6-term POC; metric ranges sane |
| 5 | **Judging (P3)** | **CPU/API** | 2 h | screenshots | judgments; α/AC1; BT | reliability gate passes (α≥0.667 or AC1≥0.80 under skew) — else cascade |
| 6 | **Extract + locate (P4)** | A100 | 2 h | FULL/NEUTRAL dev gens | `v_l`, probes, patching; F5, F13 | cosine plateau reached; a mid-band probe AUC ≥ 0.80 |
| 7 | **Dev sweep (P5)** | A100 | 4 h | `v_l`, dev subset | F6, F7; **freeze** (ℓ*,ρ*,var) | a guardrail-satisfying POC-gain>0 config exists → **git-tag `steer-frozen`** |
| 8 | **Held-out verify (P6)** | A100 | 3 h | frozen config, held-out | S2.4–S2.7; F8, F12 | success criterion evaluated; random control ≠ steered |
| 9 | **Stretch (P7)** | A100 | 2 h | AOI vectors, subsets | S2.8–S2.9; F9 | correspondence decision; early-token comparison |
| — | **buffer / re-runs** | A100 | 3 h | — | — | contingency (contrast noise, under-power, sweep re-do) |

Budget: ~6 L4-h + ~14 A100-h ≈ **243 CU ≈ $50–65**; judge ≈ **$14** (PLAN §VI.7).

---

## Session 1 — Pilot (gate zero, §III.9 / PREREG §10)

```bash
python scripts/run_stage1_generation.py --dry-run          # confirm plan (4,630) + provenance
# pilot subset: 2 prompts (L01 easy, D02 hard) x {FULL, NOSYS} x 3 seeds = 12 gens
python -m p19.pilot --prompts L01 D02 --cells FULL NOSYS --seeds 0 1 2 \
       --out $P19_ARTIFACTS/pilot --engine vllm            # (thin wrapper over generation_vllm)
# render + metric the 12 (CPU path, but fine on the GPU box):
python scripts/run_metrics_demo.py --glob "$P19_ARTIFACTS/pilot/*.html"   # ad-hoc metric pass
```
**PASS iff** render ≥ 11/12 AND FULL≠NOSYS on PSI + ≥2 objective families with a visible manual
difference (save the 12 screenshots) AND FULL−NOSYS POC gap > 0 on the majority of prompt×seed.
**FAIL →** (a) fix prompt formatting (verify `apply_chat_template`, system-vs-user placement, skill
not truncated, special tokens) and re-pilot; (b) only if still no effect after format fixes,
trigger the **ADR-001 model fallback to Llama-3.1-8B** (the sole sanctioned trigger; restarts both
stages, requires an ADR note).

## Sessions 2–3 — Stage-1 generation (P1)

```bash
python scripts/run_stage1_generation.py --split dev  --out $P19_ARTIFACTS/stage1 \
       --manifest $P19_RESULTS/stage1_manifest.jsonl        # ~2,000; resumes from manifest
python scripts/run_stage1_generation.py --split heldout --out $P19_ARTIFACTS/stage1 \
       --manifest $P19_RESULTS/stage1_manifest.jsonl        # +630 → cumulative 4,630
```
Sampling is fixed (T=0.7, top_p=0.9, top_k=40, rep_penalty=1.05, max_new_tokens=4096, seeds {0..4};
interaction cells seeds {0..2}). vLLM only (bulk throughput). Checkpoint every 200 units to Drive.
**Acceptance:** cumulative 4,630; render-success ≥ 0.9 on a 20-page spot check.

## Session 4 — Render + objective metrics (P2, CPU-OK — can run locally)

```bash
# Chromium preinstalled at /opt/pw-browsers locally; on Colab: playwright install chromium
python -m p19.render_all --html-dir $P19_ARTIFACTS/stage1 --out $P19_RESULTS \
       --manifest $P19_RESULTS/render_manifest.jsonl        # screenshots + DOM-JSON + metrics.parquet
python -m p19.oracle_validation --metrics $P19_RESULTS/metrics.parquet \
       --human $P19_RESULTS/human_labels.csv                # PSI ρ≥0.4 gate; c* branch; F4, F10
```
**Acceptance (PREREG §9):** PSI validates (ρ≥0.4) — else the confirmatory POC drops the −PSI term
(6-term POC, recorded in the manifest before any confirmatory test); c* branch chosen (human ≥30 →
median human-preferred M, else median dev-FULL M); metric ranges sane.

## Session 5 — Judging + reliability + BT (P3, API)

```bash
python scripts/run_judging.py --dry-run                     # confirm the comparison graph
python -m p19.judge_run --graph dev --primary gemini-2.5-flash --audit gpt-4o --audit-frac 0.15 \
       --screenshots $P19_RESULTS/screenshots --out $P19_RESULTS/judgments.parquet   # both orders
python scripts/run_analysis.py --stage reliability --human $P19_RESULTS/human_labels.csv
```
**Acceptance (PREREG §5):** reliability gate passes — α_K ≥ 0.667 OR (AC1 ≥ 0.80 with demonstrable
skew π_max ≳ 0.80). **Fail → cascade:** revise rubric → swap judge (GPT-4o/Claude) → escalate humans
to N=300 + down-weight judge → objective-only null decisions. Judge temperature 0; both orders;
order-inconsistent → tie.

## Session 6 — Extract + locate (P4)

```bash
python scripts/run_stage2_extraction.py --dry-run
python -m p19.stage2_extract --corpus full_neutral_dev --layers 11-20 \
       --out $P19_RESULTS/activations                       # S2.0 means + F13 stability
python -m p19.stage2_locate --activations $P19_RESULTS/activations \
       --out $P19_RESULTS/localization                      # probes + patching → F5, band (RQ5)
```
Reuses the Stage-1 FULL/NEUTRAL dev generations (200/side) — teacher-forced HF forward, mean-
response capture. **Acceptance:** cosine plateau reached (Δcos < 0.01 over the last 20% at focus
layers) — else extend seeds 5–7 and re-check; a mid-band probe AUC ≥ 0.80 with selectivity ≥ 0.15.

## Session 7 — Dev sweep → FREEZE (P5)

```bash
python scripts/run_stage2_steering.py --dry-run             # 35 coarse configs + arms
python -m p19.stage2_sweep --stage coarse --out $P19_RESULTS/sweep    # 5 layers x 7 ρ x mean-resp
python -m p19.stage2_sweep --stage refine --out $P19_RESULTS/sweep    # best 2 layers x 3 ρ x 3 var
python -m p19.stage2_freeze --sweep $P19_RESULTS/sweep --write config/steering_frozen.yaml
git add config/steering_frozen.yaml && git commit -m "freeze steering operating point" \
       && git tag steer-frozen                              # BEFORE any held-out generation
```
**Acceptance (PREREG §7):** a guardrail-satisfying config exists — dev POC-gain > 0 (bootstrap
CI > 0) s.t. mean-KL ≤ 0.30 nats AND steered render-success ≥ 0.90; ties → lower KL. If no single-
layer config clears it → escalate to multi-layer injection or the 2–4D subspace (pre-stated
fallbacks), then re-select. **Do not proceed to Session 8 without the `steer-frozen` tag.**

## Session 8 — Held-out causal verification (P6, THE BAR)

```bash
python -m p19.stage2_verify --frozen config/steering_frozen.yaml --heldout \
       --arms unsteered steered random full_ref --k-random 5 --out $P19_RESULTS/verify   # 432 gens
python -m p19.stage2_flip --frozen config/steering_frozen.yaml --out $P19_RESULTS/flip    # S2.5
python -m p19.stage2_specificity --noncode config/noncode_probe.yaml --out $P19_RESULTS/spec  # S2.6
python scripts/run_analysis.py --stage stage2 --results $P19_RESULTS
```
**Success criterion (PREREG §7, verbatim):** steered-NOSYS beats unsteered-NOSYS on ≥1 objective
family after Holm AND the reliability-gated preference delta (steered ≻ unsteered) has BT-utility
cluster-bootstrap CI > 0 AND the norm-matched random control (k=5) does NOT satisfy both AND the
flip test attenuates. Addition succeeds but flip does not → "sufficient, not demonstrably
necessary." Report %skill-reproduced with CI. **Acceptance:** criterion evaluated; random control ≠
steered (specificity); side-effect tolerances met (algorithmic pass-rate drop ≤ 10%; general-text
mean KL ≤ 0.30).

## Session 9 — Stretch (P7)

```bash
python -m p19.stage2_correspondence --aoi-vectors $P19_RESULTS/activations --out $P19_RESULTS/corr  # S2.8
python -m p19.stage2_early_token --frozen config/steering_frozen.yaml --k 16 64 256 --out ...        # S2.9
```
**Acceptance:** correspondence decision (found if mean |cos| < 0.3 AND ≥3/5 signatures match);
early-vs-full steering comparison.

---

## Failure playbooks

- **OOM (activation capture / steering).** Batch-size ladder: 8 → 4 → 2 → 1; capture *chosen layers
  only* (11–20), running means not full sequences (~0.8 GB/example otherwise, 01_qwen_model_facts);
  A100-40GB → High-RAM 80GB slider; last resort 4-bit for generation-only arms (note the determinism
  caveat — never mix 4-bit and bf16 within a comparison).
- **Session disconnect (~90-min idle).** Every stage reads its manifest and skips already-hashed
  units (`Manifest.hashed_paths()`); resume by re-running the same command — it continues from the
  last Drive checkpoint. Keep a browser tab active; checkpoint every 200 units.
- **vLLM/HF mismatch.** Never cross-compare (ADR-002). For any Stage-1↔Stage-2 number, re-generate
  the baseline in HF with the same sampling + seed.
- **Render nondeterminism.** Pinned Chromium + viewport + DSF 1 + animations disabled + offline +
  fonts-ready; if the Chromium/Playwright version changes, regenerate ALL screenshots together.
- **MixedLM non-convergence.** The `fit_factorial` / `fit_mixedlm` ladder auto-falls back
  (lbfgs → bfgs → cg → powell → OLS with prompt-clustered SEs / cluster bootstrap); the rung used is
  recorded per model (THEORY T3.6).
- **Under-powered preference edge.** Raise seed-pairs (pre-stated contingency, up to the 4k budget);
  if still under-powered, fall back to the objective channel for the two-signal null rule (never
  reinterpret an under-powered delta as a null).
