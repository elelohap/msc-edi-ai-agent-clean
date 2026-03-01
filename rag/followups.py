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

def generate_followups(question: str, context_chunks=None):
    q = (question or "").lower()

    def has(*keywords):
        return any(k in q for k in keywords)

    if has("project", "projects", "hands-on"):
        return [
            "What is the workload like in EDI?",
            "What skills will I gain from these projects?",
            "What are the career outcomes after EDI?",
        ]

    if has("workload", "stress", "cope", "difficult"):
        return [
            "What type of projects will I work on?",
            "What support systems are available for students?",
            "What are the career outcomes after EDI?",
        ]

    if has("career", "job", "employment"):
        return [
            "What skills will I gain from EDI?",
            "What industries do graduates enter?",
            "What are the admission requirements?",
        ]

    if has("apply", "admission", "eligible", "suitable"):
        return [
            "What are the admission requirements?",
            "Do I need a portfolio for EDI?",
            "How do I apply to the EDI programme?",
        ]

    if has("deadline", "process", "timeline"):
        return [
            "What documents are required for application?",
            "What is the application timeline?",
            "How do I apply to the EDI programme?",
        ]

    if has("visa", "international", "student pass"):
        return [
            "Do I need a visa to study at NUS?",
            "What is the application process for international students?",
            "What are the admission requirements?",
        ]

    return [
        "What is the curriculum like?",
        "What type of projects will I work on?",
        "What are the career outcomes after EDI?",
    ]

def followups_when_unanswerable(question: str) -> list[str]:
    # keep these 100% within your documented coverage
    return [
        "What is the curriculum like?",
        "What type of projects will I work on?",
        "What are the admission requirements?",
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
