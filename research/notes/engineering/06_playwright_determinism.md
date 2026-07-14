# D-g — Playwright screenshot determinism & rendering hygiene

**Sources.** Playwright docs (test-snapshots, accessibility-testing) + 2026 visual-testing guides. CLAUDE.md: Chromium preinstalled at `/opt/pw-browsers`; render with network disabled.

## Determinism practices (bake into `src/rendering/`)
1. **Fixed viewport.** Set an explicit viewport (e.g. **1280×800 desktop**; add **375×812 mobile** as a second condition). Full-page screenshots: width controls layout, height follows content — pin width. Same width across all cells.
2. **Disable animations.** `page.screenshot({ animations: 'disabled' })` fast-forwards CSS animations/transitions to final state and disables transitions → deterministic regardless of capture timing. Also hide the text caret (`caret: 'hide'`).
3. **Fonts.** Font rendering varies by OS; **await font load** (`document.fonts.ready`) before capture. Because pages are **hermetic single-file (ADR-006, no external fonts)**, only system/generic fallbacks render — so **pin the environment** (Docker/Colab Linux + preinstalled Chromium) and generate all screenshots in the **same** environment; baselines from a different OS won't match (sub-pixel/font differences).
4. **Network disabled.** Route-block/offline so no external fetch occurs (also enforces hermeticity — a page that *needs* network is scored non-hermetic). `context.route('**', r => r.abort())` or offline context.
5. **Wait for stability.** Wait for `networkidle`/no pending JS/`document.fonts.ready` and a fixed settle delay before capture; `toHaveScreenshot()` auto-waits for animation/network/layout stability if used.
6. **Pin versions.** Record Chromium + Playwright versions; regenerate all screenshots together if versions change (cross-version rendering differs).
7. **Device scale factor** fixed (e.g. 1) for consistent pixel dimensions feeding the objective screenshot metrics (colorfulness, contrast, complexity).

## Why this matters for the oracle
- **Objective screenshot metrics** (Hasler colorfulness, contrast, visual complexity, purple-index — A3/A7) and **VLM judgments** both consume the screenshot; nondeterministic rendering would inject noise orthogonal to the design manipulation, inflating variance and biasing cross-cell comparisons.
- **DOM metrics** (balance, alignment, overflow/overlap, contrast per node) read `boundingBox()`/computed styles from the **rendered** DOM (never raw code strings, per CLAUDE.md) — also require a stable render.
- Determinism lets us treat the render as a **fixed function of the HTML**, so all variance is attributable to generation (prompt/seed/steering), which the mixed-effects model assumes.

## CPU-executable now (compute policy)
- All of the above runs **CPU-only on fixture HTML** in this environment (Chromium at `/opt/pw-browsers`): render fixtures, compute the full objective-metric stack, screenshot with animations disabled/network blocked, unit-test geometry metrics — must actually run and pass here (ADR-007) before the GPU phase produces real pages.

## Borrow / Avoid
- **Borrow:** fixed viewport + `animations:'disabled'` + caret hide + `document.fonts.ready` + offline route-block + `networkidle` wait + pinned Chromium/Playwright + fixed DSF; generate all screenshots in one environment.
- **Avoid:** capturing mid-animation; relying on external fonts (breaks hermeticity + determinism); mixing OS/browser versions across a run; reading colors from CSS text instead of the rendered pixels/DOM.
