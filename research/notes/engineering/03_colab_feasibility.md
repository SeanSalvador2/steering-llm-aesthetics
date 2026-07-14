# D-c — Google Colab (2026) feasibility for the GPU phase

**Sources.** Colab FAQ (research.google.com/colaboratory/faq.html) + 2026 Colab guides (Hivenet, Bison KB, Thunder Compute Jul-2026). Figures are approximate/subject to change — verify at run time.

## GPU tiers & VRAM (2026)
| GPU | VRAM | Notes | Fit for our 7–8B bf16 (~15–16 GB) |
|---|---|---|---|
| **T4** | 16 GB (≈15 usable, ECC) | free/Pro; ~1.76 compute units/hr | **Generation only via 4-bit**; too tight for bf16 + activations |
| **L4** | 24 GB | Pro; good default | **Workable** — bf16 weights (~15 GB) + KV/activations (~8 GB) |
| **A100** | 40 or 80 GB (via High-RAM slider) | Pro/Pro+; ~15 CU/hr | **Comfortable** — headroom for full-sequence activation capture |

- **Compute Units:** Colab Pro ≈ **$12.67/mo, ~100 units/mo**; Pro+ ≈ **$50/mo, ~500 units**; pay-as-you-go available. A100 burns ~**15 CU/hr** → ~33 hr on a 500-unit budget; L4 far cheaper. Budget the GPU phase around L4 with A100 for the activation-capture passes.
- **Sessions:** up to **12 h** (Pro), **24 h** (Pro+ with units); **idle disconnect ~90 min**. → checkpoint aggressively; make every stage resumable.
- **High-RAM** runtime available (needed if holding many activations in CPU RAM).

## Drive persistence pattern
- Mount Google Drive; write **artifacts (HTML, screenshots, activations, results JSONL/Parquet) to Drive**, not the ephemeral VM disk (lost on disconnect). Manifest-track artifacts (CLAUDE.md orchestration rules). Keep large activation tensors as `.safetensors`/`.npy` shards on Drive; store only chosen-layer captures to bound size.

## Workload sizing (rough)
- **Stage 1 generation:** ~(16 factorial cells + 4 controls) × prompts (say 40) × seeds (5) ≈ **4,000 generations** (+ LOO/AOI cells). At ~30–60 tok/s HF or ~1–2k tok/s vLLM batched (D4), single-file HTML ~2–4k tokens → vLLM makes Stage-1 generation a few GPU-hours; HF-generate would be ~10× slower. → **use vLLM for Stage-1 bulk generation**, HF for Stage-2 activation work (D4).
- **Stage 2 activation capture:** forward passes only (no sampling) over the contrast sets on chosen layers; cheap. Steering-generation passes use HF hooks (slower, but far fewer generations on held-out prompts).

## Verdict (feeds D1/D2)
Entirely feasible on **Colab Pro/Pro+ with L4 (default) + A100 (activation/steering passes)**. No blocker. Key operational rules: checkpoint every stage to Drive; keep activation captures to selected layers; run bulk generation on vLLM, activation/steering on HF; expect ~90-min idle kills → resumable pipeline. bf16 on L4/A100; 4-bit only for T4 generation-only fallback (note determinism caveat vs bf16).
