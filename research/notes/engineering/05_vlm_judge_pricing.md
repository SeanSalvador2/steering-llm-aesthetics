# D-f — VLM judge options & cost (July 2026)

**Sources.** 2026 API-pricing aggregators (benchlm.ai, intuitionlabs, aipricing.guru, ai.google.dev/gemini-api/docs/pricing). Prices approximate as of Jul 2026 — verify at run time; per-image token accounting varies by provider.

## Candidate judges (vision-capable)
| Model | ~Input $/1M tok | ~Output $/1M tok | Notes |
|---|---|---|---|
| **Gemini 2.5 Flash** | ~$0.15–0.30 | ~$0.60–2.50 | cheapest strong vision; high rate limits; good primary |
| Gemini 2.5 Flash-Lite | ~$0.10 | ~$0.40 | cheapest; possible bulk pre-screen |
| **GPT-4o / 4.1-class** | ~$2.50 | ~$10 | strong, different family from Qwen (avoids self-enhancement) |
| **Claude (Sonnet-class) vision** | ~$3 | ~$15 | strong reasoning judge; Opus-class $5/$25 |
| Qwen2.5-VL-72B (via provider) | low (open) | low | **avoid as primary** (same family as subject → self-enhancement bias, C1) |

- **Image token cost:** each screenshot consumes image tokens (provider-specific; e.g. a ~1024px image ≈ hundreds–~1290 tokens depending on provider/detail). Budget ~**1k input tokens per screenshot** as a planning figure; a pairwise judgment = 2 screenshots + rubric prompt (~1–1.5k text) ≈ **~3–3.5k input tokens** + a short structured output (~200 tok).

## Cost estimate for our volume (D6 arithmetic)
Assume **2,000–4,000 pairwise judgments**, each **both orders** (×2 calls) to control position bias, ~3.5k input + 0.2k output tokens per call.
- Calls = 4,000 judgments × 2 orders = **8,000 calls** (upper end).
- Tokens ≈ 8,000 × (3.5k in + 0.2k out) = **28M input + 1.6M output**.
- **Gemini 2.5 Flash** (~$0.30/$2.50): ≈ 28×$0.30 + 1.6×$2.50 = **$8.4 + $4.0 ≈ $12** (upper end). Flash-Lite ≈ **$3–5**.
- **GPT-4o** (~$2.50/$10): ≈ 28×$2.50 + 1.6×$10 = **$70 + $16 ≈ $86**.
- **Claude Sonnet-class** (~$3/$15): ≈ **$84 + $24 ≈ $108**.
- Lower end (2,000 judgments, single order for exploratory): ~¼ of the above.

⇒ **Total judge cost is trivial-to-modest**: ~$10–15 on Gemini Flash, ~$85–110 on GPT-4o/Claude for the full both-orders 4k set. Even validating with two judges is cheap.

## Recommendation (D6)
- **Primary judge: Gemini 2.5 Flash** — cheapest strong vision, high rate limits (bulk both-orders judging), different family from Qwen. Run the full pairwise set here.
- **Secondary/validation judge: GPT-4o or Claude Sonnet-class** — different family; run on a **subset** to (a) measure cross-judge chance-corrected agreement (C2) and (b) confirm the primary isn't idiosyncratic. Budget allows the secondary on the full set if desired (~$85–110).
- **Human-labeled subset** (the reliability ground truth, ADR-005): a few hundred pairs, both orders, ≥2 human raters → compute judge-vs-human α/AC1 and human-human α/AC1.
- **Rate limits:** Flash tiers allow high RPM; batch with backoff; both-orders + rubric per call. Cache the rubric as a system prompt.

## Guards (from C1)
- Both presentation orders; tie if inconsistent. Rubric-anchored/checklist (ArtifactsBench-style). Judge ≠ subject family. Cross-check judge verdicts vs objective metrics to catch colorfulness/verbosity bias. Report chance-corrected judge-human agreement before trusting any delta.
