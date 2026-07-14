# Experimental design & inference for prompt×seed data (survey cluster)

The statistical machinery for Stage 1/2 analysis: mixed-effects for repeated measures, multiple-comparison control, power, fractional factorials, preregistration.

## Mixed-effects models (prompt×seed repeated measures)
- Our data are **crossed/nested**: each objective metric or BT utility is measured per (cell, prompt, seed). Prompts and seeds are **random effects**; cells (components/conditions) are **fixed effects**.
- Model (objective metric $y$): $y_{cps} = \mu + \tau_c + u_p + v_{cp} + \epsilon_{cps}$, with $\tau_c$ fixed cell effects, $u_p\sim N(0,\sigma_p^2)$ random prompt intercepts, optional $v_{cp}$ random cell-by-prompt slopes, residual $\epsilon$. Fit with **statsmodels `MixedLM`** (supports random intercepts & slopes, REML/ML; groups=prompt). For binary metrics (render-success) use a GLMM (binomial) — statsmodels `BinomialBayesMixedGLM` or via `bambi`/`pymer4` if needed.
- Rationale: respects that seeds within a prompt are correlated; a naive per-generation t-test overstates n and inflates false positives (pseudoreplication — the brief's "statistical, not anecdotal" mandate).

## Cluster bootstrap
- For statistics without clean parametric SEs (BT strengths, ratios, aesthetic composites): **resample whole prompts with replacement** (the cluster), recompute the statistic, repeat → percentile CIs. Preserves within-prompt correlation. Preferred CI method for the BT effects (C3).

## Multiple-comparison control
- We test many effects (5 LOO + 5 AOI + interactions + several metrics). Control family-wise or false-discovery:
  - **Holm–Bonferroni** (Holm 1979): sequentially rejective, controls FWER, uniformly more powerful than Bonferroni, **no independence assumption** — good for our confirmatory main-effect tests (necessity/sufficiency of each component).
  - **Benjamini–Hochberg** (1995): controls FDR at level $q$; more powerful, appropriate for the **exploratory** metric-by-metric and interaction scans.
- **Policy:** Holm for the confirmatory component-effect family (headline claims); BH for exploratory secondary metrics; pre-register which is which.

## Power analysis for paired preference tests
- Preference deltas are **paired** (same prompt, skill vs neutral). Use the **McNemar / paired sign test** framework: with discordant-pair probability, required n scales with effect size. For a paired-proportion shift the normal approx gives
$$n \approx \frac{\big(z_{1-\alpha/2}\sqrt{p_d} + z_{1-\beta}\sqrt{p_d - \delta^2/p_d}\big)^2}{\delta^2},$$
where $p_d$ = P(discordant pair), $\delta$ = P(skill wins) − P(neutral wins). Rule of thumb: detecting a **60/40** win-split at 80% power, α=.05 needs on the order of ~**200 informative pairs**; **65/35** needs ~**80**; smaller effects need more. This sizes prompts×pairs per cell and the ~2–4k total judgment budget (D6/D8).
- For BT utilities, power via **simulation**: assume plausible $\beta$ gaps + noise, simulate pairwise data at candidate n, estimate detection rate.

## Fractional factorial designs (the ablation block)
- **2^(5-1) resolution V**, generator **E = ABCD** (defining relation I = ABCDE): **16 runs** instead of 32.
- **Aliasing:** main effects aliased only with 4-factor interactions; **all two-factor interactions aliased only with three-factor interactions** ⇒ **main effects and all 2FIs are cleanly estimable** if 3FI+ are negligible (a standard, defensible assumption for 5 design components). This is exactly ADR-004's "resolution-V half fraction."
- Each of the 16 runs × prompts × seeds; add the 4 control cells outside the factorial. (Montgomery 2017, Ch. 8; PSU STAT 503 L8.)

## Preregistration in ML
- Freeze **PREREGISTRATION.md** before any GPU run: hypotheses, the exact cell table + fractional design, seeds/cell, primary vs secondary metrics, the reliability gate (α/AC1 thresholds), the multiple-comparison policy (Holm vs BH), the power target, and null-decision rules ("effect = null unless it moves an objective metric or a reliability-and-power-gated preference delta"). Mirrors growing ML norms for confirmatory analysis; prevents garden-of-forking-paths given the many metrics/cells.

## Net for Project 19
- **MixedLM** on objective metrics (random prompt & seed), **cluster-bootstrap** BT utilities, **Holm** for confirmatory component claims + **BH** for exploratory scans, **paired-preference power** sizing the judgment budget, **2^(5-1) res V** for the interaction block, all frozen in a **preregistration**.

## Borrow / Avoid
- **Borrow:** MixedLM crossed random effects; cluster bootstrap over prompts; Holm(confirmatory)+BH(exploratory); McNemar power formula for pairs; 2^(5-1) res V (E=ABCD); prereg with frozen null rule.
- **Avoid:** per-generation t-tests (pseudoreplication); a single α-correction lumping confirmatory+exploratory; full 2⁵ (wasteful); post-hoc metric selection (forking paths) — hence preregistration.
