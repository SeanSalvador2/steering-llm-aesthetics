# Exemplar 02 — Anthropic `web-artifacts-builder` SKILL.md (design guidance)

- **URL:** https://github.com/anthropics/skills/blob/main/skills/web-artifacts-builder/SKILL.md
- **License:** Anthropic Agent Skills repo; frontmatter `license: Complete terms in LICENSE.txt`.
- **Purpose:** tooling to build elaborate multi-component claude.ai HTML artifacts (React + TypeScript + Vite + Parcel + Tailwind + shadcn/ui), bundled into a single HTML file.

## The one explicit aesthetics instruction (captured near-verbatim)
> **"Design & Style Guidelines — VERY IMPORTANT: To avoid what is often referred to as 'AI slop', avoid using excessive centered layouts, purple gradients, uniform rounded corners, and Inter font."**

## Why it matters for us
- Confirms the **negative-constraint core** (C5) is stable across Anthropic's skills and is stated as the single most important design directive — a strong prior that **negative constraints carry outsized weight**, a hypothesis Stage-1 LOO/AOI will test directly.
- Names four concrete, **machine-checkable** tells: centered layouts (large centered flex near top), purple gradients (CSS linear-gradient with violet hues), uniform rounded corners (single border-radius everywhere), Inter font (font-family). Each becomes an objective metric / component of the purple-slop index (stage1_ui/03, 07).
- The rest of the skill is build tooling (init/bundle scripts, shadcn components) — not aesthetic guidance; the aesthetic payload is the single line above, which is notable: a **very short** negative-constraint block is credited with avoiding "AI slop," motivating the "does 500 tokens beat a one-liner?" control cell (ADR-003).
