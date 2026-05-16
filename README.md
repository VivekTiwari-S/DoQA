# DoQA — Conversational Document Intelligence

> Upload any PDF. Ask anything. Get grounded, context-aware answers.

DoQA is a RAG-based (Retrieval-Augmented Generation) document Q&A system that lets you have a conversation with your documents. Built with LangChain, Pinecone, and Gemma — it retrieves the most relevant chunks from your uploaded PDF and generates precise, grounded answers rather than hallucinated ones.

---

## How it works

```
User uploads PDF
      ↓
PDF is parsed and split into chunks
      ↓
Chunks are embedded (HuggingFace) and stored in Pinecone
      ↓
User asks a question
      ↓
Question is embedded → top-k relevant chunks retrieved from Pinecone
      ↓
Chunks + question passed to Gemma (via OpenRouter)
      ↓
Grounded answer returned to user
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangChain |
| Vector Store | Pinecone |
| Embeddings | HuggingFace (`all-MiniLM-L6-v2`) |
| LLM | Gemma (via OpenRouter) |
| Backend | FastAPI |
| Frontend | Streamlit |
| PDF Parsing | PyPDF2 |

---

## Project Structure

```
DoQA/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # FastAPI endpoints (upload, query)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ingestion.py       # PDF parsing, chunking, embedding, Pinecone upsert
│   │   └── retrieval.py       # Query embedding, Pinecone search, LLM answer gen
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic request/response models
│   └── __init__.py
├── ui/
│   └── streamlit_app.py       # Streamlit frontend
├── uploads/                   # Temp storage for uploaded PDFs (gitignored)
├── .env                       # API keys (gitignored)
├── .gitignore
├── main.py                    # FastAPI app entrypoint
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- A [Pinecone](https://www.pinecone.io/) account (free tier works)
- An [OpenRouter](https://openrouter.ai/) API key for Gemma access

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/DoQA.git
cd DoQA

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the root directory:

```env
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=doqa-index
OPENROUTER_API_KEY=your_openrouter_api_key
```

### Run the app

```bash
# Start the FastAPI backend
uvicorn main:app --reload

# In a separate terminal, start the Streamlit frontend
streamlit run ui/streamlit_app.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload a PDF and trigger ingestion into Pinecone |
| `POST` | `/query` | Ask a question and get a grounded answer |

---

## Roadmap

- [x] Project structure and architecture
- [ ] PDF ingestion pipeline (parse → chunk → embed → upsert)
- [ ] RAG retrieval pipeline (query → search → generate)
- [ ] FastAPI backend with upload and query endpoints
- [ ] Streamlit frontend with file uploader and chat interface
- [ ] Multi-document support (query across multiple uploaded PDFs)
- [ ] Source citation in answers (show which page the answer came from)

---

## Author

**Vivek Tiwari** — [LinkedIn](https://linkedin.com/in/your-profile) · [GitHub](https://github.com/your-username)

---

## License

MIT