from app.database import SessionLocal
from app.models import DocumentChunk
from app.embeddings import generate_embedding
from app.vector_store import add_chunk


def index_chunks():
    db = SessionLocal()

    try:
        chunks = (
            db.query(DocumentChunk)
            .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
            .all()
        )

        print(f"Found {len(chunks)} chunks.")

        for chunk in chunks:
            embedding = generate_embedding(chunk.content)

            add_chunk(
                chunk_id=chunk.id,
                content=chunk.content,
                embedding=embedding,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
            )

            print(
                f"Indexed chunk {chunk.id} "
                f"(document {chunk.document_id}, "
                f"index {chunk.chunk_index})"
            )

        print("Embedding indexing completed.")

    finally:
        db.close()


if __name__ == "__main__":
    index_chunks()
