from app.llm import generate_answer
from app.semantic_search import semantic_search


def answer_question(question: str, top_k: int = 5) -> dict:
    results = semantic_search(question, top_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "question": question,
            "answer": "I could not find relevant information in the available documents.",
            "sources": [],
        }

    context_parts = []

    for document, metadata in zip(documents, metadatas):
        context_parts.append(
            f"""
Document ID: {metadata["document_id"]}
Chunk Index: {metadata["chunk_index"]}

Content:
{document}
"""
        )

    context = "\n".join(context_parts)

    answer = generate_answer(question, context)

    sources = [
        {
            "document_id": metadata["document_id"],
            "chunk_index": metadata["chunk_index"],
            "distance": distance,
        }
        for metadata, distance in zip(metadatas, distances)
    ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
    }

