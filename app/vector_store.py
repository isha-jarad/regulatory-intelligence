import chromadb


client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="document_chunks"
)


def add_chunk(
    chunk_id: int,
    content: str,
    embedding: list[float],
    document_id: int,
    chunk_index: int,
):
    collection.upsert(
        ids=[str(chunk_id)],
        embeddings=[embedding],
        documents=[content],
        metadatas=[
            {
                "document_id": document_id,
                "chunk_index": chunk_index,
            }
        ],
    )


def search_chunks(
    embedding: list[float],
    top_k: int = 5,
):
    return collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
    )
