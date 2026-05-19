import os
import uuid
import PyPDF2
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# --- Pinecone setup ---
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "doqa-index")
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension

# --- Embedding model (loaded once at import time) ---
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def get_or_create_index():
    """Get existing Pinecone index or create one if it doesn't exist."""
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(INDEX_NAME)


def parse_pdf(file_path: str) -> list[dict]:
    """
    Parse a PDF and return a list of dicts with page number and text.
    Each dict: { "page": int, "text": str }
    """
    pages = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"page": page_num + 1, "text": text.strip()})
    return pages


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Split page texts into smaller chunks using LangChain's splitter.
    Each chunk carries metadata: page number and a unique chunk id.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = []
    for page in pages:
        splits = splitter.split_text(page["text"])
        for split in splits:
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": split,
                "page": page["page"]
            })
    return chunks


def embed_and_upsert(chunks: list[dict], filename: str) -> int:
    """
    Embed chunks using HuggingFace and upsert vectors into Pinecone.
    Returns the number of chunks indexed.
    """
    index = get_or_create_index()

    texts = [chunk["text"] for chunk in chunks]
    vectors = embeddings_model.embed_documents(texts)

    pinecone_vectors = []
    for chunk, vector in zip(chunks, vectors):
        pinecone_vectors.append({
            "id": chunk["id"],
            "values": vector,
            "metadata": {
                "text": chunk["text"],
                "page": chunk["page"],
                "source": filename
            }
        })

    # Upsert in batches of 100 to stay within Pinecone limits
    batch_size = 100
    for i in range(0, len(pinecone_vectors), batch_size):
        batch = pinecone_vectors[i:i + batch_size]
        index.upsert(vectors=batch)

    return len(pinecone_vectors)


def ingest_pdf(file_path: str, filename: str) -> int:
    """
    Full ingestion pipeline:
    PDF → parse → chunk → embed → upsert into Pinecone.
    Returns number of chunks indexed.
    """
    pages = parse_pdf(file_path)
    if not pages:
        raise ValueError("Could not extract any text from the PDF. It may be scanned or image-based.")

    chunks = chunk_pages(pages)
    if not chunks:
        raise ValueError("No text chunks were generated from the PDF.")

    indexed_count = embed_and_upsert(chunks, filename)
    return indexed_count