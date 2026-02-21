# rag/retriever.py
from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np
from openai import OpenAI

MIN_SCORE = float(os.getenv("MIN_SIMILARITY", "0.2"))

_BASE = Path(__file__).resolve().parent
ROOT = _BASE.parent
DOCS_PATH = Path(os.getenv("DOCS_PATH", str(ROOT / "docs.pkl")))
FAISS_PATH = Path(os.getenv("FAISS_PATH", str(ROOT / "faiss.index")))

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")  # 1536 dims by default :contentReference[oaicite:1]{index=1}

_docs: List[Any] | None = None
_index: faiss.Index | None = None

_client = OpenAI()

def _load_resources() -> None:
    global _docs, _index
    if _docs is not None and _index is not None:
        return

    if not DOCS_PATH.exists():
        raise FileNotFoundError(f"Docs file not found: {DOCS_PATH}")
    if not FAISS_PATH.exists():
        raise FileNotFoundError(f"FAISS index not found: {FAISS_PATH}")

    with open(DOCS_PATH, "rb") as f:
        _docs = pickle.load(f)

    _index = faiss.read_index(str(FAISS_PATH))

def _to_text(doc: Any) -> str:
    # supports either str docs OR dict docs from older pipelines
    if isinstance(doc, str):
        return doc
    if isinstance(doc, dict):
        for k in ("text", "content", "chunk", "page_content"):
            v = doc.get(k)
            if isinstance(v, str):
                return v
        return str(doc)
    return str(doc)

# embed the user question into a vector
def _embed_query(text: str) -> np.ndarray:
    # OpenAI Embeddings API :contentReference[oaicite:2]{index=2}
    text = text[:4000]  # safety cap
    resp = _client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    vec = np.array(resp.data[0].embedding, dtype="float32")
    # If you built the index with normalized vectors, normalize queries too
    faiss.normalize_L2(vec.reshape(1, -1))
    return vec

# Finds the top_k closest chunk
def retrieve_context(query: str, top_k: int = 8) -> List[Dict[str, Any]]:
    _load_resources()    #loads docs.pkl and faiss.index
    assert _docs is not None and _index is not None   # confirms that the two resources are available, else crash

    q = _embed_query(query).reshape(1, -1)
    scores, idxs = _index.search(q, top_k)

    # for debugging
    print("[RAG] raw scores:", scores[0][:5], flush=True)

    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], idxs[0]):
        if idx < 0 or score < MIN_SCORE:
            continue
        doc = _docs[int(idx)]
        results.append({"text": _to_text(doc), "score": float(score)})
    return results
