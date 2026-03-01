from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

_PUNCT_RE = re.compile(r"[^\w\s]")

def _canon(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "")
    t = t.lower().strip()
    t = _PUNCT_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def generate_followups(question: str, context_chunks: Optional[List[Dict[str, Any]]]) -> List[str]:
    """
    Lightweight rule-based followup generation (no extra LLM calls).
    Moved from llm.py.
    """
    q = (question or "").lower()

    context_text = " ".join(
        [(c.get("text", "") if isinstance(c, dict) else str(c)) for c in (context_chunks or [])[:3]]
    ).lower()

    combined = q + " " + context_text

    if "challenge" in combined or "hard" in combined or "rigor" in combined:
        return [
            "What is the workload like in EDI?",
            "What type of projects will I work on?",
            "How do students cope in the programme?",
        ]

    if "value" in combined or "worth" in combined or "career" in combined:
        return [
            "What are the career outcomes of EDI?",
            "What skills will I gain from the programme?",
            "What industries do graduates enter?",
        ]

    if "course" in combined or "module" in combined or "curriculum" in combined:
        return [
            "What courses are included in the programme?",
            "Are there electives available?",
            "How are projects structured?",
        ]

    if "apply" in combined or "suitable" in combined or "admission" in combined:
        return [
            "What are the admission requirements?",
            "Do I need a portfolio for EDI?",
            "What backgrounds are accepted?",
        ]

    return [
        "What are the admission requirements?",
        "What is the curriculum like?",
        "What career opportunities does EDI lead to?",
    ]


def clean_followups(
    followups: Optional[List[str]],
    question: str,
    *,
    similarity_threshold: float = 0.92,
    min_len: int = 15,
) -> Optional[List[str]]:
    """
    Removes duplicate / near-duplicate followups vs the user's current question,
    and dedupes within followups.
    """
    if not followups:
        return None

    q = _canon(question)
    cleaned: List[str] = []
    seen = set()

    for f in followups:
        if not f or not f.strip():
            continue

        f_can = _canon(f)

        # exact canonical match
        if f_can == q:
            continue

        # substring containment canonical
        if f_can in q or q in f_can:
            continue

        # fuzzy similarity
        if len(f_can) > min_len and _similar(f_can, q) > similarity_threshold:
            continue

        # dedupe within followups
        if f_can in seen:
            continue

        cleaned.append(f.strip())
        seen.add(f_can)

    return cleaned
