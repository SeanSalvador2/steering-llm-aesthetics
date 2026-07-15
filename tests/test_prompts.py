"""Prompt corpus + leakage audit + ChatML tests (PLAN §II.1.5, §II.2; PREREG §3)."""
from p19 import prompts as pr


def test_corpus_size_and_splits():
    """58 prompts; frozen split 40 dev / 8 seen / 10 unseen (PLAN §II.2.1)."""
    assert len(pr.all_prompts()) == 58
    assert len(pr.split_ids("dev")) == 40
    assert len(pr.split_ids("heldout_seen")) == 8
    assert len(pr.split_ids("heldout_unseen")) == 10


def test_unseen_types_absent_from_dev():
    """Settings (ST) and admin-table (AT) are entirely absent from dev (OOD test; PLAN §II.2)."""
    dev_types = {p["type"] for p in pr.dev_prompts()}
    assert "settings" not in dev_types and "admin-table" not in dev_types


def test_leakage_audit_clean():
    """(d) Zero banned-word whole-word matches over the 58 briefs (PLAN §II.2 / PREREG §3)."""
    res = pr.audit_prompt_leakage()
    assert res["n_prompts"] == 58
    assert res["pass"], f"banned-word hits: {res['hits']}"


def test_whole_word_matching_is_boundary_safe():
    """Whole-word regex matches 'clean' but not 'cleanser'; hyphenated bans match as units."""
    assert pr._whole_word_hits("a clean layout", ["clean"]) == ["clean"]
    assert pr._whole_word_hits("a cleanser bottle", ["clean"]) == []
    assert pr._whole_word_hits("cutting-edge tools", ["cutting-edge"]) == ["cutting-edge"]


def test_output_constraint_in_user_turn_and_nosys():
    """Output constraint sits in the USER turn; NOSYS omits the system message (PLAN §II.1.4/§II.1.5)."""
    msgs_full = pr.build_messages("FULL", "L01")
    assert msgs_full[0]["role"] == "system"
    assert msgs_full[-1]["role"] == "user"
    assert "single self-contained HTML file" in msgs_full[-1]["content"]
    msgs_nosys = pr.build_messages("NOSYS", "L01")
    assert all(m["role"] != "system" for m in msgs_nosys)  # no system message at all
    assert "single self-contained HTML file" in msgs_nosys[-1]["content"]


def test_chatml_render_fallback():
    """ChatML render emits Qwen2 markers with an assistant generation prompt (01_qwen_model_facts)."""
    s = pr.render_chatml(pr.build_messages("FULL", "L01"))
    assert "<|im_start|>system" in s and "<|im_start|>user" in s
    assert s.rstrip().endswith("<|im_start|>assistant")
