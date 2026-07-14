# Skill Exemplars — Sources, Provenance & License

Collected public frontend-design guidance texts that instantiate "the design skill" we study. Verbatim reproduction only where license clearly allows; otherwise faithful structured capture + short quotes + link. **For our own experiments we use `canonical_skill_v0.md` (original text we authored, grounded in these sources), not a wholesale copy.**

| # | Exemplar | Source URL | Provenance | License | Reproduction here |
|---|---|---|---|---|---|
| 01 | Anthropic `frontend-design` SKILL.md | github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md | Anthropic official Agent Skills repo | Repo **example skills = Apache-2.0** (document skills docx/pdf/pptx/xlsx are source-available-only; frontend-design is an example skill). **Verify per-folder LICENSE before verbatim redistribution.** | Faithful **structured breakdown + short quotes** (full verbatim not captured; see note) |
| 02 | Anthropic `web-artifacts-builder` SKILL.md | github.com/anthropics/skills/blob/main/skills/web-artifacts-builder/SKILL.md | Anthropic official Agent Skills repo | Same repo; frontmatter says "license: Complete terms in LICENSE.txt" | Design-relevant portion captured near-verbatim (short) |
| 03 | Anthropic blog: *Improving Frontend Design Through Skills* | claude.com/blog/improving-frontend-design-through-skills | Anthropic blog | © Anthropic (blog) — link only | Summary only (host blocked to fetcher) |
| 04 | "Purple slop" discourse (community) | prg.sh/…Purple-Gradient-Website; techbytes.app; paddo.dev; developersdigest.tech "16 patterns" | Independent blogs (2025–26) | © respective authors — link only | Paraphrased tells only |
| — | Our canonical skill | `canonical_skill_v0.md` (this dir) | **Authored for this project** | Ours (project license) | Full text; used in experiments |

## Notes on capture fidelity
- The Anthropic **frontend-design** SKILL.md could not be pulled fully verbatim through the available fetch path (the summarizing fetcher enforces a short-quote limit; the GitHub MCP is scoped to the project repo only). What is captured in `01_anthropic_frontend_design.md` is a **faithful section-by-section breakdown with short representative quotes**, sufficient to (a) document the 5-component structure and (b) ground our canonical adaptation. Before any verbatim redistribution, re-pull the file and confirm the per-folder Apache-2.0 LICENSE.
- Adoption signal: the official frontend-design plugin reports **277k+ installs** — evidence the effect is widely credited (and unstudied), the project's motivation.

## Licensing stance for the project
- We **adapt** (not copy) the guidance into `canonical_skill_v0.md`, cite Anthropic as the inspiration/provenance, and keep our text original and clearly component-labeled (C1–C5) so it is directly ablatable. This avoids any redistribution ambiguity and gives us a clean, controllable independent variable.
