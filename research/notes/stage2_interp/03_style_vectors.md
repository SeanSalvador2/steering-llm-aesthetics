# B3 — Style Vectors for Steering Generative LLMs (Konen et al. 2024)

**Citation.** Konen, Jentzsch, Diallo, Schütt, Bensch, El Baff, Opitz, Hecking. *Style Vectors for Steering Generative Large Language Models.* Findings of EACL 2024. arXiv:2402.01618.

**TL;DR.** The closest published work to our setting: steer *style* (sentiment, emotion, formality) by adding a "style vector" to hidden-layer activations during generation. Two ways to build the vector — (a) **activation-based** (mean of recorded activations for style-specific texts, optionally minus a neutral mean) and (b) **training-based** (learn a direction from a style classifier). Activation-based, computed with no training, works nearly as well — a direct precedent for our diff-in-means "clean-design" vector.

## Method, in depth

**Activation-based style vectors.** Feed a corpus of texts labelled with a style $s$ through the model; record hidden activations $h_l$ at layer $l$ (averaged over tokens of each input). The style vector is the mean activation for style-$s$ texts, contrasted against a neutral/opposite mean:
$$v_l^{(s)} = \overline{h_l}^{\,(s)} - \overline{h_l}^{\,(\text{neutral})}.$$
This is diff-in-means at the *sentence-representation* level (mean over response tokens), not a single aligned token — important because generation is free-form (like ours).

**Training-based style vectors.** Train a linear classifier on activations to separate styles; use its weight vector (or the direction between class means induced by it) as $v_l^{(s)}$. Comparable or slightly better than activation-based but requires labelled training; the paper's headline is that the *simpler activation-based* vector is already effective.

**Injection.** At generation, add the (scaled) style vector to the activations of hidden layers:
$$h_l' = h_l + \lambda\, v_l^{(s)},$$
with a tunable steering factor $\lambda$. They sweep $\lambda$ over a continuous range and show the style intensity is **parameterisable and roughly monotone** — small $\lambda$ nudges, large $\lambda$ dominates (eventually harming fluency). Injection at intermediate layers; they analyse *which* layers give the best style-vs-content trade-off (mid layers preferred).

**Model / data.** Demonstrated on Alpaca-style LLaMA (7B-class) instruction models; styles from sentiment (positive/negative) and emotion datasets (e.g. joy/anger/sadness/fear). Evaluation measures **style strength** (classifier or lexicon score on the output) against **content preservation / fluency** (semantic similarity, perplexity), tracing the Pareto trade-off as $\lambda$ varies.

## Key results & numbers
- Activation-based style vectors steer sentiment/emotion effectively with **no training**, competitive with training-based vectors.
- Steering is nuanced and continuous in $\lambda$; distinguishes from prompt engineering (finer, dial-able control).
- Mid-layer injection gives the best style/content balance; extreme $\lambda$ degrades fluency (the recurring strength trade-off).

## Limitations / critiques
- Styles are coarse (sentiment/emotion); "clean visual design in generated HTML" is higher-dimensional and downstream of a long code generation, so the signal may be weaker/more distributed.
- Content-vs-style trade-off is exactly our risk: steering "design" may trade against code correctness/render success — must be measured (our objective oracle does this).
- Evaluated on short text; long-form code generation stresses the "add at all positions" assumption differently.

## Relevance to Project 19
This is our nearest neighbour and de-risks the plan: a *style* direction extracted by **mean-of-activations difference** and added with a scalar $\lambda$ demonstrably steers generative output. It validates (a) using the **mean over response tokens** as the extraction statistic for free-form generation (vs CAA's single answer-letter position), and (b) framing the whole exercise as a **style-vs-content trade-off** to be characterised via a $\lambda$ sweep and a Pareto plot (design quality vs render-success/code-validity) — which is precisely our Stage-2 failure-surface map.

## Borrow
- Mean-over-response-tokens diff-in-means as the primary extraction statistic for long generations (D3).
- Continuous $\lambda$ sweep with an explicit style-vs-content Pareto curve; pick the operating point on the dev set.
- Report the layer that best trades design gain against code/coherence loss.

## Avoid
- Don't push $\lambda$ into the fluency-collapse regime for headline numbers; report the whole curve including where design "wins" only by breaking the page.
- Don't assume a text-style result transfers 1:1 to code aesthetics — verify with the objective oracle, since "content" here includes machine-checkable correctness.
