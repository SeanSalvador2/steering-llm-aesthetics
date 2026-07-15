"""Prompt corpus + leakage audit + ChatML assembly (PLAN §II.1.5, §II.2; §VI.1 `src/prompts`).

- Corpus loading and frozen split accessors (dev / held-out seen / held-out unseen).
- Leakage audit (PLAN §II.2): zero case-insensitive whole-word `banned_words` matches over
  the USER-turn briefs only (output constraint + system texts excluded, per the scope rule).
- ChatML message assembly: system = {skill|fillers|beauty|absent}, user = brief + output
  constraint. NOSYS omits the system message entirely (not an empty string).
"""
from __future__ import annotations

import re

from .config import prompts_config, prompts_by_id, cells_by_id
from .skill_assembly import build_system_prompt, output_constraint


# --------------------------------------------------------------------------- corpus + splits

def all_prompts() -> list[dict]:
    return prompts_config()["prompts"]


def banned_words() -> list[str]:
    return prompts_config()["banned_words"]


def split_ids(split: str) -> list[str]:
    """Frozen prompt ids for a split ∈ {dev, heldout_seen, heldout_unseen} (PLAN §II.2.1)."""
    return list(prompts_config()["split_freeze"][split])


def dev_prompts() -> list[dict]:
    ids = set(split_ids("dev"))
    return [p for p in all_prompts() if p["id"] in ids]


def heldout_prompts(include_seen: bool = True, include_unseen: bool = True) -> list[dict]:
    ids: set[str] = set()
    if include_seen:
        ids |= set(split_ids("heldout_seen"))
    if include_unseen:
        ids |= set(split_ids("heldout_unseen"))
    return [p for p in all_prompts() if p["id"] in ids]


def prompt_text(prompt_id: str) -> str:
    return prompts_by_id()[prompt_id]["text"]


# --------------------------------------------------------------------------- leakage audit

def _whole_word_hits(text: str, terms: list[str]) -> list[str]:
    """Case-insensitive whole-word matches of any term in text (PLAN §II.2 regex \\b...\\b).

    Uses (?<!\\w)/(?!\\w) so hyphenated banned words like 'professional-looking' and
    'cutting-edge' match as single units.
    """
    hits = []
    for t in terms:
        pat = r"(?<!\w)" + re.escape(t) + r"(?!\w)"
        if re.search(pat, text, re.IGNORECASE):
            hits.append(t)
    return hits


def audit_prompt_leakage() -> dict:
    """(d) Zero banned-word whole-word matches over the 58 briefs (PLAN §II.2 / PREREG §3).

    Scope = user-turn brief text only. Also asserts each brief names a concrete domain and
    >= 3 functional sections (heuristic: >= 3 comma/semicolon-separated clauses after the
    first clause), per PLAN §II.2.1's audit procedure.
    """
    terms = banned_words()
    hits: list[tuple[str, str]] = []
    thin: list[str] = []
    for p in all_prompts():
        for w in _whole_word_hits(p["text"], terms):
            hits.append((p["id"], w))
        # functional-section heuristic: clauses after the first ';'
        tail = p["text"].split(";", 1)
        sections = re.split(r"[;,]", tail[1])[0:] if len(tail) > 1 else []
        n_sections = len([s for s in sections if s.strip()])
        if n_sections < 3:
            thin.append(p["id"])
    return {
        "hits": hits,
        "thin_briefs": thin,
        "pass": len(hits) == 0,
        "n_prompts": len(all_prompts()),
    }


# --------------------------------------------------------------------------- ChatML assembly

def user_message(prompt_id: str) -> str:
    """User turn = brief + constant output constraint (PLAN §II.1.4/§II.1.5)."""
    return f"{prompt_text(prompt_id)}\n\n{output_constraint()}"


def build_messages(cell_id: str, prompt_id: str) -> list[dict]:
    """ChatML message list for (cell, prompt).

    NOSYS omits the system message entirely (PLAN §II.1.5). The output constraint is always
    in the user turn so hermeticity holds even with no system prompt.
    """
    _ = cells_by_id()[cell_id]  # validates cell_id
    msgs: list[dict] = []
    sys = build_system_prompt(cell_id)
    if sys is not None:
        msgs.append({"role": "system", "content": sys})
    msgs.append({"role": "user", "content": user_message(prompt_id)})
    return msgs


def render_chatml(messages: list[dict]) -> str:
    """Render messages with the Qwen2 ChatML template (fallback when the tokenizer is absent).

    Prefers `tokenizer.apply_chat_template`; otherwise emits the documented Qwen2 ChatML string
    (01_qwen_model_facts) so downstream code has a deterministic prompt string in the CPU env.
    """
    from .skill_assembly import _try_qwen_tokenizer

    tok = _try_qwen_tokenizer()
    if tok is not None:  # pragma: no cover - only on Colab
        return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    parts = []
    for m in messages:
        parts.append(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n")
    parts.append("<|im_start|>assistant\n")
    return "".join(parts)
