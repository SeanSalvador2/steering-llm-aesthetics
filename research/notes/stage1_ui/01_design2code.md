# A1 — Design2Code: How Far Are We From Automating Front-End Engineering? (Si et al. 2024)

**Citation.** Si, Zhang, Yang, Liu, Yang. *Design2Code.* arXiv:2403.03163 (2024). Project: salt-nlp.github.io/Design2Code.

**TL;DR.** Benchmark of **484 real webpages** (screenshot → HTML) with a suite of **automatic, DOM/render-based metrics** that decompose "does the generated page match the target" into fine-grained, non-aggregated scores. This is the template for our *objective* oracle: block detection + matching, then per-dimension text/position/color/CLIP scores. (Task is screenshot-to-code; ours is text-to-code, so we adapt the *metric machinery*, not the reference-image dependence.)

## Method, in depth

**Benchmark.** 484 webpages curated from C4/Common-Crawl, made hermetic (inline CSS, images replaced with placeholders) so rendering is deterministic — **the same hermetic-single-file constraint we adopt (ADR-006).**

**Evaluation pipeline.** Render both reference and generated HTML (headless browser), detect **visual blocks** (text/element regions), align reference↔generated blocks with the **Jonker–Volgenant** assignment algorithm, then score five fine-grained dimensions (deliberately **not** aggregated):
1. **Block-Match** — matched block area / total block area; penalizes missing or hallucinated elements.
2. **Text similarity** — character overlap per matched block via **Sørensen–Dice**.
3. **Position similarity** — alignment accuracy of matched block centers (normalized distance).
4. **Color similarity** — text-color difference via **CIEDE2000** perceptual color distance.
5. **CLIP similarity (high-level)** — cosine similarity of CLIP embeddings of the two full screenshots (overall visual resemblance).

**Prompting methods.** Direct prompting, **text-augmented** (feed extracted text), and **self-revision** (model critiques/edits its own output) on GPT-4V and Gemini Pro Vision; plus an open **Design2Code-18B** finetune.

**Human eval.** Pairwise: annotators judge visual appearance + content. GPT-4V pages judged able to *replace* the original in **49%** of cases and rated **better** than the original in **64%** — evidence that automatic metrics need human corroboration (our two-signal oracle).

## Key results & numbers
- GPT-4V best; open models lag mainly on **recalling visual elements** and **layout/position**, while **text and color improve a lot with finetuning**.
- Metrics kept separate as diagnostics (a model should score well on all) — mirrors AxBench's "don't let one axis mask another."

## Limitations / critiques
- Metrics are **reference-based** (need the target screenshot). Our generation is *open-ended from a text prompt* with **no ground-truth page**, so block-match/CLIP-to-reference don't apply directly. We borrow the *rendering + block-detection + per-dimension* machinery but replace reference-matching with **reference-free** aesthetic/validity metrics (contrast, alignment regularity, palette stats — see A3).
- CLIP similarity is coarse; correlates with layout but not fine aesthetics.

## Relevance to Project 19
Blueprint for the objective half of the oracle and confirmation of the hermetic-render design. Two direct transfers: (1) **render-then-detect-blocks-then-score-per-dimension** architecture; (2) **don't aggregate** raw metrics into one number — report a vector of diagnostics. The *reference-free* adaptation is the key delta: since we have no target image, our "position/alignment" becomes **alignment/spacing regularity** of the generated DOM itself (A3), and "color" becomes **palette statistics / contrast** rather than color-vs-reference.

## Borrow
- Headless render + visual block detection; Jonker–Volgenant only if we ever do reference matching.
- CIEDE2000 for perceptual color differences; Sørensen–Dice for text overlap (useful for content-preservation checks between skill/neutral cells of the *same* prompt).
- CLIP-screenshot similarity as a *within-prompt cross-cell* drift measure (skill vs neutral of same prompt) even without an external reference.
- Human-corroboration of automatic metrics (49/64% lesson).

## Avoid
- Reference-image-dependent metrics as our headline (we have no ground truth); use them only for within-prompt cross-cell comparisons.
- Treating CLIP similarity as an aesthetic-quality score — it's visual-match, not quality.
