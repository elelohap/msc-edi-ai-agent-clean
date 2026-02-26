# rag/routing/policy.py
# keep this ordering

from typing import Any, Optional, Tuple
from . import patterns as P
from . import fallbacks as F
from .helpers import (
    chunks_to_text,
    has_any_signal,
    extract_requirement_thing,
    POSITIONING_SIGNALS,
    HARD_REQUIREMENT_SIGNALS,
)

def answer_requirement(q: str, context_chunks: Any) -> str:
    thing = extract_requirement_thing(q) or "that"
    ctx = chunks_to_text(context_chunks)

    if ctx and has_any_signal(ctx, HARD_REQUIREMENT_SIGNALS):
        return f"Yes — {thing} is required for admission to MSc Engineering Design & Innovation (EDI)."

    if ctx and has_any_signal(ctx, POSITIONING_SIGNALS):
        return (
            f"No — {thing} is not a formal requirement for admission to MSc Engineering Design & Innovation (EDI). "
            "Admissions are usually assessed holistically."
        )

    return F.REQUIREMENT_FALLBACK_GENERIC


def route_early(q: str) -> Optional[str]:
    if P.GREETING_PATTERN.match(q):
        return "Hello! I can help you with MSc EDI programme related questions."
    if P.THANKS_PATTERN.match(q):
        return "You’re welcome!"
    if P.PRAISE_PATTERN.match(q):
        return "Glad it helped!"
    if P.MDES_PATTERN.search(q):
        return F.MDES_REDIRECT_MSG
    return None


def route_intake(q: str) -> Optional[str]:
    # Suitability must always win
    if P.SUITABILITY_PATTERN.search(q):
        return None

    # Not an intake-related question
    if not (
        P.INTAKE_PATTERN.search(q)
        or P.PROGRAMME_START_PATTERN.search(q)
        or P.APPLICATION_PERIOD_PATTERN.search(q)
    ):
        return None

    if P.PROGRAMME_START_PATTERN.search(q):
        return F.PROGRAMME_START_FALLBACK

    if P.APPLICATION_PERIOD_PATTERN.search(q):
        return None  # let RAG handle exact dates

    return (
        "When you say “intake”, do you mean the **programme start date** "
        "or the **application period**?\n\n"
        "• Programme start date: when classes begin\n"
        "• Application period: when you submit your application"
    )



def route_policy_logistics(q: str, context_chunks: Any) -> Optional[str]:
    if P.OFFER_OUTCOME_PATTERN.search(q):
        return F.OFFER_OUTCOME_FALLBACK

    if P.REAPPLICATION_PATTERN.search(q):
        return F.REAPPLICATION_FALLBACK

    if P.VISA_PROCESS_PATTERN.search(q):
        return F.VISA_PROCESS_FALLBACK

    if P.VISA_PATTERN.search(q):
        return F.VISA_FALLBACK

    if P.ARRIVAL_PATTERN.search(q):
        return None if context_chunks else F.NOT_FOUND_FALLBACK

    return None


def route_requirement_or_suitability(
    q: str, context_chunks: Any
) -> Optional[Tuple[str, str]]:
    # Requirements: can be answered directly
    if (
        P.REQUIREMENT_PATTERN.search(q)
        and not P.WH_PREFIX_PATTERN.search(q)
        and not P.LOGISTICS_PATTERN.search(q)
    ):
        return ("direct", answer_requirement(q, context_chunks))

    # Suitability: DETECT ONLY — never answer here
    if P.SUITABILITY_PATTERN.search(q) or P.SUITABILITY_PROFILE_PATTERN.search(q):
        return ("suitability", "")

    return None


def pick_rag_fallback(q: str) -> str:
    if (
        P.REQUIREMENT_PATTERN.search(q)
        and not P.WH_PREFIX_PATTERN.search(q)
        and not P.LOGISTICS_PATTERN.search(q)
    ):
        return F.REQUIREMENT_FALLBACK_GENERIC

    if P.SUITABILITY_PATTERN.search(q) or P.SUITABILITY_PROFILE_PATTERN.search(q):
        return F.SUITABILITY_FALLBACK

    return F.NOT_FOUND_FALLBACK
