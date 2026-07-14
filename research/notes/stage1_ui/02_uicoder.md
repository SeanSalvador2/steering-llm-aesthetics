# A2 — UICoder: Finetuning LLMs to Generate UI Code through Automated Feedback (Wu et al. 2024)

**Citation.** Wu, Schoop, Leung, Barik, Bigham, Nichols (Apple). *UICoder.* arXiv:2406.07739 (2024).

**TL;DR.** Improves UI-code generation without human labels by a **self-training loop** driven by **automated feedback**: a compiler/renderer (does it build & render?) and a **multimodal model** scoring visual relevance (CLIP-style). Generate → filter/score/de-duplicate → finetune. Establishes that *automatable* signals (compiles, renders, visual-relevance score) are strong enough to drive UI quality — precedent for our objective oracle and for treating **render-success** as a first-class metric.

## Method, in depth

**Loop.** Start from a base LLM; (1) self-generate a large synthetic set of UI-code prompts+outputs; (2) **automated filtering**: compile/render each output — discard non-compiling; (3) **automated scoring**: a multimodal model (CLIP text–image relevance between the prompt and the rendered screenshot) scores visual relevance; (4) aggressive de-duplication; (5) finetune on the refined higher-quality subset; iterate. Applied to several open LLMs (targets SwiftUI in the paper's setting).

**Signals.**
- **Compiler/renderer** = hard gate (binary: does it build/render). Directly analogous to our **render-success / hermetic-render** metric.
- **CLIP visual relevance** = soft quality/relevance score (prompt ↔ screenshot). Analogous to a learned auxiliary metric (cf. UIClip A4).

## Key results & numbers
- Iterated finetuning yields models that **beat all downloadable open baselines** and approach larger proprietary models on automated metrics **and human preference**.
- Confirms automated feedback (compile + multimodal relevance) is sufficient to raise UI quality without human annotation.

## Limitations / critiques
- CLIP relevance measures *prompt-image match*, not *aesthetic quality* — a page can be relevant yet ugly. Needs an explicit quality signal (UIClip, or our aesthetic metrics).
- Targets a specific framework (SwiftUI); we target single-file HTML, but the loop/signals transfer.

## Relevance to Project 19
Two lessons: (1) **render-success as a gating metric** is validated and load-bearing — a non-rendering page is a null regardless of aesthetics (matches our oracle's render-success requirement). (2) A **multimodal relevance score** is a cheap auxiliary metric we can compute (CLIP between prompt and screenshot) to catch off-task generations, separate from aesthetic quality. UICoder also shows the *default* open-LLM UI output is weak until pushed — consistent with the "AI slop default" our skill is supposed to move.

## Borrow
- Compile/render gate as a hard, deterministic first metric; report render-success rate per cell.
- CLIP prompt↔screenshot relevance as an auxiliary "on-task" check (distinct from aesthetics).
- De-duplication discipline for any generated corpus.

## Avoid
- Using CLIP relevance as the aesthetic-quality signal (it isn't) — pair with UIClip/aesthetic metrics + the VLM preference judge.
- Assuming compile==good; render-success is necessary, not sufficient.
