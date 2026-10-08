from app.embeddings import generate_embedding
from app.vector_store import search_chunks


def semantic_search(query: str, top_k: int = 5):
    query_embedding = generate_embedding(query)

    return search_chunks(
        embedding=query_embedding,
        top_k=top_k,
    )


if __name__ == "__main__":
    query = "What does this document say about JavaScript?"

    results = semantic_search(query, top_k=3)

    for i, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        print("\n--- Result", i + 1, "---")
        print("Document ID:", metadata["document_id"])
        print("Chunk index:", metadata["chunk_index"])
        print("Distance:", distance)
        print("Content:")
        print(document[:500])
