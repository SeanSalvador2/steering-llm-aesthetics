# B5 — AxBench: Even Simple Baselines Outperform Sparse Autoencoders (Wu et al. 2025)

**Citation.** Wu, Arora, Geiger, Wang, Huang, Jurafsky, Manning, Potts (Stanford). *AxBench: Steering LLMs? Even Simple Baselines Outperform Sparse Autoencoders.* ICML 2025. arXiv:2501.17148.

**TL;DR.** A large, standardized benchmark comparing steering and concept-detection methods head-to-head on Gemma-2-2B and 9B. Headline: for **steering, prompting wins, finetuning second, and difference-in-means (DiffMean) beats SAEs**; for **concept detection, DiffMean is best; SAEs are not competitive** on either. This is the primary evidence gating our ADR-008 (SAEs demoted to stretch).

## Method, in depth

**Concepts & scale.** ~500 concepts (16k concept set drawn from GemmaScope feature labels for the detection track), each with a natural-language description. Methods compared: **prompting, LoRA finetuning, DiffMean (difference-in-means), SAE / SAE-based steering, LAT (linear artificial tomography, the RepE reading-vector), linear probes, and ReFT-r1** (their new weakly-supervised Rank-1 Representation Finetuning), plus SAE-difference/decoder steering.

**Steering evaluation.** For each concept a target is injected; an **LLM judge scores three axes 0–2**: (i) concept expression (did the target concept appear?), (ii) instruction relevance (did it still answer?), (iii) fluency. These are combined into a **harmonic mean** so a method must satisfy all three (you can't win by emitting the concept word incoherently). Steering applied on the residual stream at a chosen layer (~layer 20 region for the 9B); coefficient tuned per method.

**Concept detection evaluation.** Given text, score how well each method's concept vector detects concept presence (ranking/AUC-style), measured against held-out labels.

**ReFT-r1.** A rank-1 representation-finetuning direction learned with weak supervision — designed to be competitive *and* interpretable, sitting between DiffMean (cheap, interpretable) and finetuning (strong, opaque). It is competitive on both tracks.

## Key results & numbers
- **Steering ranking:** prompting > finetuning > (ReFT-r1 ≈ DiffMean) > … > SAEs (bottom). SAEs "not competitive" on either track.
- **Concept detection:** representation methods, especially **DiffMean, perform best**; SAEs again not competitive.
- The authors release SAE-scale feature dictionaries for ReFT-r1 and DiffMean so the simple baselines can be used at SAE scale.
- Prompting being the steering winner is a crucial caution: an *intervention* method must be justified by what prompting *can't* do (our whole premise is "steer with **no** prompt," so prompting is not an option at test time — but the comparison sets the bar).

## Limitations / critiques
- Gemma-2 only; concept set is short single-token-ish concepts, not complex behaviours like "clean design."
- **Rebuttals exist:** Jørgensen & Hansen 2026 (arXiv:2605.31183) show SAEs can approach LoRA on AxBench *with a better supervised feature-selection pipeline*; Arad et al. 2025 (arXiv:2505.20063) get 2–3× SAE steering gains by filtering for "output features." So "SAEs lose" is really "naive SAE feature-picking loses"; the *default* baseline advantage of DiffMean still stands.
- Judge-based metric inherits LLM-judge biases (see C1).

## Relevance to Project 19
Directly confirms **ADR-008**: our primary Stage-2 method should be **difference-in-means**, not SAE-feature steering. DiffMean is the strongest *interpretable, training-free* steering/detection baseline in the largest existing comparison; SAEs would be a stretch even if a suite existed for our model (it doesn't for Qwen2.5-Coder — see D9). The harmonic-mean-of-three-axes evaluation is a template for combining our signals so a method can't "win" by wrecking the page.

## Borrow
- DiffMean as the default steering/probing vector.
- **Multi-axis combined score** (analogue: design-quality × render-success × instruction-adherence, combined so all must hold) to prevent degenerate "wins."
- ReFT-r1 as a fallback if pure DiffMean under-steers and we can afford light supervision.

## Avoid
- SAE-feature steering as the primary path (no Qwen2.5-Coder SAEs; loses to DiffMean by default; fragile per Ronge 2026).
- Judging steering on concept-expression alone — always couple with fluency/instruction axes (here: code validity).
