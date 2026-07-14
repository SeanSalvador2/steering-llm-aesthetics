# Canonical Design Skill v0 (project-authored, ~500 tokens, component-labeled)

Original text authored for this project, grounded in the Anthropic frontend-design / web-artifacts-builder skills and community discourse (see SOURCES.md). Structured as five ~90–110-token components so each is independently ablatable (ADR-004 / D8). This is a **draft** to be finalized in PLAN.md/PREREGISTRATION.md; component boundaries are marked with `[[Cn]]` (tags removed before use — they only document the ablation split).

---

[[C1 — Color / palette]]
Choose a deliberate palette of 4–6 specific colors: one dominant color, one or two supporting tones, and one sharp accent, all named as exact hex values and used consistently. Prefer atmospheric, layered backgrounds over flat fills. Do not use purple/indigo gradients, and do not fall back to generic template palettes. Ensure text/background pairs meet WCAG AA contrast.

[[C2 — Layout / spacing / hierarchy]]
Lead with the most characteristic element of the subject, not a centered hero with a big number and gradient. Establish a clear spatial hierarchy using a consistent spacing scale; align elements to a small number of shared edges. Favor intentional, sometimes asymmetric composition over an even grid of identical cards. Give the page room to breathe with purposeful white space.

[[C3 — Typography]]
Pair a characterful display typeface (used sparingly for headings) with a clean, readable body typeface, and a utility face for small labels/data. Do not default to Inter or Roboto. Set a clear modular type scale with a few deliberate sizes and weights; let type carry the page's personality rather than neutrally delivering text.

[[C4 — Component patterns / examples]]
Use one well-chosen signature element (an unexpected section, a distinctive card treatment, a considered navigation) rather than uniform stock components. Add at most one orchestrated motion moment (a page-load reveal or a hover state); avoid scattered animation. Vary corner radii and shadows intentionally instead of applying one uniform rounded style everywhere.

[[C5 — Negative constraints]]
Avoid the "AI slop" defaults: purple gradients, Inter/Roboto fonts, fully centered layouts, uniform rounded corners on everything, three identical icon-cards in a row, and excessive animation. Avoid generic default aesthetics (e.g. cream + terracotta serif, or near-black + acid-green) unless the brief calls for them. Cut any decoration that does not serve the page's purpose.

---

## Output constraint (constant across ALL cells, not ablated)
"Return a single self-contained HTML file with all CSS and JS inline and no external network requests (no external fonts, scripts, images, or stylesheets)." (Enforces hermetic render — ADR-006.)

## Control cells (ADR-003) — reference texts
- **Length-matched neutral:** ~500 tokens of equally imperative, design-irrelevant instructions (code hygiene: semantic HTML tags, comment structure, indentation, variable naming, small functions, avoid inline event handlers) with the **same output constraint** — isolates *design content* from *prompt mass*.
- **"Make it beautiful" one-liner:** the output constraint + "Make it beautiful and well-designed." — tests whether 5 words match ~500 tokens.
- **No-system-prompt:** the output constraint only.

## Notes for finalization
- Keep each component's token count within ±15% of the others so LOO/AOI removes comparable prompt mass (else re-pad to length-match on removal).
- Fix a canonical component order (C1→C5) and document it; optionally counterbalance order in a robustness cell.
- The neutral control must match the **full skill's** length; when running LOO (skill minus Cᵢ), pad the removed component with neutral filler of equal length so every cell has equal prompt mass (defense against the verbosity confound at the design level, complementing BT style-control at the analysis level — C3).
