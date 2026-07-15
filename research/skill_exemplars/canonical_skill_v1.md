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
Avoid AI slop defaults: purple or indigo gradients; Inter and Roboto typefaces; fully centered
hero layouts built around one big headline and stat; three identical icon cards in a row; uniform
rounded corners on everything; and scattered or excessive animation. Never default to generic
template palettes or cream with terracotta serif and near black with acid green looks, unless the
brief calls for them. Cut any decoration that serves no purpose.

---

## 2. Token balance (ADR-009 ±15% rule)

Target: each component ≈ **85 tokens** (nominal). Counts are measured **exactly** with the
`Qwen/Qwen2.5-Coder-7B-Instruct` tokenizer (`tokenizer.encode`, no special tokens) on the
whitespace-normalized component text; the word-count × ~1.33 estimate (whitespace-split words,
em-dashes counted) remains the documented fallback for environments without the tokenizer. The
±15 % band is taken around the observed mean **m** of the five exact counts:
**m = 78.2 → band [66.5, 89.9]**.

| Component | words | est. tokens (×1.33) | exact Qwen tokens | within ±15 % of m? |
|---|---|---|---|---|
| C1 color | 63 | ~84 | 75 | yes |
| C2 layout | 64 | ~85 | 73 | yes |
| C3 typography | 62 | ~82 | 75 | yes |
| C4 patterns | 65 | ~86 | 80 | yes |
| C5 negatives | 71 | ~94 | 88 | yes |

**Revision note (pre-freeze, sanctioned).** C5 was reworded before the `prereg-v1` tag: the
original phrasing measured **104 exact tokens** (~28 % over the mean) because BPE fragments
semicolon lists and long hyphen chains (`cream-and-terracotta-serif` alone = 7 tokens) that the
×1.33 estimate masked. Every semantic constraint is preserved — all six slop tells (purple/indigo
gradients; Inter/Roboto; the fully centered hero built around one big headline and stat; three
identical icon cards in a row; uniform rounded corners on everything; scattered/excessive
animation), generic template palettes, both named generic looks (cream + terracotta serif;
near black + acid green), the "unless the brief calls for them" escape, and the
cut-decoration-that-serves-no-purpose rule. Hyphen chains were broken into BPE-friendly phrasing.
The reword also brings Filler-5 (75 exact tokens) back within ±15 % of its matched component.

**Build-time enforcement.** `src/skill_assembly` measures each component with the actual
`Qwen/Qwen2.5-Coder-7B-Instruct` tokenizer and **asserts** `0.85·m ≤ len(Cᵢ) ≤ 1.15·m` where
`m` = mean component length. If a component is short it is padded with a trailing neutral clause
drawn from the matched filler block (below); if long, a trailing clause is trimmed at a sentence
boundary. The assertion is a hard test; the frozen counts are recorded in the manifest. Full skill
= **391 exact tokens** (nominal target ≈ 5 × 85 ≈ 425).

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

**Filler token counts** (exact Qwen tokenizer, words × ≈1.33 as fallback; enforced at build time
against the matched component's token count): raw F1 67 t (C1 75); F2 65 t (C2 73); F3 69 t
(C3 75); F4 71 t (C4 80); F5 75 t (C5 88) — every raw filler within ±15 % of its matched component;
all equally imperative in mood. Build-time equalization (below) then makes the match exact:
equalized F1 75, F2 74, F3 76, F4 81, F5 87 — each within ±2 tokens of its component.

**Padding pool (frozen; build-time equalization).** `src/skill_assembly.equalize_fillers` makes the
length match exact at build time: each Filler-i is deterministically padded (appending pool clauses
in the fixed order below, skipping any that would overshoot) or trimmed (at sentence boundaries
only) until |tokens(Fᵢ) − tokens(Cᵢ)| ≤ 2 under the exact Qwen2.5-Coder tokenizer; per-filler final
counts are recorded in the manifest. Pool clauses are render-inert, imperative, on-topic for their
filler, and pass the same banned-topic audit as the fillers.

**Pad-1a** (↔F1): Apply the same wrapping style to every long tag so no line stands out.

**Pad-1b** (↔F1): Break attribute lists at a consistent width.

**Pad-1c** (↔F1): Keep tag casing uniform throughout.

**Pad-2a** (↔F2): Keep spacing between rule blocks even so the stylesheet reads in a steady rhythm.

**Pad-2b** (↔F2): Order declarations the same way in every rule.

**Pad-2c** (↔F2): Keep rule blocks tidy and short.

**Pad-3a** (↔F3): Prefer plain descriptive words over clever coinages when a name must be introduced.

**Pad-3b** (↔F3): Keep names short, plain, and easy to scan.

**Pad-3c** (↔F3): Keep the vocabulary of names small.

**Pad-4a** (↔F4): Group constants near the top of the script so their values are easy to locate.

**Pad-4b** (↔F4): Keep the script's functions in one predictable order.

**Pad-4c** (↔F4): Prefer flat logic over nesting.

**Pad-5a** (↔F5): Delete stale comments rather than letting them drift out of date.

**Pad-5b** (↔F5): Keep comment punctuation simple and consistent.

**Pad-5c** (↔F5): Prefer one clear comment over three vague ones.

**LOO padding rule.** In a leave-one-out cell (full skill minus Cᵢ), Cᵢ is replaced **in its
original slot** by Filler-i, so the cell has the same token count and the same positional layout as
FULL. In an add-one-in cell (Cᵢ alone), the other four slots hold their matched fillers. Therefore
**every factorial cell (all 16 res-V runs and all 5 LOO cells) carries constant prompt mass —
FULL = 391 exact Qwen2.5-Coder tokens, every cell within ±10 of it after filler equalization
(≈425 nominal on the estimate path)** — and constant slot structure; only *content* varies. The
**NEUTRAL** control is exactly Filler-1‖Filler-2‖Filler-3‖Filler-4‖Filler-5 — i.e. the all-filler
`(−,−,−,−,−)` corner.

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
| **FULL** | C1‖C2‖C3‖C4‖C5 (391 tok exact) | task + output constraint | the intact skill |
| **NEUTRAL** | Filler-1‖…‖Filler-5 (391 ± 10 tok after equalization) | task + output constraint | length-matched, design-irrelevant; isolates *design content* from *prompt mass*; the Stage-2 contrast side |
| **BEAUTY1** | "Make it beautiful and well-designed." (≈8 tok) | task + output constraint | does a 5-word nudge match 391 tokens? (RQ4) |
| **NOSYS** | *(no system message)* | task + output constraint | bare baseline; the Stage-2 "steer with no prompt" base |

---

## 6. Optional robustness variant (off the primary path)

**MIXED** (not run in the confirmatory design): a "realistic" skill in which negatives are
interleaved into C1–C4 as real published skills write them (the v0 style). Used only to check that
the content-orthogonal split does not itself change the headline skill effect (a single extra cell,
BH-exploratory). Documented here so the frozen primary design stays clean per ADR-009.
