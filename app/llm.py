from google import genai

from app.database import settings


client = genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_answer(question: str, context: str) -> str:
    prompt = f"""
You are a regulatory document assistant.

Answer the user's question using ONLY the provided document context.

Rules:
- Do not invent facts.
- Do not use outside knowledge.
- If the context does not contain enough information to answer,
  clearly say that the available documents do not provide enough information.
- Give a concise, professional answer.
- Base every important claim on the provided context.

User question:
{question}

Document context:
{context}
"""

    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input=prompt,
    )

    return interaction.output_text
