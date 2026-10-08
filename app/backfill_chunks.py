from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Document, DocumentChunk
from app.chunking import chunk_text


def backfill_chunks():
    db: Session = SessionLocal()

    try:
        documents = db.query(Document).all()

        for document in documents:
            existing_chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == document.id)
                .count()
            )

            if existing_chunks > 0:
                print(
                    f"Skipping document {document.id}: "
                    f"already has {existing_chunks} chunks."
                )
                continue

            chunks = chunk_text(document.content)

            for index, chunk in enumerate(chunks):
                new_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                )

                db.add(new_chunk)

            print(
                f"Created {len(chunks)} chunks "
                f"for document {document.id}: {document.title}"
            )

        db.commit()
        print("Chunk backfill completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    backfill_chunks()
