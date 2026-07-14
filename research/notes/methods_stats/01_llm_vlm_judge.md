# C1 — LLM/VLM-as-Judge Reliability (Zheng et al. 2023; UI-specific VLM judging)

**Citations.**
- Zheng, Chiang, Sheng, Zhuang, Wu, et al. *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* NeurIPS 2023. arXiv:2306.05685.
- Thakur, Choudhary, Ramayapally, Vaidyanathan, Hupkes. *Judging the Judges.* arXiv:2406.12624.
- Jeon et al. *G-FOCUS / WiserUI-Bench* (pairwise UI judging, position-bias fix). arXiv:2505.05026.
- ArtifactsBench (A1 cluster) — checklist MLLM-judge, 94.4% vs WebDev Arena.

**TL;DR.** Strong LLM judges match human preference at **~80%+ agreement** (≈ human–human agreement) but carry **position, verbosity, and self-enhancement biases**. Pairwise is more reliable than absolute scoring; biases are mitigable (order-swapping, rubrics, references). For UIs specifically, **rubric/checklist-anchored VLM judges reach ~90% human agreement** and position-bias-controlled pairwise UI judging exists. This grounds our ADR-005 judge protocol.

## Method & findings, in depth (Zheng)

**Biases quantified.**
- **Position bias:** judges favor the first- (or a specific-) position answer. Mitigation: present **both orders**; count a win only if consistent across orders (else tie). GPT-4 is more consistent than weaker judges but not immune.
- **Verbosity bias:** longer answers preferred even when not better (directly relevant — a skill may increase output length; our length-matched neutral + BT style control address this).
- **Self-enhancement bias:** a judge slightly prefers outputs from its own model family — so **the judge should differ from the subject model** (ours does: subject = Qwen2.5-Coder; judge = a strong API VLM).
- **Limited reasoning/math grading** — less relevant for aesthetics.

**Agreement numbers.** GPT-4 vs human **>80%** agreement on MT-Bench/Arena, ≈ the human–human rate. **Pairwise** comparison is more robust than single-answer **absolute** scoring (Likert), which suffers scale-usage drift — argues for our **pairwise** protocol.

**Judging the Judges (Thakur).** Re-establishes that **percent agreement is misleading — use Cohen's κ** (chance-corrected): judges with high % agreement can assign very different scores. Llama-3-70B and GPT-4-Turbo align well with humans; leniency and instruction-length biases exist. → we must report **chance-corrected** agreement (C2), not raw %.

## VLM-as-judge for images/UI
- **ArtifactsBench:** checklist-guided MLLM judge, **94.4%** ranking consistency w/ WebDev Arena, **>90%** pairwise agreement w/ experts — rubric anchoring is the key to reliability.
- **WiserUI-Bench / G-FOCUS:** pairwise UI-persuasiveness judging with an inference-time strategy that **reduces position bias** and improves accuracy — a UI-specific, position-bias-aware pairwise protocol we can reuse.
- General caution: VLM judges also show modality-specific biases (e.g. preferring more colorful/denser images) — our **objective metrics cross-check** guards against a judge that just likes color.

## Relevance to Project 19
Defines the preference half of the oracle: **pairwise screenshot comparison, both orders, rubric-anchored, judge ≠ subject family, chance-corrected agreement gate + power gate.** ArtifactsBench proves a rubric MLLM judge can be trusted at ~90% human agreement; WiserUI-Bench gives the position-bias-controlled pairwise recipe. Verbosity/length bias is exactly why ADR-003's length-matched control and C3's BT style-control matter (a skill that yields longer/denser pages must not "win" on length alone).

## Borrow
- **Pairwise, both orders, tie if inconsistent**; anchored rubric with explicit design dimensions; judge from a different family than Qwen.
- **Checklist-guided** scoring (ArtifactsBench) for reliability; validate judge on a **human-labeled subset** and report **chance-corrected** agreement (Krippendorff α / Gwet AC1).
- Cross-check judge verdicts against objective metrics to detect judge idiosyncrasies (e.g. colorfulness bias).

## Avoid
- **Absolute Likert** scoring as the headline (scale drift) — use pairwise + Bradley-Terry.
- **Percent agreement** as the reliability statistic (use κ/α/AC1).
- A judge in the **same family** as the subject (self-enhancement) — since subject is Qwen2.5-Coder, avoid a Qwen-VL-only judge as primary; if used, use as secondary and check.
- Ignoring verbosity/length bias — pair with length control + BT style adjustment.
