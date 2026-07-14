# Accessibility, contrast math & machine-checkable violations (survey cluster)

The deterministic, "unfoolable" backbone of the objective oracle. What is machine-checkable, and the exact formulas.

## axe-core (Deque; github.com/dequelabs/axe-core)
- Rules for **WCAG 2.0/2.1/2.2 levels A/AA/AAA** + best-practices; designed for **zero false positives** (reported violations are reliable) and returns **"incomplete"** for items needing human review.
- **Coverage:** automated tools catch roughly **~30–57% of WCAG issues**; axe cited at **~57%** of issues found in a first-time audit — the rest (alt-text quality, focus-order logic, caption accuracy) need humans. So axe gives a **reliable lower bound** on accessibility defects.
- Runs in the page via Playwright (`@axe-core/playwright`); returns violations with rule id, impact (minor→critical), and offending nodes. **We report axe violation counts by impact per rendered page** — deterministic, per-cell.
- Prevalence prior: **low-contrast text appears on 79.1% of WebAIM-Million pages** — contrast is the single most common, most-checkable defect, and a prime axis for the skill to improve.

## WCAG 2.x contrast (the formula we implement)
Relative luminance of an sRGB color: linearize each channel
$$C_{\text{lin}} = \begin{cases} C_{sRGB}/12.92 & C_{sRGB} \le 0.03928\\ \left(\frac{C_{sRGB}+0.055}{1.055}\right)^{2.4} & \text{otherwise}\end{cases}$$
$$L = 0.2126\,R_{\text{lin}} + 0.7152\,G_{\text{lin}} + 0.0722\,B_{\text{lin}}.$$
Contrast ratio between lighter $L_1$ and darker $L_2$:
$$CR = \frac{L_1 + 0.05}{L_2 + 0.05} \in [1, 21].$$
(The +0.05 models ambient glare.) **AA thresholds:** **4.5:1** normal text, **3:1** large text (≥18pt or 14pt bold) and UI components; **AAA:** 7:1 / 4.5:1. → per-page we compute text/background contrast per text node and report **fraction below 4.5:1** and the min/median contrast.

## APCA (WCAG 3 direction)
- **Advanced Perceptual Contrast Algorithm** (Somers 2022) — polarity-aware (which color is text vs background matters), models perceived lightness contrast (Lc score, roughly −108…+106) with font-size/weight thresholds, rather than a single ratio. More perceptually accurate, esp. for dark mode / thin text. **Use as a secondary contrast metric**; WCAG 2.x ratio remains the primary (stable, standardized, axe-aligned).

## Other deterministic DOM/render metrics (assemble into the suite)
- **Render success / hermeticity:** page renders with network disabled and no external fetch (ADR-006) — binary gate.
- **Overflow/overlap counts:** elements exceeding viewport or with intersecting bounding boxes (layout bugs) via `boundingBox()` geometry.
- **Alignment/spacing regularity:** number of distinct x/y edge positions and the entropy of gaps (Ngo regularity, A3).
- **Palette statistics:** dominant-color count, Hasler colorfulness, purple-hue fraction (A3 purple-slop index).
- **Typography-scale consistency:** number of distinct font-sizes / font-families; ratio adherence to a modular scale (few, geometrically-spaced sizes = consistent).

## Net for Project 19
The **deterministic half** of the oracle = {render-success, axe violation counts (esp. contrast), WCAG contrast distribution, overflow/overlap counts, alignment/spacing regularity, palette/colorfulness/purple-index, typography-scale consistency}. All computable from Playwright DOM + screenshot, all reproducible offline, all "unfoolable." These are necessary; the VLM-preference half supplies aesthetic judgment the metrics can't (≤½ variance ceiling, A3).

## Borrow
- axe-core via Playwright for violation counts (report by impact); WCAG 2.x contrast formula above as a first-party metric (don't depend only on axe for contrast — compute it to get the full distribution).
- Overflow/overlap and alignment-regularity from bounding boxes.

## Avoid
- Treating axe pass as "accessible/good" — it covers ~½ of criteria; it's a lower bound.
- Reading raw CSS strings for color/contrast — compute on the **rendered** DOM/screenshot (CLAUDE.md: never raw code strings).
