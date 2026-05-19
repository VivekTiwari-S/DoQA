from pydantic import BaseModel
from typing import Optional, List


class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_indexed: int
    index_name: str


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class SourceChunk(BaseModel):
    page: int
    text: str
    score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None