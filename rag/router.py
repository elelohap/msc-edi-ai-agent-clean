from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from rag.llm import ask_llm
from rag.retriever import retrieve_context
from rag.formatting.markdown import format_markdown_safe
from rag.limits import limiter, real_ip

from rag.routing.policy import (
    route_early,
    route_intake,
    route_policy_logistics,
    route_requirement_or_suitability,
    pick_rag_fallback,
)

import re
import time
import hashlib
import os
from typing import Optional

import psycopg2

print("ROUTER FILE LOADED FROM:", __file__, flush=True)

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")


def log_to_postgres(
    *,
    origin: Optional[str],
    session_id: Optional[str],
    ip_hash: str,
    user_agent: Optional[str],
    question: str,
    status: int,
    latency_ms: int,
) -> None:
    if not DATABASE_URL:
        print("[LOGGING] DATABASE_URL missing; skipping DB log", flush=True)
        return

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_logs
                    (origin, session_id, ip_hash, user_agent, question, status, latency_ms)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (origin, session_id, ip_hash, user_agent, question, status, latency_ms),
                )
    except Exception as e:
        print(f"[LOGGING ERROR] {e}", flush=True)


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
    t0 = time.time()
    payload = await request.json()
    q = (payload.get("question") or payload.get("query") or "").strip()

    origin = request.headers.get("origin")
    user_agent = request.headers.get("user-agent")
    session_id = payload.get("session_id")  # optional
    ip = real_ip(request)
    ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]

    def respond(answer_text: str, status_code: int = 200):
        latency_ms = int((time.time() - t0) * 1000)

        # TEMP DEBUG: remove after first successful row appears
        # print(f"[DBLOG] inserting ip_hash={ip_hash} status={status_code}", flush=True)

        log_to_postgres(
            origin=origin,
            session_id=session_id,
            ip_hash=ip_hash,
            user_agent=user_agent,
            question=q,
            status=status_code,
            latency_ms=latency_ms,
        )
        return JSONResponse({"answer": answer_text}, status_code=status_code)

    if not q:
        return respond(pick_rag_fallback(""))

    print(f"[ASK] ip={ip} q={q}", flush=True)

    # Retrieve once; reuse everywhere
    context_chunks = retrieve_context(q, top_k=10)

    # 0) Early exits
    r = route_early(q)
    if r:
        return respond(format_markdown_safe(r))

    r = route_intake(q)
    if r:
        return respond(format_markdown_safe(r))

    # 1) Policy/logistics hard stop
    r = route_policy_logistics(q, context_chunks)
    if r:
        return respond(format_markdown_safe(r))

    # 2) Requirement vs suitability
    rs = route_requirement_or_suitability(q, context_chunks)
    if rs:
        kind, payload2 = rs
        if kind == "direct" and not is_suitability_question(q):
            return respond(format_markdown_safe(payload2))

    # 3) LLM
    answer = ask_llm(q, context_chunks)
    answer = normalize_inline_numbered_lists(answer)

    # 4) Suitability fallback only if LLM failed
    if is_suitability_question(q) and not answer.strip():
        answer = pick_rag_fallback(q)

    # 5) Final generic fallback
    if not answer.strip():
        answer = pick_rag_fallback(q)

    return respond(answer)
