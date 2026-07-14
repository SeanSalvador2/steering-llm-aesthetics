# A5 — The Frontend-Design Skill Phenomenon & the "AI Slop" Default

DEEP note on the object of study itself: what a frontend-design skill actually contains, the documented default-LLM aesthetic it counters, and a **5-component decomposition** grounded in the real Anthropic skill text (feeds D10 and the ablation cells).

## The artifact: Anthropic `frontend-design` skill (github.com/anthropics/skills, `skills/frontend-design/SKILL.md`)
- **License:** repo example-skills (algorithmic-art, brand-guidelines, frontend-design, …) are **Apache-2.0**; document skills (docx/pdf/pptx/xlsx) are source-available-only. Frontend-design is an example skill → Apache-2.0 (verify per-folder LICENSE at run time before verbatim redistribution; safest path is to **adapt**, not copy, into our canonical skill).
- **Adoption:** the official frontend-design plugin reports **277k+ installs** — the effect is widely credited by the community, unstudied academically. This is the "everyone reports it, nobody measured it" gap the project fills.
- **Framing:** approach design "as the design lead at a small studio" giving each brief a visual identity that "could not be mistaken for anyone else's"; make **deliberate, opinionated choices about palette, typography, and layout specific to the brief.**
- **Process it prescribes:** a **two-pass workflow** — (1) brainstorm a *design plan* (compact token system: 4–6 named hex colors; 2+ typeface roles — a characterful display face used sparingly + complementary body + utility face; one-sentence layout concepts with ASCII wireframes; one signature element); (2) **critique the plan against the brief** and revise anything matching generic defaults *before* writing code; then build; then critique again (screenshots, responsiveness, focus states, reduced-motion).
- **Explicit negative constraints (the "avoid" list):** avoid **purple gradients, Inter font, excessive centered layouts, uniform rounded corners, excessive animation**; and three named default aesthetics to avoid unless the brief asks: (a) warm cream `#F4F1EA` + high-contrast serif + terracotta accent; (b) near-black background + single acid-green/vermilion accent; (c) broadsheet layout with hairlines, zero border-radius, dense columns. "Spend your boldness in one place"; "cut any decoration that does not serve the brief."

## Companion: `web-artifacts-builder` skill (same repo)
Single explicit aesthetic line: *"To avoid what is often referred to as 'AI slop', avoid using excessive centered layouts, purple gradients, uniform rounded corners, and Inter font."* Confirms the negative-constraint core is stable across Anthropic's skills.

## The documented default ("purple slop") — community discourse (cite as web sources)
Consistent account across blogs (prg.sh "Why Your AI Keeps Building the Same Purple Gradient Website"; techbytes; paddo.dev; developersdigest "16 patterns"):
- **Tells:** purple/indigo gradients, **Inter/Roboto** fonts, three feature cards with icons in a grid, centered hero with big-number stats, uniform rounded corners, flat backgrounds, predictable grids.
- **Mechanism (their explanation, matches linear-rep view):** models sample the **high-probability center** of web training data (the "median of every Tailwind tutorial 2019–2024"); without direction they regress to safe, universal choices → convergent aesthetic. A skill *shifts the distribution* toward committed, distinctive choices.
- This is precisely a **steerable distributional shift** — motivating both Stage 1 (which instructions move it) and Stage 2 (can we move it by activation steering with no prompt).

## Proposed 5-component decomposition (grounded, sentence-level — for ablation cells & D10)
Map the real skill onto five ablatable components (ADR-004):
1. **C1 Color/Palette** — "define 4–6 named hex colors; dominant color with sharp accents; atmospheric depth over flat fills; avoid purple gradients / the three default palettes."
2. **C2 Layout/Spacing/Hierarchy** — "lead with the most characteristic element (not big-number+gradient); structural devices must encode meaning; asymmetric composition over predictable grids; deliberate spacing; spend boldness in one place; avoid excessive centered layouts."
3. **C3 Typography** — "pair a characterful display face with a complementary body + utility face; different families per project; clear type scale with intentional weights/widths; avoid Inter/Roboto defaults."
4. **C4 Component patterns / examples** — "one orchestrated motion moment (page-load/scroll/hover); a signature unique element; concrete exemplar snippets; uniform-rounded-corners avoidance."
5. **C5 Negative constraints** — the consolidated "avoid" list (purple gradients, Inter, centered hero, uniform radius, excessive animation, the three default aesthetics).

Each component is ~80–120 tokens so the full canonical skill is ~**500 tokens** — matching the project's target. LOO/AOI ablation over {C1…C5} + the four control cells (full-skill, length-matched-neutral, "make it beautiful" one-liner, no-system-prompt) is the Stage-1 design.

## Relevance to Project 19
This note *is* the independent variable. It (a) supplies the canonical skill to adapt (D10), (b) gives the 5 components to ablate, (c) documents the default aesthetic the skill moves (so the "purple-slop index" has a real target), and (d) frames the phenomenon as a distributional shift that could plausibly be reproduced by a single steering direction (Stage-2 hypothesis).

## Borrow
- The five components above as the ablation factors; the four control cells; the ~500-token budget.
- The skill's own **negative constraints** as *direct, checkable objective metrics* (purple-gradient present? Inter used? centered hero? uniform radius?) — the skill tells us exactly what to measure.
- The two-pass "plan then critique against defaults" structure as prior art for why the skill works (commit-before-coding).

## Avoid
- Verbatim wholesale copying of the Anthropic text into our repo without confirming the per-folder Apache-2.0 license; **adapt** into our own `skill.md` and cite provenance.
- Treating "purple slop" as only about color — the tells are multi-component (type, layout, motion), which is why component ablation is the right instrument.
