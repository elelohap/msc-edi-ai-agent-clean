
# test_retriever.py
import logging
from rag.retriever import retrieve_context

logging.basicConfig(level=logging.INFO)

question = "What is the tuition fee for the EDI program?"
print("\n🔍 Testing retriever with question:", question)

chunks = retrieve_context(question, top_k=5)

print("\n📌 Retrieved chunks:")
for i, c in enumerate(chunks, 1):
    print(f"{i}. score={c['score']}\n   text={c['text'][:200]}...\n")
