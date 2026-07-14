# A3 — Computational Interface Aesthetics (Ngo 2003; Miniukovich & De Angeli 2015; Reinecke et al. 2013; Hasler & Süsstrunk 2003)

DEEP note — these are the sources for the **objective aesthetic metrics we will implement**. Includes the actual formulas and their measured predictive power against human ratings (so we know which are worth computing).

## Ngo, Teo & Byrne 2003 — *Modelling Interface Aesthetics* (Information Sciences 152:25–46, doi:10.1016/S0020-0255(02)00404-8)
Proposes **14 geometric layout measures**, each normalized to [0,1], computed from bounding boxes of layout objects: **balance, equilibrium, symmetry, sequence, cohesion, unity, proportion, simplicity, density, regularity, economy, homogeneity, rhythm, order-and-complexity.** The most implementable and discriminative for our DOM:

- **Balance** $BM = 1 - \frac{|BM_{\text{vertical}}| + |BM_{\text{horizontal}}|}{2}$, where each axis balance is the normalized difference of summed object "weights" (area × distance to axis) on the two sides. Even weight distribution → high balance.
- **Equilibrium** $EM = 1 - \frac{|EM_x| + |EM_y|}{2}$, where $EM_x, EM_y$ are the offsets of the layout's **center of mass** from the frame center, normalized. Centered mass → high equilibrium.
- **Symmetry** $SYM$ — normalized comparison of object measures (x, y, width, height, distance to center) reflected across vertical/horizontal/diagonal axes; axial duplication.
- **Density** — fraction of screen area occupied by objects (optimal near a mid value, not maximal).
- **Regularity / alignment** — degree to which object edges/centers share a small number of alignment points (few distinct x/y alignment lines → high regularity).

Validated to correlate with human aesthetic ratings on constructed layouts. **We implement balance, equilibrium, symmetry, regularity/alignment, density** directly from DOM bounding boxes (Playwright `boundingBox()` per element).

## Miniukovich & De Angeli 2015 — *Computation of Interface Aesthetics* (CHI 2015, doi:10.1145/2702123.2702575)
**Eight screenshot metrics** aimed at *first-impression* aesthetics of real GUIs/webpages/apps:
**visual clutter, color range, number of dominant colors, figure-ground contrast, contour congestion, symmetry, grid quality, white space.**
- **Color range / number of dominant colors** — count of distinct perceptual colors (quantized) / dominant palette size; too many → clutter, too few → dull.
- **Figure–ground contrast** — contrast between foreground elements and background.
- **Contour congestion** — density of nearby edges/contours (crowded borders read as cluttered).
- **Grid quality** — how well elements snap to an underlying grid (regular column/row structure).
- **White space** — proportion and distribution of empty area.
- **Measured power:** the set explains up to **49% of variance in webpage aesthetics** and **32% in iPhone-app aesthetics**, under both immediate (first-glance) and deliberate viewing. → a realistic ceiling for objective metrics; they are *partial* predictors, not oracles (motivating the paired VLM-preference half).

## Reinecke et al. 2013 — *Predicting First Impressions ... Visual Complexity and Colorfulness* (CHI 2013, doi:10.1145/2470654.2481281)
- **548 participants, 450 websites**, ratings after **500 ms** exposure. Computational models of **perceived visual complexity** and **colorfulness** + demographics explain **~half the variance** in appeal.
- **Visual complexity** operationalized from image structure (e.g. quadtree decomposition / space-based decomposition, edge/entropy density, symmetry): more balanced, structured pages read as less "complex" and more appealing up to a point.
- **Colorfulness** operationalized à la Hasler & Süsstrunk (below).
- **Key finding:** appeal is driven by an **inverted-U in visual complexity** and a **moderate colorfulness** — both extremes hurt. Directly usable priors for our metric thresholds.

## Hasler & Süsstrunk 2003 — *Measuring Colorfulness in Natural Images* (SPIE 5007, EPFL infoscience 33994)
The standard colorfulness metric (used by Reinecke; trivial to implement on a screenshot). In opponent space with $rg = R - G$ and $yb = \tfrac{1}{2}(R+G) - B$:
$$\sigma_{rgyb} = \sqrt{\sigma_{rg}^2 + \sigma_{yb}^2}, \quad \mu_{rgyb} = \sqrt{\mu_{rg}^2 + \mu_{yb}^2},$$
$$M = \sigma_{rgyb} + 0.3\,\mu_{rgyb}.$$
Correlates **>90%** with human colorfulness ratings. → our colorfulness metric, and a building block for the **"purple-slop index"** (see below).

## Synthesis for our metric suite (feeds D7)
- **Implement from DOM:** balance, equilibrium, symmetry, alignment/grid regularity, density, white-space (Ngo + Miniukovich grid/white-space).
- **Implement from screenshot:** Hasler colorfulness, number of dominant colors, figure-ground contrast, visual-complexity (edge/quadtree), + WCAG contrast (A7).
- **Purple-slop index (principled proposal):** combine (i) **hue concentration near purple/violet** — fraction of salient pixels with hue in ~[260°,290°] and/or mean chroma-weighted hue proximity to violet; (ii) **gradient-background prevalence** — detected linear-gradient backgrounds on hero/large elements; (iii) **default-font share** — fraction of text using Inter/Roboto/system-ui; (iv) **centered-hero flag** — large centered flex block near top. Report as a vector and a weighted composite; validate that the skill *lowers* it and that it correlates with human "looks AI-generated" ratings.
- **Reality check:** literature ceiling is ~½ variance — objective aesthetics are necessary but insufficient; **this is exactly why the brief mandates the paired preference signal.**

## Borrow
- Ngo balance/equilibrium/symmetry/regularity formulas from DOM boxes; Hasler colorfulness; Miniukovich clutter/grid/white-space; inverted-U complexity + moderate-colorfulness priors.
- Report metrics as a *vector* (Design2Code lesson), not a single aesthetic score.

## Avoid
- Claiming any objective metric *is* aesthetic quality (max R²≈0.49) — always gate aesthetic claims behind the preference signal.
- Over-tuning the purple-slop index without human validation (it must correlate with "looks AI-generated" judgments to be admissible).
