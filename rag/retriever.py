import pickle
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

FAISS_PATH = "faiss.index"
DOCS_PATH = "docs.pkl"

model = SentenceTransformer("all-MiniLM-L6-v2")

with open(DOCS_PATH, "rb") as f:
    docs = pickle.load(f)

index = faiss.read_index(FAISS_PATH)

def retrieve_context(question, top_k=5):
    q_emb = model.encode([question])
    scores, indices = index.search(q_emb, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        results.append({
            "text": docs[int(idx)],
            "score": float(score)
        })
    
    return results
