from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from rag.retriever import retrieve_context
from rag.llm import ask_llm

router = APIRouter()

@router.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question", "").strip()

    if not question:
        return JSONResponse({"error": "No question provided"}, status_code=400)

    context_chunks = retrieve_context(question, top_k=5)

    answer = ask_llm(question, context_chunks)

    return JSONResponse({"answer": answer})
