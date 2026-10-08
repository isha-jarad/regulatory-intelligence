from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    title: str
    source: str
    content: str


class DocumentResponse(BaseModel):
    id: int
    title: str
    source: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str

    model_config = ConfigDict(from_attributes=True)


class SemanticSearchResult(BaseModel):
    document_id: int
    chunk_index: int
    content: str
    distance: float


class RAGSource(BaseModel):
    document_id: int
    chunk_index: int
    distance: float


class RAGResponse(BaseModel):
    question: str
    answer: str
    sources: list[RAGSource]
