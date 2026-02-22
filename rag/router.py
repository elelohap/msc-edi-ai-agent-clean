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

# codes for traceability if anything goes wrong
def _safe_origin(origin: str | None) -> str:
    if not origin:
        return "-"
    # keep just scheme+host for readability
    try:
        from urllib.parse import urlparse
        u = urlparse(origin)
        return f"{u.scheme}://{u.netloc}" if u.scheme and u.netloc else origin[:80]
    except Exception:
        return origin[:80]


# print("ROUTER FILE LOADED FROM:", __file__, flush=True)

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
    path = "unknown"
    chunks_count = 0
    top_score = None

    payload = await request.json()
    q = (payload.get("question") or payload.get("query") or "").strip()

    origin = request.headers.get("origin")
    user_agent = request.headers.get("user-agent")
    session_id = payload.get("session_id")  # optional
    ip = real_ip(request)
    ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]

    def respond(answer_text: str, status_code: int = 200):
        latency_ms = int((time.time() - t0) * 1000)
        origin_short = _safe_origin(origin)
        # ip_for_log = ip  # or a masked version if you prefer

        print(
            f"[TRACE] path={path} ip_hash={ip_hash} origin={origin_short} "
            f"qlen={len(q)} chunks={chunks_count} top={top_score} "
            f"latency_ms={latency_ms} status={status_code}",
            flush=True
        )


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
        path = "empty"
        return respond(pick_rag_fallback(""))

    print(f"[ASK] ip={ip} q={q}", flush=True)

    # Retrieve once; reuse everywhere
    try: 
        context_chunks = retrieve_context(q, top_k=10)
    except Exception as e:
        path = "retrieval_error"
        print(f"[ERROR] stage=retrieval ip={ip_hash} origin={_safe_origin(origin)} err={repr(e)}", flush=True)
        return respond("Sorry — retrieval failed. Please try again.", status_code=500)    


    chunks_count = len(context_chunks or [])
    top_score = (context_chunks[0].get("score") if chunks_count else None)


    # just for debugging and learning, if debugging required, set DEBUG_RAG=1 in Render environment variable
    DEBUG_RAG = os.getenv("DEBUG_RAG", "0") == "1"

    if DEBUG_RAG:
        print("[RAG] top chunks preview:", flush=True)
        for i, c in enumerate(context_chunks[:3]):
            preview = (c.get("text","") if isinstance(c, dict) else str(c))[:120].replace("\n"," ")
            print(f"  - {i+1}: {preview}...", flush=True)



    # print(f"[RAG] chunks={len(context_chunks)}", flush=True)


    # 0) Early exits
    print("[FLOW] checking route_early", flush=True)
    r = route_early(q)
    if r:
        path = "early"
        print("[FLOW] route_early triggered", flush=True)
        return respond(format_markdown_safe(r))
    
    print("[FLOW] checking route_intake", flush=True)
    r = route_intake(q)
    if r:
        path = "intake"
        print("[FLOW] route_intake triggered", flush=True)
        return respond(format_markdown_safe(r))

    # 1) Policy/logistics hard stop
    print("[FLOW] checking route_policy_logistics", flush=True)
    r = route_policy_logistics(q, context_chunks)
    if r:
        path = "policy_logistics"
        print("[FLOW] route_policy_logistics triggered", flush=True)
        return respond(format_markdown_safe(r))

    # 2) Requirement vs suitability
    print("[FLOW] checking route_requirement", flush=True)
    rs = route_requirement_or_suitability(q, context_chunks)
    if rs:
        print("[FLOW] route_requirement", flush=True)
        kind, payload2 = rs
        if kind == "direct" and not is_suitability_question(q):
            path = "requirement_direct"
            return respond(format_markdown_safe(payload2))

    # 3) LLM
    try:
        path = "llm"
        answer = ask_llm(q, context_chunks)
        answer = normalize_inline_numbered_lists(answer)
    except Exception as e:
        path = "llm_error"
        print(f"[ERROR] stage=llm ip={ip_hash} origin={_safe_origin(origin)} err={repr(e)}", flush=True)
        return respond("Sorry — the AI service is temporarily unavailable. Please try again.", status_code=503)


    # print(f"[LLM] answer_len={len(answer or '')}", flush=True)


    # 4) Suitability fallback only if LLM failed
    if is_suitability_question(q) and not answer.strip():
        answer = pick_rag_fallback(q)

    # 5) Final generic fallback
    if not answer.strip():
        answer = pick_rag_fallback(q)

    return respond(answer)
