# Exemplar 01 — Anthropic `frontend-design` SKILL.md (faithful structured capture)

- **URL:** https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md
- **License:** Apache-2.0 (repo example skills); verify per-folder LICENSE before verbatim reuse.
- **Frontmatter:** `name: frontend-design`; `description:` guidance for distinctive, intentional visual design (aesthetic direction, typography, avoiding templated defaults); `license: Complete terms in LICENSE.txt`.
- **Capture note:** structured breakdown + short quotes (<20 words). Not full verbatim — see SOURCES.md.

## Sections (in order) and their guidance

1. **Ground it in the subject.** "Name one concrete subject, its audience, and the page's single job" before designing; draw from the subject's materials/vernacular. Anti: designing without knowing what for.

2. **Design principles.**
   - *Hero/opening:* lead with "the most characteristic thing" in the subject's world; avoid the default "big number with small label, supporting stats, and gradient accent."
   - *Typography:* pair display + body faces deliberately; each project should use different families; clear type scale with intentional weights/widths/spacing; "type should carry personality."
   - *Structure:* "structural devices — numbering, eyebrows, dividers, labels — should encode something true about the content, not decorate it." Numbered sequences only if order matters.
   - *Motion:* strategic animation (page-load, scroll reveals, hover); "one orchestrated moment beats scattered effects"; "extra animation contributes to the feeling that the design is AI-generated."
   - *Complexity:* match execution to vision (maximalist → elaborate; minimal → precise spacing).
   - *Content:* real copy, not templated tone.

3. **Three default aesthetics to avoid** (appear "regardless of subject"; only if brief asks):
   1. Warm cream background `#F4F1EA` + high-contrast serif + terracotta accent.
   2. Near-black background + single acid-green/vermilion accent.
   3. Broadsheet layout with hairlines, zero border-radius, dense columns.

4. **Process: Brainstorm → Explore → Plan → Critique → Build → Critique again.**
   - *Plan (token system):* "4–6 named hex colors"; "2+ typeface roles" (characterful display used sparingly + complementary body + utility face for captions/data); one-sentence layout concepts with ASCII wireframes; one signature element.
   - *Critique before coding:* if any part matches generic defaults for similar briefs, revise and explain; only code after confirming uniqueness.
   - *Build:* watch CSS specificity (avoid selectors that cancel each other).
   - *Critique as you build:* screenshots; responsive to mobile; visible keyboard focus; reduced-motion support.

5. **Restraint & self-critique.** "Spend your boldness in one place"; keep surroundings quiet; "cut any decoration that does not serve the brief."

6. **Writing in design.** Words "make it easier to understand, therefore easier to use"; name by what users control ("notifications," not "webhook config"); active voice ("Save changes"); consistent vocabulary across flows; errors/empty states as direction; conversational-and-tuned register.

## Companion negative-constraint line (from web-artifacts-builder, exemplar 02)
"To avoid what is often referred to as 'AI slop', avoid using excessive centered layouts, purple gradients, uniform rounded corners, and Inter font."

## 5-component mapping (for our ablation; see stage1_ui/05)
- **C1 Color/palette** ← "4–6 named hex colors," dominant + accent, atmospheric depth; avoid purple gradients + the 3 default palettes.
- **C2 Layout/spacing/hierarchy** ← hero = most characteristic element; structural devices encode meaning; asymmetric > grid; "spend boldness in one place"; avoid centered-hero default.
- **C3 Typography** ← display+body+utility roles, different families, deliberate scale; avoid Inter/Roboto.
- **C4 Component patterns/examples** ← one orchestrated motion moment; signature element; exemplar snippets; avoid uniform radius.
- **C5 Negative constraints** ← consolidated "avoid" list (purple gradients, Inter, centered layouts, uniform radius, excessive animation, 3 default aesthetics).
