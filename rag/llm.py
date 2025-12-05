from openai import OpenAI
from rag.retriever import retrieve_context

client = OpenAI()

def ask_llm(question, context_chunks):
    # Combine retrieved context
    context_text = "\n\n".join(chunk["text"] for chunk in context_chunks)

    prompt = f"""
Use ONLY the context below to answer the question. 
If the answer is not in the context, say "The answer is not in the provided documents."

Context:
{context_text}

Question:
{question}
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    # FIX: use .content instead of ["content"]
    return completion.choices[0].message.content
