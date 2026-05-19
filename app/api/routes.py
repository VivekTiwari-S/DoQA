import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import UploadResponse, QueryRequest, QueryResponse, SourceChunk
from app.core.ingestion import ingest_pdf
from app.core.retrieval import generate_answer

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and trigger the ingestion pipeline.
    The PDF is parsed, chunked, embedded, and upserted into Pinecone.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks_indexed = ingest_pdf(file_path, file.filename)

        return UploadResponse(
            message="PDF successfully ingested into Pinecone.",
            filename=file.filename,
            chunks_indexed=chunks_indexed,
            index_name=os.getenv("PINECONE_INDEX_NAME", "doqa-index")
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    finally:
        # Clean up the uploaded file after ingestion
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    """
    Ask a question against the ingested document.
    Retrieves relevant chunks from Pinecone and generates a grounded answer via Gemma.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = generate_answer(request.question, top_k=request.top_k)

        sources = [
            SourceChunk(
                page=chunk["page"],
                text=chunk["text"],
                score=chunk["score"]
            )
            for chunk in result["sources"]
        ]

        return QueryResponse(
            question=request.question,
            answer=result["answer"],
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")