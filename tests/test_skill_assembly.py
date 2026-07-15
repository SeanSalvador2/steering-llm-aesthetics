"""Skill-assembly + build-time audit tests (PLAN §II.1; PREREG §2; ADR-009).

Covers audits (a) token balance, (b) filler banned-topic, (c) PLAN<->skill filler identity,
plus cell prompt assembly and the LOO/AOI padding rule. Audit (d) prompt leakage is in
test_prompts.py.
"""
import pytest

from p19 import skill_assembly as sa


def test_parse_five_components_and_fillers():
    """[[Cn]] tags stripped; five components and five fillers parsed (PLAN §II.1.1/§II.1.3)."""
    comps, fl = sa.components(), sa.fillers()
    assert sorted(comps) == ["C1", "C2", "C3", "C4", "C5"]
    assert sorted(fl) == ["F1", "F2", "F3", "F4", "F5"]
    assert "[[" not in comps["C1"] and "]]" not in comps["C1"]
    assert comps["C1"].startswith("Choose a deliberate palette")
    # reworded C5 (pre-freeze, BPE-friendly) carries both named looks un-hyphenated
    assert "cream with terracotta serif" in comps["C5"]
    assert "near black with acid green" in comps["C5"]


def test_normalize_ws_rejoins_hyphen_wraps():
    """A compound wrapped at its hyphen in source rejoins WITHOUT a space (regression: the
    original C5 wrapped `near-black-with-acid-\\ngreen`, which naively normalized to `acid- green`
    and corrupted the assembled prompt + token counts)."""
    assert sa._normalize_ws("near-black-with-acid-\ngreen looks") == "near-black-with-acid-green looks"
    assert sa._normalize_ws("plain\nwrap") == "plain wrap"


def test_c5_semantic_constraints_all_present():
    """Every C5 semantic constraint survived the pre-freeze reword (orchestrator decision, ADR-009).

    Constraint checklist: six slop tells, generic template palettes, both named generic looks,
    the escape clause, and the cut-purposeless-decoration rule.
    """
    c5 = sa.components()["C5"]
    for phrase in [
        "purple or indigo gradients",
        "Inter and Roboto typefaces",
        "fully centered hero layouts built around one big headline and stat",
        "three identical icon cards in a row",
        "uniform rounded corners on everything",
        "scattered or excessive animation",
        "generic template palettes",
        "cream with terracotta serif",
        "near black with acid green",
        "unless the brief calls for them",
        "Cut any decoration that serves no purpose",
    ]:
        assert phrase in c5, f"C5 lost constraint: {phrase}"


def test_token_balance_estimate_passes():
    """(a) ADR-009 ±15% balance PASSES under the word x 1.33 estimate (PLAN §II.1.2 frozen table)."""
    audit = sa.audit_token_balance(force_estimate=True)
    assert audit["method"] == "estimate"
    assert audit["pass"], f"estimate out-of-band: {audit['out_of_band']}"


def test_token_balance_exact_in_band():
    """(a) EXACT Qwen tokenizer balance PASSES: all five components inside ±15% of the mean.

    Regression lesson (kept for the record): the ORIGINAL C5 measured 104 exact tokens (~28% over
    the mean) because BPE fragments semicolon lists and long hyphen chains
    (`cream-and-terracotta-serif` = 7 tokens) that the word x 1.33 estimate masked. The
    orchestrator sanctioned a pre-freeze reword (PREREG freeze conditions include "the skill text
    is final"); every semantic constraint was preserved (see
    test_c5_semantic_constraints_all_present). Expected exact counts: C1..C5 = 75/73/75/80/88,
    m = 78.2, band [66.5, 89.9]. If the tokenizer cannot be downloaded, this runs on Colab.
    """
    tok = sa._try_qwen_tokenizer()
    if tok is None:
        pytest.skip("Qwen tokenizer unavailable in this env; exact-count check runs on Colab "
                    "(PLAN §II.1.2). The estimate-path balance test still guards the design.")
    audit = sa.audit_token_balance()  # exact
    assert audit["method"] == "qwen"
    assert audit["pass"], f"exact balance out-of-band: {audit['out_of_band']}"
    assert audit["out_of_band"] == {}
    # pin the frozen counts so silent text drift is caught
    assert audit["counts"] == {"C1": 75, "C2": 73, "C3": 75, "C4": 80, "C5": 88}, audit["counts"]


def test_component_identity_plan_vs_skill():
    """(c') PLAN §II.1.1 component blocks are identical (whitespace-normalized) to canonical §1.

    Extends the filler identity audit to the five COMPONENT blocks — added with the C5 reword so
    the plan and the frozen IV file can never silently diverge.
    """
    res = sa.audit_component_identity()
    assert res["n_plan"] == 5
    assert res["pass"], f"component mismatches: {res['mismatch']}"


def test_filler_component_length_match():
    """Each RAW Filler-i is within ±15% of its matched Ci (PLAN §II.1.3 length-matching).

    The C5 reword also restored the F5<->C5 match (old C5=104 gave ratio 0.72; new C5=88 gives
    0.852). Strict equalization (tests below) then tightens the match to ±2 exact tokens.
    """
    res = sa.audit_filler_component_match()
    assert res["pass"], {k: v for k, v in res["pairs"].items() if not v["in_band"]}
    if res["method"] == "qwen":
        assert res["pairs"]["C5"]["filler"] == 75 and res["pairs"]["C5"]["component"] == 88


# ---------------------------------------------------------------- strict equalization (must-fix)

def _require_tokenizer():
    if sa._try_qwen_tokenizer() is None:
        pytest.skip("Qwen tokenizer unavailable; strict-equalization checks run on Colab "
                    "(±2-token precision is meaningless on the word-estimate path).")


def test_padding_pool_parsed_and_identical():
    """The frozen padding pool parses (5 topics, 2-3 clauses each) and PLAN §II.1.3 ↔ canonical §3
    are identical (extends the identity audit to the pool)."""
    pool = sa.padding_pool()
    assert sorted(pool) == ["F1", "F2", "F3", "F4", "F5"]
    for topic, clauses in pool.items():
        assert 2 <= len(clauses) <= 3, (topic, clauses)
    res = sa.audit_padding_identity()
    assert res["pass"], res
    assert res["n_clauses"] == 15


def test_padding_pool_clauses_inert():
    """Every pool clause passes the filler banned-topic inertness audit (they enter fillers)."""
    res = sa.audit_filler_banned_topics(include_pool=True, include_equalized=False)
    assert res["pass"], f"banned-topic hits: {res['hits']}"
    assert res["n_texts"] == 5 + 15  # 5 fillers + 15 pool clauses


def test_equalized_fillers_within_two_tokens():
    """(a) After equalization every |tokens(F_i) - tokens(C_i)| <= 2 (exact tokenizer)."""
    _require_tokenizer()
    eq = sa.equalize_fillers()
    assert eq["available"]
    for k, v in eq["fillers"].items():
        assert abs(v["delta"]) <= 2, (k, v["tokens"], v["target"])
    # pin the frozen landing so silent pool/text drift is caught
    landed = {k: v["tokens"] for k, v in eq["fillers"].items()}
    assert landed == {"F1": 75, "F2": 74, "F3": 76, "F4": 81, "F5": 87}, landed


def test_neutral_total_within_ten_of_full():
    """(b) NEUTRAL system-prompt mass within ±10 tokens of FULL (391) after equalization."""
    _require_tokenizer()
    full = sa.count_tokens(sa.build_system_prompt("FULL"))[0]
    neutral = sa.count_tokens(sa.build_system_prompt("NEUTRAL"))[0]
    assert full == 391
    assert abs(neutral - full) <= 10, (neutral, full)


def test_all_cell_masses_within_ten():
    """(c) Every factorial/LOO/AOI/NEUTRAL cell's system-prompt mass within ±10 of FULL
    (constant-mass property, PREREG §2)."""
    _require_tokenizer()
    cm = sa.cell_mass_report(tol=10)
    assert len(cm["masses"]) == 22  # FULL + NEUTRAL + 5 LOO + 5 AOI + 10 F
    assert cm["pass"], cm["deviations"]
    assert cm["max_abs_deviation"] <= 10


def test_equalized_fillers_pass_inertness():
    """(d) The final equalized filler texts still pass the banned-topic inertness audit."""
    _require_tokenizer()
    res = sa.audit_filler_banned_topics(include_pool=True, include_equalized=True)
    assert res["pass"], f"banned-topic hits: {res['hits']}"


def test_pairwise_match_on_equalized_trivial():
    """(e) The pairwise ±15% audit passes trivially on equalized fillers (|F_i - C_i| <= 2)."""
    _require_tokenizer()
    res = sa.audit_filler_component_match(equalized=True)
    assert res["pass"]
    for k, v in res["pairs"].items():
        assert abs(v["filler"] - v["component"]) <= 2, (k, v)


def test_equalize_one_trims_at_sentence_boundary():
    """The trim branch drops trailing sentences only (canonical §3 padding-pool rule)."""
    _require_tokenizer()
    text = ("Keep the first sentence in place. Keep the second sentence in place as well. "
            "This third trailing sentence is the one that should be dropped.")
    target = sa.count_tokens("Keep the first sentence in place. "
                             "Keep the second sentence in place as well.")[0]
    out, actions = sa._equalize_one(text, target, clauses=[])
    assert out.endswith("as well.")            # cut exactly at the sentence boundary
    assert any(a.startswith("trim:") for a in actions)
    assert abs(sa.count_tokens(out)[0] - target) <= 2


def test_equalize_one_raises_when_unreachable():
    """A gap the frozen pool cannot close raises (a frozen-text defect, never silent)."""
    _require_tokenizer()
    with pytest.raises(ValueError):
        sa._equalize_one("Too short.", target=60, clauses=[("Pad-x", "tiny.")])


def test_filler_banned_topics_clean():
    """(b) Render-inertness: zero banned-topic whole-word matches in any filler (PLAN §II.1.3)."""
    res = sa.audit_filler_banned_topics()
    assert res["pass"], f"filler banned-topic hits: {res['hits']}"


def test_filler_identity_plan_vs_skill():
    """(c) PLAN §II.1.3 filler blocks are byte-identical (whitespace-normalized) to canonical §3."""
    res = sa.audit_filler_identity()
    assert res["n_plan"] == 5
    assert res["pass"], f"filler mismatches: {res['mismatch']}"


def test_system_prompt_assembly_full_and_neutral():
    """FULL = all real components; NEUTRAL = all fillers; constant slot order (PLAN §II.1.3)."""
    full = sa.build_system_prompt("FULL")
    neutral = sa.build_system_prompt("NEUTRAL")
    comps, fl = sa.components(), sa.fillers()
    for k in ("C1", "C2", "C3", "C4", "C5"):
        assert comps[k] in full
    for k in ("F1", "F2", "F3", "F4", "F5"):
        assert fl[k] in neutral
    assert full != neutral


def test_loo_and_aoi_padding_rule():
    """LOO-Ci -> Filler-i in slot i; AOI-Ci -> only Ci real, rest fillers (PLAN §II.1.3)."""
    comps, fl = sa.components(), sa.fillers()
    loo3 = sa.build_system_prompt("LOO-C3")
    assert fl["F3"] in loo3 and comps["C3"] not in loo3
    for k in ("C1", "C2", "C4", "C5"):
        assert comps[k] in loo3  # other components remain
    aoi2 = sa.build_system_prompt("AOI-C2")
    assert comps["C2"] in aoi2
    for k in ("F1", "F3", "F4", "F5"):
        assert fl[k] in aoi2
    assert comps["C1"] not in aoi2


def test_control_cells():
    """BEAUTY1 = the nudge; NOSYS = no system message (None, not empty string) (PLAN §II.1.5)."""
    assert sa.build_system_prompt("BEAUTY1") == "Make it beautiful and well-designed."
    assert sa.build_system_prompt("NOSYS") is None


def test_padding_trimming_helpers():
    """pad_to grows toward target; trim_to shrinks at a sentence boundary (PLAN §II.1.2)."""
    short = "One short clause."
    padded = sa.pad_to(short, target_tokens=40, filler_text=sa.fillers()["F1"])
    assert len(padded.split()) > len(short.split())
    long_text = " ".join([f"Sentence number {i} here." for i in range(20)])
    trimmed = sa.trim_to(long_text, target_tokens=20)
    assert len(trimmed.split()) < len(long_text.split())
    assert trimmed.rstrip().endswith(".")  # cut at a sentence boundary
