# Prompt-/instruction-component ablation methodology (survey cluster)

Precedents for ablating parts of a prompt/instruction and measuring behavioral deltas — the methodological shape of Stage 1.

## Direct precedents
- **CAA & persona vectors (B2, B9):** treat a system-prompt/instruction as inducing a measurable behavioral shift, and compare *with vs without* the instruction — the atomic ablation unit. Persona vectors additionally compare **length/format-matched** contrastive system prompts, the same confound control as our length-matched neutral (ADR-003).
- **Chatbot Arena style control (C3, Chiang et al. 2024):** the canonical example of **regressing out a confound** (response length, #markdown-headers, #lists) so the remaining coefficient reflects "substance." Our ablation is the experimental analogue: hold prompt *length/imperativeness* fixed (neutral control) so the estimated component effects reflect *design content*, not prompt mass.
- **Persona-prompt studies (e.g. Luz de Araujo & Roth 2024, arXiv:2407.02099):** assign 162 personas + **control personas (30 paraphrases of "a helpful assistant")** to separate persona effect from prompt-sensitivity — precedent for our "make it beautiful" one-liner and neutral controls as reference cells.
- **UICoder / DesignRepair:** show design-guidance/guideline injection changes measurable UI-quality metrics — evidence that instruction content moves objective signals (so component effects should be detectable).

## Design-of-experiments framing (see also methods_stats)
- Component ablation = a **factorial experiment** with factors {C1 color, C2 layout, C3 type, C4 patterns, C5 negatives}, each present/absent.
- **Leave-one-out (full − Cᵢ)** estimates **necessity**; **add-one-in (∅ + Cᵢ)** estimates **sufficiency**; a **fractional-factorial block** estimates **interactions** without the full 2⁵.
- Response = objective metric vector + BT preference utility (two-signal oracle); analysis = mixed-effects over prompt×seed with multiple-comparison control (methods_stats).

## Key methodological cautions
- **Confound = prompt length/format.** Adding a component both adds *content* and *tokens*; without the length-matched neutral, a "component helps" result could be "more instruction tokens help." ADR-003 neutralizes this. (The Arena style-control result is the proof-of-concept that such confounds are real and removable.)
- **Order/position effects in prompts:** where a component sits in the system prompt can matter; randomize/counterbalance component order across cells or fix a canonical order and note it.
- **Interaction, not just main effects:** components may be sub/super-additive (e.g. negative constraints only help if a palette is also specified). The fractional-factorial block is there to catch two-way interactions (resolution V keeps main effects + 2FIs clean).
- **Seeds:** generation is stochastic; each cell needs ≥3 seeds (headline 5) and distributional analysis — a single sample per cell is anecdote (brief's trap list).

## Net for Project 19
No prior work ablates a *design* skill's components with an objective+preference oracle — the methodology is assembled from (a) with/without-instruction contrasts (CAA/persona), (b) confound-regression (Arena style control), (c) control-condition design (persona-prompt studies), and (d) classical fractional-factorial DOE. This is a defensible, novel synthesis.

## Borrow
- With/without + **length-matched-neutral** + **one-liner** + **empty** as the four reference cells.
- LOO (necessity) + AOI (sufficiency) + fractional-factorial 2^(5-1) res V (interactions).
- Fixed canonical component order (documented) or counterbalanced; ≥3 seeds/cell.

## Avoid
- Comparing skill vs empty prompt as the *only* contrast — confounds content with prompt mass.
- Full 2⁵×prompts×seeds naively (explodes) — use the fractional block (ADR-004 / D8).
- Single-seed cells — mandate distributions.
