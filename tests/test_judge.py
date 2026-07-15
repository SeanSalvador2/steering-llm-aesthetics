"""Judge tests: both-orders/tie logic + schema validation + mock dry-run (PLAN §III.8, App C)."""
import pytest

from p19 import judge


def test_verbatim_template_markers():
    """The template is the verbatim PLAN Appendix C text (role + JSON schema)."""
    assert "senior product designer" in judge.JUDGE_SYSTEM
    assert "AI-slop" in judge.JUDGE_SYSTEM
    assert '"winner"' in judge.JUDGE_USER_TEMPLATE and "per_criterion" in judge.JUDGE_USER_TEMPLATE


def test_validate_verdict_schema():
    """Verdict schema validation accepts valid and rejects malformed (PLAN §III.8)."""
    good = {"winner": "A", "confidence": 4,
            "per_criterion": {k: "A" for k in judge.CRITERIA}, "rationale": "ok"}
    assert judge.validate_verdict(good)
    assert not judge.validate_verdict({"winner": "C", "confidence": 4,
                                       "per_criterion": {}, "rationale": ""})
    assert not judge.validate_verdict({"winner": "A", "confidence": 9,
                                       "per_criterion": {k: "A" for k in judge.CRITERIA},
                                       "rationale": "x"})  # confidence out of range


def test_consistent_winner():
    """A clear winner is consistent across both orders (PLAN §III.8)."""
    mj = judge.MockJudge(quality={"FULL": 1.0, "NEUTRAL": 0.0}, position_bias=0.0)
    j = mj.judge_pair(judge.PairInput("brief", "a", "b", "FULL", "NEUTRAL", "p1", edge="FULL-NEUTRAL"))
    assert j.winner == "A" and j.consistent


def test_position_bias_resolves_to_tie():
    """Order-inconsistent verdicts (near-equal + position bias) resolve to tie (PLAN §III.8)."""
    mj = judge.MockJudge(quality={"X": 0.50, "Y": 0.52}, position_bias=0.3, tie_margin=0.15)
    j = mj.judge_pair(judge.PairInput("brief", "a", "b", "X", "Y", "p1", edge="X-Y"))
    assert j.winner == "tie" and not j.consistent


def test_batch_dry_run():
    """Mock batch dry-run over several pairs returns one judgment per pair (PLAN §III.8)."""
    mj = judge.MockJudge(quality={"FULL": 1.0, "NEUTRAL": 0.0, "LOO-C5": 0.6})
    pairs = [
        judge.PairInput("b", "a", "b", "FULL", "NEUTRAL", "p1", edge="FULL-NEUTRAL"),
        judge.PairInput("b", "a", "b", "FULL", "LOO-C5", "p1", edge="FULL-LOO-C5"),
    ]
    out = mj.judge_batch(pairs)
    assert len(out) == 2 and all(o.judge_model == "mock" for o in out)


def test_api_judges_import_guarded():
    """Gemini/OpenAI judges raise clearly if their client libs are absent (Colab-only)."""
    for cls in (judge.GeminiJudge, judge.OpenAIJudge):
        try:
            cls()
        except ImportError:
            pass  # expected in the CPU env without the 'judge' extra
        except NotImplementedError:
            pass  # client present but no calls made here
