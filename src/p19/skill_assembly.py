"""Skill assembly + build-time audits (PLAN §II.1, §VI.1 `src/skill_assembly`; ADR-009).

Parses the frozen `canonical_skill_v1.md` into its five prescriptive components (C1..C5)
and five render-inert fillers (F1..F5), builds any cell's system prompt from its sign vector
under the LOO/AOI padding rule, and runs the four build-time audits:

  (a)  token balance ±15%            (PLAN §II.1.2 / canonical §2; ADR-009; exact tokenizer)
  (b)  filler banned-topic audit     (PLAN §II.1.3; render-inertness)
  (c)  filler identity check         (PLAN §II.1.3 ↔ canonical §3)
  (c') component identity check      (PLAN §II.1.1 ↔ canonical §1; added with the C5 reword)
  (c'') filler↔component length match (PLAN §II.1.3 pairing; near-constant LOO/AOI mass)
  (d)  prompt leakage audit          (PLAN §II.2 — delegated to src/prompts, re-exported)

Assembly decision not fully pinned by PLAN: the five slots are joined by a blank line
(`config/skill.yaml: block_separator = "\\n\\n"`) so the system prompt reads as five
paragraphs. The ±15% balance is per-component and separator-independent.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from . import REPO_ROOT
from .config import skill_config, cells_by_id

# --------------------------------------------------------------------------- parsing

_COMPONENT_TAG = re.compile(r"^\[\[C(\d)\b.*?\]\]\s*$", re.MULTILINE)
_FILLER_MARK = re.compile(r"\*\*Filler-(\d)\*\*\s*\(↔C\d\):\s*", re.UNICODE)
_PAD_MARK = re.compile(r"\*\*Pad-(\d)([a-z])\*\*\s*\(↔F\d\):\s*", re.UNICODE)


def _normalize_ws(text: str) -> str:
    """Collapse whitespace to single spaces (canonical text form).

    A hyphenated compound wrapped at its hyphen in the source (e.g.
    ``near-black-with-acid-\\ngreen``) is rejoined WITHOUT a space so the assembled prompt and
    the tokenizer see the intended single compound ``near-black-with-acid-green``. Em-dashes
    (U+2014, always space-surrounded here) are untouched.
    """
    text = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[A-Za-z])", "-", text)  # rejoin hyphenated wraps
    return re.sub(r"\s+", " ", text).strip()


def parse_components(md_text: str) -> dict[str, str]:
    """Extract C1..C5 prescriptive text from the skill markdown (tags stripped).

    A component runs from just after its ``[[Cn ...]]`` tag line to the next tag / ``---`` /
    ``## `` heading. Whitespace is normalized. Returns {"C1": text, ...}.
    """
    matches = list(_COMPONENT_TAG.finditer(md_text))
    comps: dict[str, str] = {}
    for i, m in enumerate(matches):
        n = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        chunk = md_text[start:end]
        # stop at a section rule / heading if one appears before the next tag
        chunk = re.split(r"\n---\s*\n|\n##\s", chunk)[0]
        comps[f"C{n}"] = _normalize_ws(chunk)
    return comps


def parse_fillers(md_text: str) -> dict[str, str]:
    """Extract F1..F5 filler text from markdown of the form ``**Filler-n** (↔Cn): text``.

    Each filler runs to the next filler marker / ``---`` / bold-line / heading. Returns
    {"F1": text, ...} with normalized whitespace.
    """
    marks = list(_FILLER_MARK.finditer(md_text))
    fillers: dict[str, str] = {}
    for i, m in enumerate(marks):
        n = m.group(1)
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(md_text)
        chunk = md_text[start:end]
        # cut at the next section rule, heading, or a following bold marker line
        chunk = re.split(r"\n---\s*\n|\n#{1,6}\s|\n\*\*", chunk)[0]
        fillers[f"F{n}"] = _normalize_ws(chunk)
    return fillers


@lru_cache(maxsize=None)
def _skill_md() -> str:
    path = REPO_ROOT / skill_config()["skill_file"]
    return Path(path).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def components() -> dict[str, str]:
    return parse_components(_skill_md())


@lru_cache(maxsize=None)
def fillers() -> dict[str, str]:
    return parse_fillers(_skill_md())


def parse_padding_pool(md_text: str) -> dict[str, list[tuple[str, str]]]:
    """Extract the frozen padding pool: {"F1": [("Pad-1a", clause), ...], ...} in document order.

    Clauses are the strict-equalization pad source (canonical §3 / PLAN §II.1.3 padding-pool
    subsection). Each clause runs to the next bold marker / rule / heading, normalized like the
    fillers.
    """
    marks = list(_PAD_MARK.finditer(md_text))
    pool: dict[str, list[tuple[str, str]]] = {}
    for i, m in enumerate(marks):
        topic, suffix = m.group(1), m.group(2)
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(md_text)
        chunk = md_text[start:end]
        chunk = re.split(r"\n---\s*\n|\n#{1,6}\s|\n\*\*", chunk)[0]
        pool.setdefault(f"F{topic}", []).append((f"Pad-{topic}{suffix}", _normalize_ws(chunk)))
    return pool


@lru_cache(maxsize=None)
def padding_pool() -> dict[str, list[tuple[str, str]]]:
    return parse_padding_pool(_skill_md())


# --------------------------------------------------------------------------- tokenization

@lru_cache(maxsize=1)
def _try_qwen_tokenizer():
    """Return the Qwen tokenizer if it can be loaded offline/online, else None.

    Tokenizer-only download is permitted (no weights). In this CPU env HF-hub access may be
    blocked; callers fall back to the word x words_per_token estimate and mark the exact-count
    test skipped-with-reason so it runs on Colab.
    """
    try:  # pragma: no cover - network/deps dependent
        from transformers import AutoTokenizer

        name = skill_config()["tokenizer"]
        return AutoTokenizer.from_pretrained(name)
    except Exception:
        return None


def count_tokens(text: str, force_estimate: bool = False) -> tuple[int, str]:
    """(token_count, method) where method ∈ {"qwen", "estimate"}.

    Uses the real Qwen tokenizer when available (and not forced off); otherwise
    words x words_per_token (PLAN §II.1.2). `force_estimate=True` always uses the estimator
    (the tokenizer-independent path PLAN froze its ±15% table on).
    """
    if not force_estimate:
        tok = _try_qwen_tokenizer()
        if tok is not None:
            return len(tok.encode(text, add_special_tokens=False)), "qwen"
    wpt = skill_config()["token_balance"]["words_per_token"]
    return int(round(len(text.split()) * wpt)), "estimate"


# --------------------------------------------------------------------------- audits

def audit_token_balance(force_estimate: bool = False) -> dict:
    """(a) ADR-009 ±15% token balance over C1..C5 (PLAN §II.1.2).

    Checks 0.85*m <= len(Ci) <= 1.15*m for the mean m. Returns per-component counts, the band,
    the tokenizer method, pass flag, and any out-of-band components. Does NOT mutate the frozen
    text (the frozen skill is the preregistered IV; PREREG §2).

    Regression history: the original C5 measured 104 exact tokens (~28% over the mean) because
    BPE fragments semicolon lists and long hyphen chains (`cream-and-terracotta-serif` = 7 tokens)
    that PLAN §II.1.2's word x 1.33 estimate masked. Escalated; the orchestrator sanctioned a
    pre-freeze reword of C5 (PREREG's freeze conditions include "the skill text is final"),
    preserving every semantic constraint. Both paths now pass: exact C1..C5 = 75/73/75/80/88
    (m = 78.2, band [66.5, 89.9]); estimate path in-band as before.
    """
    comps = components()
    tol = skill_config()["token_balance"]["tol"]
    counts: dict[str, int] = {}
    method = "estimate"
    for k in ("C1", "C2", "C3", "C4", "C5"):
        counts[k], method = count_tokens(comps[k], force_estimate=force_estimate)
    m = sum(counts.values()) / len(counts)
    lo, hi = (1 - tol) * m, (1 + tol) * m
    ok = all(lo <= v <= hi for v in counts.values())
    return {
        "counts": counts,
        "mean": m,
        "band": [lo, hi],
        "method": method,
        "pass": ok,
        "out_of_band": {k: v for k, v in counts.items() if not (lo <= v <= hi)},
    }


def audit_filler_banned_topics(include_pool: bool = True, include_equalized: bool = False) -> dict:
    """(b) Render-inertness: zero whole-word banned-topic matches in any filler (PLAN §II.1.3).

    Also scans the frozen PADDING-POOL clauses (they enter fillers at equalization time, so they
    must satisfy the same inertness rule) and, on request, the final equalized filler texts.
    """
    banned = skill_config()["filler_banned_topics"]
    texts: dict[str, str] = dict(fillers())
    if include_pool:
        for topic, clauses in padding_pool().items():
            for cid, clause in clauses:
                texts[cid] = clause
    if include_equalized:
        for k, v in equalized_fillers().items():
            texts[f"{k}-equalized"] = v
    hits: list[tuple[str, str]] = []
    for fk, text in texts.items():
        for term in banned:
            # whole-word, case-insensitive; hyphenated terms (well-formed) matched literally
            pat = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
            if re.search(pat, text, re.IGNORECASE):
                hits.append((fk, term))
    return {"hits": hits, "pass": len(hits) == 0, "n_texts": len(texts)}


def _plan_md() -> str:
    return (REPO_ROOT / skill_config()["plan_file"]).read_text(encoding="utf-8")


def _plan_filler_text() -> dict[str, str]:
    """Parse the filler blocks out of PLAN §II.1.3 (for the identity audit)."""
    return parse_fillers(_plan_md())


# PLAN §II.1.1 formats components as a bold header line followed by a "> " blockquote.
_PLAN_COMPONENT = re.compile(r"\*\*C(\d) — [^\n]*?\*\*[^\n]*\n((?:>[^\n]*\n?)+)")


def parse_plan_components(md_text: str) -> dict[str, str]:
    """Extract C1..C5 text from PLAN §II.1.1's blockquote format, normalized like the canonical."""
    out: dict[str, str] = {}
    for m in _PLAN_COMPONENT.finditer(md_text):
        body = re.sub(r"^>[ \t]?", "", m.group(2), flags=re.MULTILINE)
        out[f"C{m.group(1)}"] = _normalize_ws(body)
    return out


def audit_filler_identity() -> dict:
    """(c) PLAN §II.1.3 ↔ canonical §3 filler-text identity (whitespace-normalized).

    Both sources are parsed with the same normalizer; any content divergence fails.
    """
    canon = fillers()
    plan = _plan_filler_text()
    mism: list[str] = []
    for k in ("F1", "F2", "F3", "F4", "F5"):
        if canon.get(k) != plan.get(k):
            mism.append(k)
    return {"mismatch": mism, "pass": len(mism) == 0, "n_plan": len(plan)}


def audit_component_identity() -> dict:
    """(c') PLAN §II.1.1 ↔ canonical §1 component-text identity (whitespace-normalized).

    Extends the filler identity check to the five COMPONENT blocks, so the skill text can never
    silently diverge between the plan and the frozen IV file (added with the sanctioned pre-freeze
    C5 reword to guarantee the sync).
    """
    canon = components()
    plan = parse_plan_components(_plan_md())
    mism: list[str] = []
    for k in ("C1", "C2", "C3", "C4", "C5"):
        if canon.get(k) != plan.get(k):
            mism.append(k)
    return {"mismatch": mism, "pass": len(mism) == 0, "n_plan": len(plan)}


def audit_filler_component_match(force_estimate: bool = False, equalized: bool = False) -> dict:
    """Filler-i within ±15% of its matched component Ci (PLAN §II.1.3 length-matching).

    The LOO/AOI padding rule swaps Ci <-> Filler-i in the same slot; near-constant prompt mass
    requires each pair to be token-length-matched. Checked pairwise: 0.85*|Ci| <= |Fi| <= 1.15*|Ci|.
    With `equalized=True` the check runs on the strict-equalized fillers (trivially in-band, since
    equalization enforces |Fi - Ci| <= 2).
    """
    comps = components()
    fl = equalized_fillers() if equalized else fillers()
    tol = skill_config()["token_balance"]["tol"]
    pairs: dict[str, dict] = {}
    ok = True
    for i in range(1, 6):
        ci, _ = count_tokens(comps[f"C{i}"], force_estimate=force_estimate)
        fi, method = count_tokens(fl[f"F{i}"], force_estimate=force_estimate)
        in_band = (1 - tol) * ci <= fi <= (1 + tol) * ci
        pairs[f"C{i}"] = {"component": ci, "filler": fi, "ratio": fi / ci, "in_band": in_band}
        ok = ok and in_band
    return {"pairs": pairs, "pass": ok,
            "method": method}


def audit_padding_identity() -> dict:
    """PLAN §II.1.3 ↔ canonical §3 padding-pool identity (whitespace-normalized, order-sensitive)."""
    canon = padding_pool()
    plan = parse_padding_pool(_plan_md())
    mism: list[str] = []
    for k in ("F1", "F2", "F3", "F4", "F5"):
        if canon.get(k) != plan.get(k):
            mism.append(k)
    n_clauses = sum(len(v) for v in canon.values())
    return {"mismatch": mism, "pass": len(mism) == 0 and len(plan) == 5,
            "n_topics": len(canon), "n_clauses": n_clauses}


# --------------------------------------------------------------------------- strict equalization

_EQUALIZE_TOL = 2  # |tokens(F_i) - tokens(C_i)| <= 2 (orchestrator directive; canonical §3)


def _equalize_one(text: str, target: int, clauses: list[tuple[str, str]],
                  tol: int = _EQUALIZE_TOL) -> tuple[str, list[str]]:
    """Deterministically pad/trim one filler to target±tol exact tokens.

    Trim: drop trailing sentences (sentence boundary only) while above target+tol.
    Pad: append pool clauses IN THE FIXED DOCUMENT ORDER, skipping any clause that would overshoot
    target+tol, until count >= target-tol. No randomness. Returns (text, action log).
    Raises ValueError if the frozen pool cannot reach the window (a frozen-text defect).
    """
    actions: list[str] = []
    count = count_tokens(text)[0]
    # trim at sentence boundaries only
    while count > target + tol:
        sentences = _SENTENCE_END.split(text)
        if len(sentences) <= 1:
            raise ValueError(f"cannot trim below {count} toward {target}±{tol}: single sentence")
        text = " ".join(sentences[:-1]).strip()
        actions.append(f"trim:-1sentence({sentences[-1][:30]}...)")
        count = count_tokens(text)[0]
    # pad from the frozen pool, fixed order, skip overshooters
    for clause_id, clause in clauses:
        if count >= target - tol:
            break
        cand = f"{text} {clause}"
        cand_count = count_tokens(cand)[0]
        if cand_count <= target + tol:
            text, count = cand, cand_count
            actions.append(f"pad:{clause_id}")
    if not (target - tol <= count <= target + tol):
        raise ValueError(
            f"equalization failed: {count} not in [{target - tol}, {target + tol}]; "
            f"the frozen padding pool needs a clause sized to close the gap")
    return text, actions


@lru_cache(maxsize=1)
def equalize_fillers() -> dict:
    """Strict build-time filler equalization: |tokens(F_i) - tokens(C_i)| <= 2 (canonical §3).

    Requires the exact Qwen tokenizer (±2-token precision is meaningless on the word-estimate
    path); returns {"available": False} without it — callers then fall back to the raw frozen
    fillers, and the equalization tests skip-with-reason so they run on Colab. Deterministic:
    fixed pool order, no randomness. The report (per-filler final counts + actions) is what the
    manifest records.
    """
    if _try_qwen_tokenizer() is None:  # pragma: no cover - exercised on tokenizer-less envs
        return {"available": False, "fillers": {}, "reason": "qwen tokenizer unavailable"}
    comps, fl, pool = components(), fillers(), padding_pool()
    out: dict[str, dict] = {}
    for i in range(1, 6):
        target = count_tokens(comps[f"C{i}"])[0]
        text, actions = _equalize_one(fl[f"F{i}"], target, pool.get(f"F{i}", []))
        out[f"F{i}"] = {
            "text": text,
            "tokens": count_tokens(text)[0],
            "target": target,
            "delta": count_tokens(text)[0] - target,
            "actions": actions,
        }
    return {"available": True, "fillers": out}


def equalized_fillers() -> dict[str, str]:
    """The build-time filler texts: strict-equalized when the tokenizer is available, else raw."""
    eq = equalize_fillers()
    if not eq.get("available"):
        return fillers()
    return {k: v["text"] for k, v in eq["fillers"].items()}


def cell_mass_report(tol: int = 10) -> dict:
    """Exact system-prompt token mass for every sign-vector cell (constant-mass check, PREREG §2).

    All 22 sign-vector cells (FULL, NEUTRAL, 5 LOO, 5 AOI, 10 F) must sit within ±tol tokens of
    FULL after equalization. BEAUTY1/NOSYS are reported for reference only (they are the nudge /
    bare controls, not length-matched by design).
    """
    from .config import cells_config

    masses: dict[str, int] = {}
    ref: dict[str, int | None] = {}
    for cell in cells_config()["cells"]:
        prompt = build_system_prompt(cell["id"])
        mass = count_tokens(prompt)[0] if prompt is not None else 0
        if cell.get("sign") is not None:
            masses[cell["id"]] = mass
        else:
            ref[cell["id"]] = mass
    full = masses["FULL"]
    devs = {cid: m - full for cid, m in masses.items()}
    max_abs = max(abs(d) for d in devs.values())
    return {"masses": masses, "reference_cells": ref, "full_mass": full,
            "deviations": devs, "max_abs_deviation": max_abs,
            "pass": max_abs <= tol, "tol": tol}


def run_build_audits() -> dict:
    """Run the build-time audits (a)-(d) + the two sync audits (c'/match).

    (a) token balance; (b) filler banned-topic; (c) filler identity PLAN<->canonical;
    (c') component identity PLAN<->canonical; filler<->component length match;
    (d) prompt leakage (imported from src/prompts).
    """
    from .prompts import audit_prompt_leakage  # local import avoids circular dependency

    return {
        "token_balance": audit_token_balance(),
        "filler_banned_topics": audit_filler_banned_topics(include_pool=True,
                                                           include_equalized=True),
        "filler_identity": audit_filler_identity(),
        "component_identity": audit_component_identity(),
        "padding_identity": audit_padding_identity(),
        "filler_component_match": audit_filler_component_match(),
        "prompt_leakage": audit_prompt_leakage(),
    }


# --------------------------------------------------------------------------- balancing (padding/trimming)

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def trim_to(text: str, target_tokens: int) -> str:
    """Trim `text` to <= target_tokens at a sentence boundary (PLAN §II.1.2)."""
    sentences = _SENTENCE_END.split(text)
    out: list[str] = []
    for s in sentences:
        cand = " ".join(out + [s])
        if count_tokens(cand)[0] > target_tokens and out:
            break
        out.append(s)
    return " ".join(out).strip()


def pad_to(text: str, target_tokens: int, filler_text: str) -> str:
    """Pad `text` up toward target_tokens with trailing clauses from `filler_text` (PLAN §II.1.2)."""
    sentences = _SENTENCE_END.split(filler_text)
    out = text
    for s in sentences:
        if count_tokens(out)[0] >= target_tokens:
            break
        out = (out + " " + s).strip()
    return out


def balance_components() -> dict[str, str]:
    """Return C1..C5 padded/trimmed into the ±15% band if any fall outside (else raw text).

    For frozen v1 all components are in-band, so this is a no-op; exercised on a synthetic
    out-of-band case in the tests.
    """
    comps = dict(components())
    fl = fillers()
    audit = audit_token_balance()
    if audit["pass"]:
        return comps
    lo, hi = audit["band"]  # pragma: no cover - v1 is in-band
    target = int(round(audit["mean"]))
    for k, v in audit["counts"].items():
        if v > hi:
            comps[k] = trim_to(comps[k], target)
        elif v < lo:
            comps[k] = pad_to(comps[k], target, fl["F" + k[1]])
    return comps


# --------------------------------------------------------------------------- prompt assembly

def cell_sign_vector(cell_id: str) -> list[int] | None:
    """The ±1 sign vector over [C1..C5] for a factorial/LOO cell, else None (BEAUTY1/NOSYS)."""
    return cells_by_id()[cell_id].get("sign")


def build_system_prompt(cell_id: str) -> str | None:
    """Assemble a cell's system prompt (PLAN §II.1.5).

    - NOSYS: returns None (no system message — NOT an empty string).
    - BEAUTY1: returns the beauty line.
    - factorial/LOO/AOI/NEUTRAL: per-slot real component (sign +1) or matched filler (sign -1),
      joined by the block separator. Constant mass, constant slot order. Fillers are the
      STRICT-EQUALIZED texts (|F_i - C_i| <= 2 exact tokens) when the tokenizer is available;
      raw frozen fillers otherwise (documented no-tokenizer fallback).
    """
    scfg = skill_config()
    cell = cells_by_id()[cell_id]
    sign = cell.get("sign")
    if sign is None:
        if cell["system"] == "none":
            return None
        if cell["system"] == "beauty":
            return scfg["beauty_line"]
        raise ValueError(f"cell {cell_id} has no sign and unknown system '{cell['system']}'")
    comps = components()
    fl = equalized_fillers()
    slots = []
    for i, s in enumerate(sign):
        key = f"C{i + 1}" if s == 1 else f"F{i + 1}"
        slots.append(comps[key] if s == 1 else fl[key])
    return scfg["block_separator"].join(slots)


def output_constraint() -> str:
    """The constant hermetic-output constraint (PLAN §II.1.4), appended to every user turn."""
    return skill_config()["output_constraint"]
