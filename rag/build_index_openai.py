# rag/build_index_openai.py
from __future__ import annotations

import os
import pickle
import time
from pathlib import Path
from typing import Iterator, List, Tuple

import faiss
import numpy as np
from openai import OpenAI

# ---- Config (override via env vars) ----
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "64"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", "0"))  # 0 = no limit
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "60"))  # seconds

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
# DATA_DIR = ROOT / "data"
DATA_DIR = Path(os.getenv("DATA_DIR", str(ROOT / "data")))
DOCS_PATH = ROOT / "docs.pkl"
FAISS_PATH = ROOT / "faiss.index"

client = OpenAI()


def chunk_text(text: str, chunk_size: int, overlap: int) -> Iterator[str]:
    """Yield overlapping character chunks from text (memory-safe)."""
    text = text.replace("\r\n", "\n").strip()
    n = len(text)
    if n == 0:
        return
    
    if overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be < CHUNK_SIZE")

    start = 0
    while start < n:
        end = min(n, start + chunk_size)
        c = text[start:end].strip()
        if c:
            yield c

        # ✅ critical: if we reached the end, stop (prevents infinite tail repeats)
        if end >= n:
            break
        start = end - overlap

def iter_sources() -> Iterator[Tuple[str, str]]:
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Missing data folder: {DATA_DIR}")
    files = sorted(DATA_DIR.rglob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No .txt files found in: {DATA_DIR}")
    for fp in files:
        yield fp.name, fp.read_text(encoding="utf-8", errors="ignore")


def embed_batch(texts: List[str]) -> np.ndarray:
    """Embed a batch and return normalized float32 vectors."""
    print(f"Embedding batch of {len(texts)}...")
    t0 = time.time()
    resp = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
        timeout=OPENAI_TIMEOUT,
    )
    vecs = np.array([d.embedding for d in resp.data], dtype="float32")
    faiss.normalize_L2(vecs)  # cosine-like similarity with IndexFlatIP
    print(f"Batch done in {time.time() - t0:.1f}s")
    return vecs


def main() -> None:
    docs: List[str] = []
    vec_batches: List[np.ndarray] = []

    chunk_count = 0
    pending: List[str] = []

    print(f"Reading sources from: {DATA_DIR}")
    print(
        f"Embedding model: {EMBED_MODEL} | batch={BATCH_SIZE} | chunk={CHUNK_SIZE} | "
        f"overlap={CHUNK_OVERLAP} | max_chunks={MAX_CHUNKS or 'none'}"
    )

    for fname, text in iter_sources():
        print(f"FILE {fname}: chars={len(text)}")
        for i, c in enumerate(chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP), start=1):
            docs.append(f"[{fname} | chunk {i}]\n{c}")
            pending.append(docs[-1])
            chunk_count += 1

            if chunk_count % 500 == 0:
                print(f"Chunks processed: {chunk_count}")

            if MAX_CHUNKS and chunk_count >= MAX_CHUNKS:
                break

            if len(pending) >= BATCH_SIZE:
                vec_batches.append(embed_batch(pending))
                pending.clear()

          
        if MAX_CHUNKS and chunk_count >= MAX_CHUNKS:
            break

    if pending:
        vec_batches.append(embed_batch(pending))
        pending.clear()

    if not docs:
        raise RuntimeError("No chunks produced. Check your data/*.txt files.")

    print(f"Total chunks collected: {len(docs)}")

    vecs = np.vstack(vec_batches)
    print(f"Embeddings shape: {vecs.shape}")

    dim = vecs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vecs)

    print("Writing docs.pkl and faiss.index...")
    with open(DOCS_PATH, "wb") as f:
        pickle.dump(docs, f)

    faiss.write_index(index, str(FAISS_PATH))

    print("Wrote:", DOCS_PATH, FAISS_PATH)
    print("Done.")


if __name__ == "__main__":
    main()
