import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DATA_FOLDER = "data"  # folder containing .txt files
DOCS_PKL = "docs.pkl"
FAISS_INDEX = "faiss.index"

# ----- SETTINGS -----
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50


def load_text_files(folder):
    docs = []
    file_list = sorted(os.listdir(folder))  # fixed ordering

    print(f"📄 Loading documents from {folder}...")

    for filename in file_list:
        if filename.endswith(".txt"):
            path = os.path.join(folder, filename)

            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()

            if text:
                docs.append(text)

    print(f"🔹 Loaded {len(docs)} documents.")
    return docs


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0

    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks


def build_dataset(docs):
    all_chunks = []

    print("🔹 Splitting into chunks...")

    for doc in docs:
        chunks = chunk_text(doc)
        all_chunks.extend(chunks)

    print(f"🔹 Total text chunks: {len(all_chunks)}")
    return all_chunks


def embed_chunks(chunks):
    print("🔹 Embedding text with all-MiniLM-L6-v2...")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks, batch_size=32, show_progress_bar=True)

    embeddings = np.asarray(embeddings).astype("float32")
    return embeddings


def save_index(embeddings, chunks):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)

    print(f"🔹 Creating FAISS index (dim={dim})...")
    index.add(embeddings)

    faiss.write_index(index, FAISS_INDEX)

    print("💾 Saving docs.pkl...")
    with open(DOCS_PKL, "wb") as f:
        pickle.dump(chunks, f)

    print("✅ Saved faiss.index and docs.pkl")


def main():
    docs = load_text_files(DATA_FOLDER)
    chunks = build_dataset(docs)
    embeddings = embed_chunks(chunks)
    save_index(embeddings, chunks)
    print("🎉 Ingestion complete! FAISS index is ready.")


if __name__ == "__main__":
    main()
