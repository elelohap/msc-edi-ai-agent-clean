from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from rag.llm import ask_llm
from rag.retriever import retrieve_context
from rag.formatting.markdown import format_markdown_safe
from rag.limits import limiter
from rag.limits import real_ip


from rag.routing.policy import (
    route_early,
    route_intake,
    route_policy_logistics,
    route_requirement_or_suitability,
    pick_rag_fallback,
)

import re

router = APIRouter()

print("ROUTER LOADED", flush=True)


# -----------------------------
# Helpers
# -----------------------------

def is_suitability_question(q: str) -> bool:
    q = (q or "").lower()
    return any(p in q for p in [
        "am i suitable",
        "will i be suitable",
        "would i be suitable",
        "is edi suitable",
        "suitable for me",
        "fit for edi",
        "good fit",
        "good candidate",
        "do i stand a chance",
        "chance of admission",
        "should i apply",
    ])


def normalize_inline_numbered_lists(text: str) -> str:
    if not text:
        return text

    text = re.sub(r":\s*(\d+\.)\s+\*\*", r":\n\n\1 **", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!\n)\s+(\d+\.)\s+\*\*", r"\n\n\1 **", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


# -----------------------------
# Main endpoint
# -----------------------------

@router.post("/ask")
@limiter.limit("10/minute")
async def ask(request: Request):
    payload = await request.json()
    q = (payload.get("question") or payload.get("query") or "").strip()

    if not q:
        return JSONResponse({"answer": pick_rag_fallback("")})

    ip = real_ip(request)
    print(f"[ASK] ip={ip} q={q}", flush=True)


    # Retrieve once; reuse everywhere
    context_chunks = retrieve_context(q, top_k=10)

    # 0) Early exits (greetings, thanks, etc.)
    r = route_early(q)
    if r:
        return JSONResponse({"answer": format_markdown_safe(r)})

    r = route_intake(q)
    if r:
        return JSONResponse({"answer": format_markdown_safe(r)})

    # 1) Policy / logistics (visa, immigration, Student’s Pass) — HARD STOP
    r = route_policy_logistics(q, context_chunks)
    if r:
        return JSONResponse({"answer": format_markdown_safe(r)})

    # 2) Requirement vs suitability
    rs = route_requirement_or_suitability(q, context_chunks)
    if rs:
        kind, payload = rs
        if kind == "direct" and not is_suitability_question(q):
            return JSONResponse({"answer": format_markdown_safe(payload)})

    # 3) LLM (always used for suitability questions)
    answer = ask_llm(q, context_chunks)
    answer = normalize_inline_numbered_lists(answer)

    # 4) Suitability fallback ONLY if LLM failed
    if is_suitability_question(q) and not answer.strip():
        answer = pick_rag_fallback(q)

    # 5) Final generic fallback
    if not answer.strip():
        answer = pick_rag_fallback(q)

    return JSONResponse({"answer": answer})
