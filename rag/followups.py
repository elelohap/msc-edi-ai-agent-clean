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

# Add after _similar()

_FILLER_WORDS = {
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "is", "are", "was", "were", "do", "does", "did",
    "can", "could", "will", "would", "should", "may", "might",
    "the", "a", "an", "of", "to", "in", "on", "for", "with", "at", "from", "by", "about",
    "i", "me", "my", "we", "our", "you", "your",
    "type", "kind",  # <-- key for your duplicate case
}

def _content_tokens(text: str) -> set[str]:
    toks = []
    for w in _canon(text).split():
        if w in _FILLER_WORDS:
            continue
        # ultra-light singularization: projects -> project
        if len(w) > 3 and w.endswith("s"):
            w = w[:-1]
        toks.append(w)
    return set(toks)

def _content_duplicate(a: str, b: str) -> bool:
    ta = _content_tokens(a)
    tb = _content_tokens(b)
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    # strong overlap is effectively "same question"
    overlap = len(ta & tb) / min(len(ta), len(tb))
    return overlap >= 0.90


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
            "What are the career prospects for EDI graduates?",
            "What skills will I gain from the programme?",
            "What industries do graduates enter?",
        ]

    if "course" in combined or "module" in combined or "curriculum" in combined:
        return [
            "What courses are included in the programme?",
            "Are there elective courses available?",
            "How do I choose my courses?",
        ]

    if "apply" in combined or "suitable" in combined or "admission" in combined:
        return [
            "What are the admission requirements?",
            "Do I need a portfolio for EDI?",
            "What backgrounds are suitable for EDI?",
        ]

    return [
        "What are the admission requirements?",
        "What is the curriculum like?",
        "What career opportunities do EDI lead to?",
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

        # content-token duplicate (catches "type/kind of" variants)
        if _content_duplicate(f, question):
            continue

        # fuzzy similarity
        if len(f_can) > min_len and _similar(f_can, q) > similarity_threshold:
            continue

        # dedupe within followups
        if f_can in seen:
            continue

        # dedupe within followups (content-level)
        if any(_content_duplicate(f, prev) for prev in cleaned):
            continue


        cleaned.append(f.strip())
        seen.add(f_can)

    return cleaned
