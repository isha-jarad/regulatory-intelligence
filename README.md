# AI-Powered Regulatory Document Intelligence Platform

A FastAPI-based backend for ingesting regulatory and policy documents, storing structured document data in PostgreSQL, generating semantic embeddings with SentenceTransformers, indexing document chunks in ChromaDB, and using Gemini-powered Retrieval-Augmented Generation (RAG) to answer questions with source references.

## 1. Project Overview

The AI-Powered Regulatory Document Intelligence Platform is a backend-focused document intelligence system designed around regulatory, compliance, policy, and other text-heavy documents.

The system can:

- Ingest text-based PDF documents.
- Extract PDF text using pypdf.
- Store document metadata and content in PostgreSQL.
- Split documents into overlapping chunks.
- Store chunks as separate relational records.
- Generate semantic embeddings using SentenceTransformers.
- Store embeddings in persistent ChromaDB.
- Perform semantic similarity search over document chunks.
- Retrieve relevant context for user questions.
- Use Google Gemini to generate grounded answers.
- Return source metadata identifying the documents and chunks used for the answer.
- Expose the functionality through a FastAPI REST API.

A concise description of the project is:

I built a FastAPI-based regulatory document intelligence backend that ingests text-based PDF documents, stores document metadata and chunks in PostgreSQL, generates semantic embeddings using SentenceTransformers, indexes them in ChromaDB, retrieves relevant regulatory passages through semantic search, and uses Gemini to generate grounded answers with source references.

## 2. Architecture

                    ┌──────────────────────┐
                    │       FastAPI        │
                    │      REST API        │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┴────────────┐
                 │                          │
                 ▼                          ▼
        ┌─────────────────┐        ┌─────────────────┐
        │  PDF Ingestion  │        │ Direct JSON API │
        │     pypdf       │        │ POST /documents │
        └────────┬────────┘        └────────┬────────┘
                 │                          │
                 └────────────┬─────────────┘
                              ▼
                    ┌──────────────────┐
                    │    PostgreSQL    │
                    │                  │
                    │   documents      │
                    │   document_chunks│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     Chunking     │
                    │ 1000 chars /     │
                    │ 200 overlap      │
                    └────────┬─────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │   SentenceTransformers │
                 │   all-MiniLM-L6-v2     │
                 │   384-dimensional      │
                 │   embeddings           │ 
                 └────────────┬───────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │     ChromaDB     │
                    │ Persistent vector│
                    │      store       │
                    └────────┬─────────┘
                             │
                     Semantic Retrieval
                             │
                             ▼
                    ┌──────────────────┐
                    │ Relevant Chunks  │
                    │ + Metadata       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Gemini LLM      │
                    │  Grounded RAG    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Answer + Sources │
                    └──────────────────┘

## 3. Core Data Flow

The main PDF-to-RAG pipeline is:

PDF
 ↓
FastAPI upload endpoint
 ↓
pypdf text extraction
 ↓
PostgreSQL document
 ↓
Character-based chunking
 ↓
PostgreSQL document_chunks
 ↓
SentenceTransformer embeddings
 ↓
ChromaDB
 ↓
Semantic similarity search
 ↓
Relevant chunks
 ↓
RAG context
 ↓
Gemini
 ↓
Grounded answer + source metadata

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| PostgreSQL | Relational database |
| SQLAlchemy | ORM and database access |
| Psycopg | PostgreSQL driver |
| Pydantic | API request/response validation |
| Pydantic Settings | Environment configuration |
| pypdf | PDF text extraction |
| SentenceTransformers | Semantic embeddings |
| all-MiniLM-L6-v2 | Embedding model |
| ChromaDB | Persistent vector store |
| Google Gemini | LLM for grounded answer generation |
| VS Code | Development environment |

---

## 5. Database Design

The system uses PostgreSQL for structured and persistent document data.

### 5.1 Documents

The `documents` table stores:

- `id`
- `title`
- `source`
- `content`
- `created_at`

### 5.2 Document Chunks

The `document_chunks` table stores:

- `id`
- `document_id`
- `chunk_index`
- `content`

The relationship is:

Document
   │
   └── 1 ─────────── many ── DocumentChunk

A document therefore has multiple chunk records rather than storing all chunks inside a single database field.

### 5.3 Why Store Chunks Separately?

Separating chunks provides several advantages:

- Individual chunks can be indexed independently.
- Each chunk has its own position within a document.
- Chunk metadata can be stored alongside the content.
- PostgreSQL remains responsible for structured document and chunk data.
- The vector store can associate embeddings with specific chunk IDs and metadata.
- The design is easier to extend later with versioning, re-indexing, or additional metadata.

---

## 6. Why PostgreSQL + ChromaDB?

This project intentionally uses two storage systems for different responsibilities.

### 6.1 PostgreSQL

PostgreSQL stores structured application data:

- Document metadata
- Full document text
- Document chunks
- Relationships between documents and chunks
- Creation timestamps

### 6.2 ChromaDB

ChromaDB stores vector representations of chunks and supports semantic similarity search.

This separation keeps the relational and vector responsibilities clear:

PostgreSQL → source-of-record structured data 
ChromaDB → semantic/vector retrieval


### 6.3 Why Not pgvector?

PostgreSQL with pgvector would be a strong production architecture because it could combine relational and vector data in PostgreSQL.

For this project, pgvector was deliberately not used because the development environment is Windows-based and building/installing the PostgreSQL vector extension was outside the project's one-to-two-day scope.

Instead, ChromaDB provides a straightforward local persistent vector store while PostgreSQL remains responsible for relational data.

This is a conscious project-scope decision rather than an attempt to claim that ChromaDB is universally better than pgvector.

---

## 7. Chunking

The project uses a simple character-based chunking strategy.

### 7.1 Current Configuration

- **Chunk size:** 1000 characters
- **Overlap:** 200 characters

The overlap helps preserve context across chunk boundaries.

For example:

Chunk 0: characters 0 - 999
Chunk 1: characters 800 - 1799
Chunk 2: characters 1600 - 2599

The implementation is intentionally simple and suitable for the current project scope.

More advanced sentence-aware or paragraph-aware chunking is a possible future improvement.

---

## 8. Why `db.flush()` Is Used During PDF Ingestion

When a new document is uploaded, the document must be inserted before its chunks can reference its generated ID.

The upload transaction therefore follows this pattern:

db.add(new_document) 
db.flush()

# new_document.id is now available

# create DocumentChunk records

db.commit()


`db.flush()` sends the pending `INSERT` to PostgreSQL without committing the transaction.

This allows PostgreSQL to generate the document's primary-key ID while keeping the document and its chunks inside the same transaction.

If chunk creation fails, the transaction can be rolled back.

This provides a useful consistency guarantee:

Document + Chunks
       │
       └── one transaction

## 9. Embeddings

The project uses:

`all-MiniLM-L6-v2`


from SentenceTransformers.

The model generates 384-dimensional embeddings.

Conceptually:

Text chunk 
 ↓ 
SentenceTransformer 
 ↓ 
384-dimensional vector


These vectors are stored in ChromaDB and used for semantic similarity search.

The model was chosen because it is relatively lightweight and practical for a local fresher-level backend project.

---

## 10. Semantic Search

The semantic search endpoint accepts a natural-language query.

Example:

What are the health benefits of physical activity?


The query is converted into an embedding using the same SentenceTransformer model.

ChromaDB then searches for nearby vectors and returns relevant document chunks.

The API response includes:

- Document ID
- Chunk index
- Chunk content
- Distance

This allows the retrieved information to remain traceable to its original document and chunk.

---

## 11. Retrieval-Augmented Generation (RAG)

The RAG pipeline combines semantic retrieval with Gemini.

The process is:

User question 
 ↓ 
Question embedding 
 ↓ 
ChromaDB semantic search 
 ↓ 
Top-k relevant chunks 
 ↓ 
Context construction 
 ↓ 
Gemini 
 ↓ 
Grounded answer 
 ↓ 
Source references


Gemini is instructed to use the supplied document context rather than inventing facts or relying on unrelated external information.

If the retrieved context is insufficient, the model is instructed to acknowledge that limitation.

This makes the system more suitable for regulatory and policy-oriented question answering where traceability is important.

---

## 12. Gemini Integration

Gemini integration is isolated in:

`app/llm.py`


The API key is loaded through environment configuration rather than being hardcoded in source code.

The current model is:

`gemini-3.5-flash-lite`


The project uses the Google Gemini SDK Interactions API to generate the final answer.

Secrets are intentionally kept outside the source repository.

---

## 13. Offline Embedding Indexing

Embedding generation is currently performed through:

python -m app.index_embeddings

This script:

1. Reads document chunks from PostgreSQL.
2. Generates an embedding for each chunk.
3. Stores the embeddings in ChromaDB.
4. Stores document and chunk metadata alongside the vectors.

This is intentionally an offline indexing step rather than automatic embedding generation during every document upload.

For the current project scope, this keeps ingestion and indexing responsibilities straightforward.

A future version could automatically queue or perform embedding/indexing after document ingestion.

---

## 14. Backfilling Existing Documents

Chunking was added after some documents had already been created.

Instead of deleting those documents, a one-time backfill script was created:

`app/backfill_chunks.py`


It:

1. Finds documents without chunks.
2. Uses the existing chunking function.
3. Creates the missing `DocumentChunk` records.
4. Skips documents that already have chunks.
5. Uses transaction rollback on errors.

The resulting database was verified with:

140 total chunks


The embeddings were then regenerated/indexed into ChromaDB, resulting in:

140 ChromaDB vectors


This demonstrates how the project handled an incremental schema/application change without destroying existing data.

---

## 15. API Endpoints

### 15.1 Health

`GET /`

Returns a simple API status message.

---

### 15.2 Documents

The following endpoints provide basic document CRUD operations:

- `GET /documents`
- `POST /documents`
- `GET /documents/{id}`
- `PUT /documents/{id}`
- `DELETE /documents/{id}`


---

### 15.3 Document Search

`GET /documents/search`

Supports optional query parameters such as:

- `q`
- `source`

The search uses PostgreSQL and searches document title/content using case-insensitive matching.

Example:

GET /documents/search?q=physical%20activity


---

### 15.4 PDF Upload

`POST /documents/upload`

The endpoint:

1. Accepts PDF uploads.
2. Enforces a 10 MB maximum file size.
3. Validates the PDF content type.
4. Extracts text using pypdf.
5. Rejects PDFs where no text can be extracted.
6. Creates the document.
7. Generates chunks.
8. Stores the chunks in PostgreSQL.

---

### 15.5 Document Chunks

`GET /documents/{id}/chunks`

Returns the chunks belonging to a document.

Example:

GET /documents/10/chunks


---

### 15.6 Semantic Search

`GET /documents/semantic-search`

Parameters:

- `q`
- `top_k`

Example:

GET /documents/semantic-search?q=What%20are%20the%20health%20benefits%20of%20physical%20activity?&top_k=3


---

### 15.7 RAG Question Answering

`GET /documents/ask`

Parameters:

- `q`
- `top_k`

Example:

GET /documents/ask?q=What%20are%20the%20health%20benefits%20of%20physical%20activity?&top_k=3


The response contains:

- Original question
- Generated answer
- Source document IDs
- Source chunk indexes
- Retrieval distances

---

## 16. Example RAG Response

A successful response has the following structure:

{
  "question": "What are the health benefits of physical activity?",
  "answer": "Based on the provided documents, the health benefits of physical activity include ...",
  "sources": [
    {
      "document_id": 10,
      "chunk_index": 1,
      "distance": 0.5528
    },
    {
      "document_id": 10,
      "chunk_index": 0,
      "distance": 0.5725
    }
  ]
}
The exact answer and distances vary depending on the query and retrieved chunks.

---

## 17. Project Structure

regulatory-intelligence/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── index_embeddings.py
│   ├── semantic_search.py
│   ├── llm.py
│   ├── rag.py
│   └── backfill_chunks.py
│
├── chroma_db/
│   └── Local persistent ChromaDB data
│
├── .env
├── .venv/
└── README.md

## 18. Local Setup

### 18.1 Prerequisites

The project was developed using:

- Windows
- Python 3.14.x
- PostgreSQL 18.x
- VS Code

Git is only required when publishing the completed project to GitHub.

---

### 18.2 Clone or Download the Project

After obtaining the project source, open the project directory in VS Code.

---

### 18.3 Create the Virtual Environment

The project uses a Python virtual environment:

`.venv/`


The existing environment should be preserved rather than recreated unnecessarily.

---

### 18.4 Activate the Environment

Windows PowerShell:

.\.venv\Scripts\Activate.ps1


---

### 18.5 Configure Environment Variables

Create a `.env` file in the project root.

Example structure:

DATABASE_URL=postgresql+psycopg://postgres:YOUR_ENCODED_PASSWORD@localhost:5432/regulatory_intelligence
GEMINI_API_KEY=YOUR_GEMINI_API_KEY


Do not commit the real `.env` file to GitHub.

---

### 18.6 Create the PostgreSQL Database

Start PostgreSQL and create:

`regulatory_intelligence`


The application uses PostgreSQL through SQLAlchemy and Psycopg.

---

### 18.7 Start the API

With the virtual environment activated:

uvicorn app.main:app --reload


The API will normally be available at:

`http://127.0.0.1:8000`


Interactive Swagger documentation is available at:

`http://127.0.0.1:8000/docs`


---

## 19. Embedding Indexing

After document chunks exist in PostgreSQL, run:

python -m app.index_embeddings


The script generates embeddings and updates the persistent ChromaDB collection.

This is currently a manual/offline indexing step.

---

## 20. Important Limitations

### 20.1 Text-Based PDFs Only

The current ingestion pipeline uses pypdf for text extraction.

Scanned or image-only PDFs may not contain an extractable text layer.

Such documents can currently result in:

Could not extract text from the PDF


OCR is intentionally postponed as a future enhancement.

---

### 20.2 Document Update Synchronization

`PUT /documents/{id}` currently updates the PostgreSQL document record but does not automatically regenerate:

- Document chunks
- Embeddings
- ChromaDB vectors

Therefore, after updating a document, PostgreSQL and the vector index can temporarily become out of sync.

Automatic re-chunking and re-indexing is a planned improvement.

---

### 20.3 Offline Embedding Generation

Embeddings are currently generated using:

python -m app.index_embeddings


rather than automatically during every upload.

This keeps the current architecture simple and was appropriate for the project's limited development scope.

---

### 20.4 Simple Chunking

The current chunker uses fixed character lengths with overlap.

Future versions could use:

- Paragraph-aware chunking
- Sentence-aware chunking
- Token-based chunking
- Document-specific chunk sizes
- Metadata-aware chunking

---

### 20.5 No Authentication Yet

Authentication and authorization are not currently implemented.

The project focuses primarily on the document ingestion, retrieval, and RAG backend pipeline.

---

## 21. Design Decisions

### 21.1 PostgreSQL for Structured Data

PostgreSQL provides reliable relational storage for documents, chunks, metadata, and relationships.

### 21.2 Separate Chunk Table

Chunks are represented as database rows rather than embedded inside document content.

This makes chunk-level indexing and metadata management straightforward.

### 21.3 ChromaDB for Vectors

ChromaDB provides persistent local vector storage without requiring a PostgreSQL vector extension.

### 21.4 SentenceTransformers

`all-MiniLM-L6-v2` provides a lightweight semantic embedding model suitable for local development.

### 21.5 Gemini for Generation

Gemini is used only after relevant document context has been retrieved.

This separates:
Retrieval
from:
Generation

and makes the RAG flow easier to understand and debug.

### 21.6 Source References

The API returns document and chunk metadata with RAG answers so that retrieved information remains traceable.

---

## 22. Error Handling

The API includes basic error handling for cases such as:

- Missing documents → `404`
- Invalid PDF uploads → `400`
- PDFs larger than 10 MB → `413`
- PDFs without extractable text → `400`
- Invalid query parameters → FastAPI validation errors
- Database write failures → transaction rollback

Write operations use transaction handling with rollback so that failed database operations do not leave partially committed data.

---

## 23. Verification

The core pipeline has been tested end-to-end.

The final verification included:

| Metric | Count |
|---|---:|
| PostgreSQL chunks | 140 |
| ChromaDB vectors | 140 |


Semantic search successfully retrieved relevant chunks from:
`WHO Fact Sheet.pdf`


A RAG query about the health benefits of physical activity successfully returned:

- A grounded Gemini-generated answer
- Relevant document chunks
- Document IDs
- Chunk indexes
- Retrieval distances

This verified the complete:

Document → Chunk → Embedding → Retrieval → RAG → Sources
pipeline.

---

## 24. Future Improvements

Potential future improvements include:

- OCR for scanned/image-only PDFs
- Automatic embedding/indexing after uploads
- Automatic re-chunking and re-indexing after document updates
- Versioning of documents and embeddings
- Sentence-aware or token-aware chunking
- PostgreSQL pgvector integration
- Authentication and authorization
- Role-based access control
- Background task/queue processing
- Better document metadata extraction
- Citation formatting with page-level references
- Automated tests
- Production deployment
- Monitoring and logging
- Document deletion synchronization with ChromaDB

These are intentionally outside the current project scope.

---

## 25. Why This Project Is Backend-Focused

Although the project uses AI components, the core engineering work is backend-oriented:

- REST API design
- HTTP methods and status codes
- Request validation
- PostgreSQL database design
- SQLAlchemy ORM
- Relational relationships
- Transaction handling
- PDF ingestion
- Chunk persistence
- Vector-store integration
- Semantic retrieval
- External API integration
- Environment configuration
- Error handling
- Separation of application responsibilities

The AI components are integrated into a backend workflow rather than being the entire application.

---

## 26. Interview Summary

A concise way to explain the project in an interview:

I built a FastAPI-based regulatory document intelligence backend. It accepts text-based regulatory and policy PDFs, extracts and stores their content in PostgreSQL, splits documents into overlapping chunks, generates 384-dimensional embeddings using SentenceTransformers, and stores those embeddings in ChromaDB for semantic retrieval. For question answering, the system retrieves the most relevant chunks and passes them as controlled context to Gemini, which generates a grounded answer along with the source document and chunk metadata. I also implemented CRUD APIs, PostgreSQL text search, PDF ingestion, transaction handling, and an offline embedding-indexing workflow.

The main architectural trade-off was using PostgreSQL plus ChromaDB instead of pgvector because of the Windows/project-time constraints. I also deliberately kept OCR, authentication, advanced chunking, and automatic re-indexing outside the initial scope.

---

## 27. Status

The core backend is feature-complete and has been verified end-to-end.

| Feature | Status |
|---|---|
| FastAPI | ✓ |
| PostgreSQL | ✓ |
| SQLAlchemy | ✓ |
| PDF ingestion | ✓ |
| Document CRUD | ✓ |
| PostgreSQL text search | ✓ |
| Document chunking | ✓ |
| SentenceTransformer embeddings | ✓ |
| ChromaDB | ✓ |
| Semantic search | ✓ |
| Gemini integration | ✓ |
| RAG | ✓ |
| Source metadata | ✓ |
| End-to-end verification | ✓ |

The remaining project work is focused on documentation, repository cleanup, .gitignore, and publication to GitHub.

