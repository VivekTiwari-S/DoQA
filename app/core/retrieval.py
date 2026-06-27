import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI

load_dotenv()

# --- Pinecone setup ---
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "doqa-index")

# --- OpenRouter client (points to Gemma via OpenRouter) ---
llm_client = OpenAI(
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "google/gemma-4-26b-a4b-it:free")

# --- Embedding model (same model as ingestion — critical for consistent retrieval) ---
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def retrieve_chunks(question: str, top_k: int = 5) -> list[dict]:
    """
    Embed the user question and retrieve top-k similar chunks from Pinecone.
    Returns a list of dicts with text, page, and similarity score.
    """
    index = pc.Index(INDEX_NAME)

    query_vector = embeddings_model.embed_query(question)

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )

    chunks = []
    for match in results.matches:
        chunks.append({
            "text": match.metadata.get("text", ""),
            "page": match.metadata.get("page", 0),
            "score": round(match.score, 4)
        })

    return chunks


def build_prompt(question: str, chunks: list[dict]) -> str:
    """
    Build the RAG prompt by combining retrieved context chunks with the user question.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"[Chunk {i} | Page {chunk['page']}]\n{chunk['text']}")

    context = "\n\n".join(context_parts)

    prompt = f"""You are DoQA, a helpful assistant that answers questions strictly based on the provided document context.

CONTEXT:
{context}

QUESTION:
{question}

INSTRUCTIONS:
- Answer only using the context above.
- If the answer is not found in the context, say: "I couldn't find relevant information in the uploaded document."
- Be concise and accurate.
- Reference page numbers where relevant.

ANSWER:"""

    return prompt


def generate_answer(question: str, top_k: int = 5) -> dict:
    """
    Full retrieval pipeline:
    Question → embed → Pinecone search → build prompt → Gemma → return answer + sources.
    """
    chunks = retrieve_chunks(question, top_k=top_k)

    if not chunks:
        return {
            "answer": "No relevant content found in the document. Please upload a PDF first.",
            "sources": []
        }

    prompt = build_prompt(question, chunks)

    response = llm_client.chat.completions.create(
        model=GEMMA_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=512
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "sources": chunks
    }