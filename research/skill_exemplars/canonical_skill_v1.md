# Canonical Design Skill v1 (ADR-009-compliant, content-orthogonal, length-balanced)

**Status: FROZEN candidate for PREREGISTRATION.md.** Supersedes `canonical_skill_v0.md`.
This is the project's independent variable. Implements **ADR-009**: components C1–C4 carry
**only positive/prescriptive** guidance; **all** negative constraints live in **C5**. This makes
the five components *content-orthogonal* — ablating C5 removes *all* negative guidance, and each
Cᵢ effect is attributable to distinct content (no "no purple gradients" hiding inside the color
component). Provenance: adapted (not copied) from the Anthropic `frontend-design` /
`web-artifacts-builder` skills and community "purple-slop" discourse (`anthropic2025frontendskill`;
`skill_exemplars/SOURCES.md`); text is project-authored.

Component boundary tags `[[Cn]]` are documentation only and are **stripped** before the text is
placed in the model's system prompt. Canonical component order is **C1 → C2 → C3 → C4 → C5** and is
fixed (a counterbalanced-order robustness cell is optional, off the primary path).

---

## 1. The five components (prescriptive C1–C4; negatives-only C5)

[[C1 — Color / palette]]
Choose a deliberate palette of four to six specific colors — one dominant hue, one or two
supporting tones, and one sharp accent — each fixed as an exact hex value and reused consistently
throughout. Build depth with atmospheric, layered backgrounds such as subtle tints, soft shading,
or fine texture rather than flat fills, and ensure every text-on-background pairing clears WCAG AA
contrast.

[[C2 — Layout / spacing / hierarchy]]
Open with the most characteristic element of the subject so the page announces what it is at a
glance. Establish a clear visual hierarchy on a consistent spacing scale, aligning elements to a
small set of shared edges so the composition reads as engineered. Favor intentional, sometimes
asymmetric arrangements over uniform grids, and give the layout generous, purposeful white space so
it can breathe.

[[C3 — Typography]]
Pair a characterful display typeface, used sparingly for headings, with a clean, highly readable
body typeface and a compact utility face for small labels and data. Set a clear modular type scale
with a few deliberate sizes and weights, and let the typography carry real personality — expressive
at large sizes, quietly legible at small ones — instead of neutrally delivering text.

[[C4 — Component patterns]]
Design one well-chosen signature element — an unexpected section, a distinctive card treatment, or
a considered navigation — that anchors the page's identity. Add at most one orchestrated motion
moment, such as a single page-load reveal or a refined hover state, and make it feel deliberate.
Vary corner radii, borders, and shadows with intent so that depth and emphasis track the importance
of the content.

[[C5 — Negative constraints (ALL negatives consolidated here per ADR-009)]]
Avoid the AI-slop defaults: purple or indigo gradients; the Inter and Roboto typefaces; fully
centered hero layouts built around one big headline and stat; three identical icon-cards in a row;
uniform rounded corners on everything; and scattered or excessive animation. Do not fall back on
generic template palettes, nor on the overused cream-and-terracotta-serif or near-black-with-acid-
green looks, unless the brief calls for them. Cut any decoration that does not serve the page's
purpose.

---

## 2. Token balance (ADR-009 ±15% rule)

Target: each component ≈ **85 tokens** (Qwen2.5 tokenizer). Estimated component lengths (word count
× ~1.33 tok/word, to be replaced by exact `tokenizer.encode` counts at build time):

| Component | words | est. tokens | within ±15 % of 85 (72–98)? |
|---|---|---|---|
| C1 color | 61 | ~82 | yes |
| C2 layout | 64 | ~85 | yes |
| C3 typography | 60 | ~80 | yes |
| C4 patterns | 63 | ~84 | yes |
| C5 negatives | 66 | ~88 | yes |

**Build-time enforcement.** `src/skill_assembly` measures each component with the actual
`Qwen/Qwen2.5-Coder-7B-Instruct` tokenizer and **asserts** `0.85·m ≤ len(Cᵢ) ≤ 1.15·m` where
`m` = mean component length. If a component is short it is padded with a trailing neutral clause
drawn from the matched filler block (below); if long, a trailing clause is trimmed at a sentence
boundary. The assertion is a hard test; the frozen counts are recorded in the manifest. Full skill
≈ **5 × 85 ≈ 425 tokens** of system-prompt content.

---

## 3. Neutral filler pool (for length-matched controls and LOO/AOI padding)

Five design-**irrelevant** source-hygiene blocks, each **token-length-matched to the component it
replaces** (Filler-i ↔ Cᵢ). Purpose: hold prompt mass and slot position constant across every
factorial cell (ADR-003 confound control at the design level).

**Filler inertness rule (binding).** Fillers must be design-irrelevant AND **render-inert**: a filler
may not mandate anything that changes the rendered DOM tree, the choice of elements or attributes, or
the render outcome — nothing any objective metric could detect (semantic landmarks, `html-has-lang`,
`document-title`, tag closure, and event-handler attributes are all visible to axe-core or the
render-success gate in families V/A, so mandating them would let fillers move the oracle). Allowed
filler topics: source formatting (indentation, line width, blank lines), comment style and placement,
naming conventions for classes/ids/variables, CSS declaration ordering/grouping within rules, and JS
source organization (small single-purpose functions, `const`/`let`, declaration order). This
render-inertness restriction deliberately tightens ADR-003's illustrative "code hygiene" examples
(semantic tags and event-handler style are metric-visible, so they are excluded here).
`src/skill_assembly` runs a build-time **filler audit**, parallel to the prompt leakage audit: assert
zero case-insensitive whole-word matches in any filler of the banned-topic term list — semantic/
structural element mandates (header, nav, main, footer, aside, article, section, landmark, semantic),
document metadata (lang, title, meta), ARIA/accessibility, validation and tag closure (valid,
validate, validation, well-formed, closed, closure, unclosed, lint, linter), event attachment
(addEventListener, onclick, handler, event), and error/exception guarding — hard unit test
(`config/skill.yaml: filler_banned_topics`).

**Filler-1** (↔C1): Write the markup in a consistent source style: use lowercase for tag and
attribute names, quote every attribute value with double quotes, and keep a stable attribute order
within each tag. Break long lines at a consistent indent so no line grows unwieldy, and keep quoting
and casing choices uniform across the whole file so the source reads cleanly.

**Filler-2** (↔C2): Indent the markup consistently with two spaces per level and keep lines to a
reasonable width so the source stays legible. Group related rules together, order the CSS
declarations predictably, and leave a short comment above each major part of the stylesheet
describing what it styles. Avoid trailing whitespace and keep a single blank line between logical
blocks.

**Filler-3** (↔C3): Name classes and identifiers with clear, lowercase, hyphen-separated words that
describe purpose rather than appearance, and keep the naming scheme consistent across the file.
Avoid abbreviations that are not obvious, do not reuse one name for two purposes, and prefer a
short, stable vocabulary of names over inventing a new term for every element on the page.

**Filler-4** (↔C4): Organize any JavaScript into small, single-purpose functions with descriptive
names, each declared before the point where it is used, and keep the logic shallow rather than
deeply nested. Prefer const and let over var, keep variable declarations near their first use, group
related functions together in the script, and leave a brief comment explaining any step whose intent
is not obvious.

**Filler-5** (↔C5): Comment the code where intent is not obvious, but avoid restating what the code
plainly does; a good comment explains why, not what. Keep comments short, place each one directly
above the line or block it describes, and use a consistent comment style throughout. Remove
commented-out fragments and leftover notes to self before finishing, so only purposeful comments
remain in the final file.

**Filler token estimates** (words × ≈1.33; exact counts enforced at build time by padding/trimming to
the matched component's token count): F1 59 w ≈ 78 t (C1 ~82); F2 58 w ≈ 77 t (C2 ~85); F3 57 w ≈
76 t (C3 ~80); F4 61 w ≈ 81 t (C4 ~84); F5 63 w ≈ 84 t (C5 ~88) — all inside the ±15 % band [72, 98]
and within ±15 % of their matched components; all equally imperative in mood.

**LOO padding rule.** In a leave-one-out cell (full skill minus Cᵢ), Cᵢ is replaced **in its
original slot** by Filler-i, so the cell has the same token count and the same positional layout as
FULL. In an add-one-in cell (Cᵢ alone), the other four slots hold their matched fillers. Therefore
**every factorial cell (all 16 res-V runs and all 5 LOO cells) carries constant prompt mass ≈ 425
system tokens** and constant slot structure; only *content* varies. The **NEUTRAL** control is
exactly Filler-1‖Filler-2‖Filler-3‖Filler-4‖Filler-5 — i.e. the all-filler `(−,−,−,−,−)` corner.

---

## 4. Constant output constraint (in the USER message, never ablated)

Appended verbatim to every task prompt in **all** cells, including NOSYS (enforces hermetic render,
ADR-006):

> "Return a single self-contained HTML file: put all CSS in one `<style>` tag and all JavaScript in
> one `<script>` tag, inline, with no external network requests — no external fonts, stylesheets,
> scripts, images, or CDNs. Use only system or generic fonts, and inline SVG or CSS for any
> graphics. Output only the HTML file."

Placing the output constraint in the **user** turn (not the system prompt) keeps it present even in
the NOSYS cell, which has no system message.

---

## 5. The four control cells (ADR-003)

| Cell | System prompt | User prompt | Purpose |
|---|---|---|---|
| **FULL** | C1‖C2‖C3‖C4‖C5 (≈425 tok) | task + output constraint | the intact skill |
| **NEUTRAL** | Filler-1‖…‖Filler-5 (≈425 tok) | task + output constraint | length-matched, design-irrelevant; isolates *design content* from *prompt mass*; the Stage-2 contrast side |
| **BEAUTY1** | "Make it beautiful and well-designed." (≈8 tok) | task + output constraint | does a 5-word nudge match ≈425 tokens? (RQ4) |
| **NOSYS** | *(no system message)* | task + output constraint | bare baseline; the Stage-2 "steer with no prompt" base |

---

## 6. Optional robustness variant (off the primary path)

**MIXED** (not run in the confirmatory design): a "realistic" skill in which negatives are
interleaved into C1–C4 as real published skills write them (the v0 style). Used only to check that
the content-orthogonal split does not itself change the headline skill effect (a single extra cell,
BH-exploratory). Documented here so the frozen primary design stays clean per ADR-009.
