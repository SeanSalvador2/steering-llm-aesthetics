# Anatomy of a Design Skill

A two-stage research study of *why* a short "frontend-design skill" — a few hundred tokens
of design guidance — dramatically improves LLM-generated user interfaces.

- **Stage 1 (black-box ablation):** decompose the skill into five components and measure,
  factorially and causally, which ones carry the effect on UI quality.
- **Stage 2 (mechanistic interpretability):** locate where the guidance acts inside the
  model's activations, extract a "clean-design" steering vector, and test whether injecting
  it — with **no design prompt at all** — causally reproduces the quality gain.

Subject model (both stages): `Qwen/Qwen2.5-Coder-7B-Instruct`. Every quality claim must
move two independent signals: deterministic metrics computed on the rendered page, and a
reliability-gated pairwise preference protocol. A pre-registered null ("design behavior is
not linearly steerable") is a reportable finding, not a failure.

## Status

**CPU-validated, GPU phase pending.** All machinery is built, tested (137 tests), and
demonstrated end-to-end on synthetic data with known ground truth; no subject-model
inference has been run yet. Execution happens on Colab per `RUNBOOK.md`.

## Where to start

| If you want… | Read |
|---|---|
| The plain-language guided tour of everything | `SEAN-README.md` |
| The authoritative experimental design | `PLAN.md` (frozen rules: `PREREGISTRATION.md`) |
| The mathematical derivations | `THEORY.md` |
| The narrative walkthrough with executed code | `notebooks/00_overview.ipynb` onward |
| The paper (results slots await real data) | `paper/main.pdf` |
| Why each design decision was made | `docs/DECISIONS.md` |
| The literature this builds on | `research/SYNTHESIS.md` |
| How to run the GPU phase | `RUNBOOK.md` |

## Quickstart (CPU)

```bash
pip install -e . -r requirements-cpu.txt
pytest -q                          # full suite; no GPU or network needed at test time
python scripts/make_configs_check.py   # validate frozen configs, audits, token masses
python scripts/run_metrics_demo.py     # render fixtures and compute the metric stack
```

Notebooks `00–03`, `05`, `06a`, `07a`, and `08` are shipped executed; `04`, `06b`, and
`07b` are GPU scaffolds for the Colab sessions.
