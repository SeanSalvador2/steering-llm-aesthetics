"""Pairwise VLM judge: both-orders adjudication + mock dry-run (PLAN §III.8, Appendix C; PREREG §5).

The prompt template is VERBATIM from PLAN Appendix C. Each pair is judged in both presentation
orders (A,B) and (B,A); the winner counts only if consistent across orders, else -> tie
(position-bias control). Providers:

  - MockJudge     deterministic, bias-configurable; used for the CPU dry-run.
  - GeminiJudge   Gemini 2.5 Flash primary  (import-guarded; NO calls in the CPU env).
  - OpenAIJudge   GPT-4o audit               (import-guarded; NO calls in the CPU env).

Output JSON schema (validated): {"winner","confidence","per_criterion","rationale"} (PLAN §III.8).
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

# ---- verbatim template (PLAN Appendix C) ----
JUDGE_SYSTEM = (
    "You are a senior product designer evaluating two rendered web user interfaces, A and B, that "
    "were built for the SAME brief. Judge which is the better-designed interface FOR THAT BRIEF. "
    "Base your judgment on deliberate, brief-appropriate design choices — not on which page is "
    "merely longer, more colorful, or more filled-in. A page is not better for having more elements "
    "or brighter colors; it is better for coherent color, clear layout and hierarchy, considered "
    "typography, quality component patterns, restraint (absence of generic \"AI-slop\" tells such as "
    "purple gradients, Inter/Roboto, centered hero-with-a-big-number, three identical icon cards, "
    "uniform rounded corners, excessive animation), and fit to the brief. Return ONLY valid JSON in "
    "the specified schema. Do not add prose outside the JSON."
)

JUDGE_USER_TEMPLATE = (
    "BRIEF: \"{brief_text}\"\n\n"
    "You are shown two screenshots: image A (first) and image B (second), both rendered at "
    "1440x900. Evaluate each on: color/palette coherence; layout & visual hierarchy; typography; "
    "component/pattern quality; restraint (absence of AI-slop tells); overall fit to the brief.\n\n"
    "Return JSON exactly:\n"
    "{{\"winner\": \"A\" | \"B\" | \"tie\",\n"
    " \"confidence\": 1-5,\n"
    " \"per_criterion\": {{\"color\":\"A|B|tie\",\"layout\":\"A|B|tie\",\"typography\":\"A|B|tie\","
    "\"components\":\"A|B|tie\",\"restraint\":\"A|B|tie\",\"fit\":\"A|B|tie\"}},\n"
    " \"rationale\": \"<=40 words\"}}"
)

CRITERIA = ["color", "layout", "typography", "components", "restraint", "fit"]


@dataclass
class PairInput:
    brief_text: str
    screenshotA: str
    screenshotB: str
    cellA: str
    cellB: str
    prompt_id: str
    seedA: int = 0
    seedB: int = 0
    edge: str = ""


@dataclass
class Judgment:
    edge: str
    cellA: str
    cellB: str
    prompt_id: str
    seedA: int
    seedB: int
    winner: str            # consistency-resolved true-label winner: A|B|tie
    confidence: float
    per_criterion: dict
    rationale: str
    consistent: bool
    raw_ab_winner: str
    raw_ba_winner: str
    judge_model: str
    ts: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))


def validate_verdict(d: Any) -> bool:
    """Schema check for a single-order raw verdict (PLAN §III.8)."""
    if not isinstance(d, dict):
        return False
    if d.get("winner") not in ("A", "B", "tie"):
        return False
    c = d.get("confidence")
    if not isinstance(c, (int, float)) or not (1 <= c <= 5):
        return False
    pc = d.get("per_criterion")
    if not isinstance(pc, dict) or any(pc.get(k) not in ("A", "B", "tie") for k in CRITERIA):
        return False
    if not isinstance(d.get("rationale"), str):
        return False
    return True


def _flip(label: str) -> str:
    return {"A": "B", "B": "A", "tie": "tie"}[label]


class Judge:
    """Base judge: subclasses implement `_call_once`. Handles both-orders adjudication."""

    name = "base"

    def _call_once(self, brief: str, imgA: str, imgB: str) -> dict:  # pragma: no cover - abstract
        raise NotImplementedError

    def judge_pair(self, pair: PairInput) -> Judgment:
        """Judge in both orders; winner counts only if consistent, else tie (PLAN §III.8)."""
        v_ab = self._call_once(pair.brief_text, pair.screenshotA, pair.screenshotB)
        v_ba = self._call_once(pair.brief_text, pair.screenshotB, pair.screenshotA)
        if not (validate_verdict(v_ab) and validate_verdict(v_ba)):
            raise ValueError("judge returned an invalid verdict schema")
        # map both to true labels (A = pair.cellA's page)
        true_ab = v_ab["winner"]                 # order was (A,B)
        true_ba = _flip(v_ba["winner"])          # order was (B,A) -> flip
        consistent = true_ab == true_ba
        winner = true_ab if consistent else "tie"
        # per-criterion consistency-resolved
        per = {}
        for k in CRITERIA:
            a = v_ab["per_criterion"][k]
            b = _flip(v_ba["per_criterion"][k])
            per[k] = a if a == b else "tie"
        conf = 0.5 * (v_ab["confidence"] + v_ba["confidence"])
        return Judgment(
            edge=pair.edge, cellA=pair.cellA, cellB=pair.cellB, prompt_id=pair.prompt_id,
            seedA=pair.seedA, seedB=pair.seedB, winner=winner, confidence=conf,
            per_criterion=per, rationale=v_ab.get("rationale", "")[:200],
            consistent=consistent, raw_ab_winner=v_ab["winner"], raw_ba_winner=v_ba["winner"],
            judge_model=self.name,
        )

    def judge_batch(self, pairs: list[PairInput], max_retries: int = 5,
                    backoff_base: float = 2.0) -> list[Judgment]:
        """Batch with exponential backoff on transient errors (PLAN §III.8)."""
        out = []
        for pair in pairs:
            for attempt in range(max_retries):
                try:
                    out.append(self.judge_pair(pair))
                    break
                except ValueError:
                    raise  # schema errors are not retried
                except Exception:  # pragma: no cover - transient API errors (Colab)
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(backoff_base ** attempt)
        return out


class MockJudge(Judge):
    """Deterministic mock judge for the CPU dry-run.

    Verdict from a latent quality map + a configurable position bias + tie margin. No network.
    `position_bias` favors the FIRST-shown page (exercises the both-orders -> tie logic); a
    high bias on near-equal pairs produces order-inconsistency that resolves to tie.
    """

    name = "mock"

    def __init__(self, quality: dict[str, float] | None = None, position_bias: float = 0.0,
                 tie_margin: float = 0.15, noise: float = 0.0):
        self.quality = quality or {}
        self.position_bias = position_bias
        self.tie_margin = tie_margin
        self.noise = noise

    def _score(self, cell_tag: str, first: bool, salt: str) -> float:
        base = self.quality.get(cell_tag, 0.0)
        bias = self.position_bias if first else 0.0
        if self.noise:
            h = int(hashlib.sha256((cell_tag + salt).encode()).hexdigest(), 16)
            base += ((h % 1000) / 1000.0 - 0.5) * 2 * self.noise
        return base + bias

    def _call_once(self, brief: str, imgA: str, imgB: str) -> dict:
        # imgA/imgB here carry the cell tag (path stem) so the mock is deterministic without pixels
        salt = brief[:8]
        sA = self._score(imgA, first=True, salt=salt)
        sB = self._score(imgB, first=False, salt=salt)
        diff = sA - sB
        if abs(diff) < self.tie_margin:
            winner, conf = "tie", 2
        elif diff > 0:
            winner, conf = "A", min(5, 2 + int(abs(diff) * 3))
        else:
            winner, conf = "B", min(5, 2 + int(abs(diff) * 3))
        per = {k: winner for k in CRITERIA}
        return {"winner": winner, "confidence": conf, "per_criterion": per,
                "rationale": f"mock verdict diff={diff:.2f}"}

    def judge_pair(self, pair: PairInput) -> Judgment:
        # feed cell tags as the "images" so the deterministic mock keys on cells, not pixels
        p = PairInput(pair.brief_text, pair.cellA, pair.cellB, pair.cellA, pair.cellB,
                      pair.prompt_id, pair.seedA, pair.seedB, pair.edge)
        return super().judge_pair(p)


class GeminiJudge(Judge):  # pragma: no cover - API, Colab only
    """Gemini 2.5 Flash primary judge (import-guarded; NO calls in the CPU env)."""

    name = "gemini-2.5-flash"

    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None):
        try:
            from google import genai  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "GeminiJudge requires `google-genai` (extra 'judge'); runs on Colab only."
            ) from e
        self.model = model
        self._client = None  # constructed lazily at run time on Colab

    def _call_once(self, brief: str, imgA: str, imgB: str) -> dict:
        raise NotImplementedError("Gemini judging runs on Colab (API phase P3); see RUNBOOK.md.")


class OpenAIJudge(Judge):  # pragma: no cover - API, Colab only
    """GPT-4o audit judge on a 15% subset (import-guarded; NO calls in the CPU env)."""

    name = "gpt-4o"

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None):
        try:
            import openai  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "OpenAIJudge requires `openai` (extra 'judge'); runs on Colab only."
            ) from e
        self.model = model

    def _call_once(self, brief: str, imgA: str, imgB: str) -> dict:
        raise NotImplementedError("GPT-4o audit runs on Colab (API phase P3); see RUNBOOK.md.")
