from fastapi import FastAPI, Depends, File, HTTPException, UploadFile, Query
from pypdf import PdfReader

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, DocumentChunk
from app.schemas import (
    DocumentCreate,
    DocumentResponse,
    DocumentChunkResponse,
    SemanticSearchResult,
    RAGResponse,
)
from app.chunking import chunk_text
from app.semantic_search import semantic_search
from app.rag import answer_question


app = FastAPI()


@app.get("/")
def home():
    return {"message": "Regulatory Intelligence API is running!"}



@app.post("/documents/upload", response_model=DocumentResponse, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    MAX_FILE_SIZE = 10 * 1024 * 1024

    file_contents = file.file.read()

    if len(file_contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF file is too large. Maximum size is 10 MB."
        )

    file.file.seek(0)

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    reader = PdfReader(file.file)

    extracted_text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            extracted_text += page_text + "\n"

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the PDF"
        )

    new_document = Document(
        title=file.filename,
        source="Uploaded PDF",
        content=extracted_text
    )

    try:
        db.add(new_document)

        # Flush sends the INSERT to PostgreSQL
        # so new_document.id becomes available.
        db.flush()

        chunks = chunk_text(new_document.content)

        for index, chunk in enumerate(chunks):
            new_chunk = DocumentChunk(
                document_id=new_document.id,
                chunk_index=index,
                content=chunk
            )

            db.add(new_chunk)

        db.commit()
        db.refresh(new_document)

    except Exception:
        db.rollback()
        raise

    return new_document


@app.get("/documents", response_model=list[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).all()
    return documents


@app.post("/documents", response_model=DocumentResponse, status_code=201)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    new_document = Document(
        title=document.title,
        source=document.source,
        content=document.content
    )

    try:
        db.add(new_document)
        db.commit()
        db.refresh(new_document)
    except Exception:
        db.rollback()
        raise

    return new_document


@app.get("/documents/search", response_model=list[DocumentResponse])
def search_documents(
    q: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Document)

    if q:
        search_pattern = f"%{q}%"

        query = query.filter(
            (Document.title.ilike(search_pattern)) |
            (Document.content.ilike(search_pattern))
        )

    if source:
        query = query.filter(Document.source.ilike(source))

    return query.all()

@app.get(
    "/documents/semantic-search",
    response_model=list[SemanticSearchResult],
)
def semantic_search_documents(
    q: str,
    top_k: int = Query(5, ge=1, le=20),
):
    results = semantic_search(q, top_k)

    response = []

    for i, content in enumerate(results["documents"][0]):
        response.append(
            SemanticSearchResult(
                document_id=results["metadatas"][0][i]["document_id"],
                chunk_index=results["metadatas"][0][i]["chunk_index"],
                content=content,
                distance=results["distances"][0][i],
            )
        )

    return response


@app.get("/documents/ask", response_model=RAGResponse)
def ask_question(q: str, top_k: int = Query(5, ge=1, le=20)):
    return answer_question(q, top_k)



@app.get("/documents/{id}/chunks", response_model=list[DocumentChunkResponse])
def get_document_chunks(id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document.chunks



@app.get("/documents/{id}", response_model=DocumentResponse)
def get_document(id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == id).first()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return document

@app.put("/documents/{id}", response_model=DocumentResponse)
def update_document(
    id: int,
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    existing_document = (
        db.query(Document)
        .filter(Document.id == id)
        .first()
    )

    if existing_document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    existing_document.title = document.title
    existing_document.source = document.source
    existing_document.content = document.content

    try:
        db.commit()
        db.refresh(existing_document)
    except Exception:
        db.rollback()
        raise

    return existing_document


@app.delete("/documents/{id}")
def delete_document(id: int, db: Session = Depends(get_db)):
    document = (
        db.query(Document)
        .filter(Document.id == id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    try:
        db.delete(document)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Document deleted successfully"}


