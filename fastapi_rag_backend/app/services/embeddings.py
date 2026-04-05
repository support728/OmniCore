from fastapi_rag_backend.app.services.openai_client import client
from fastapi_rag_backend.app.config import settings

def _validate_dimensions(embedding: list[float]) -> None:
    if len(embedding) != settings.vector_dim:
        raise ValueError(
            f"Embedding dimension mismatch: got {len(embedding)}, expected {settings.vector_dim}. "
            f"Check EMBEDDING_MODEL and VECTOR_DIM."
        )


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    print("USING KEY:", settings.openai_api_key[:10])
    response = client.embeddings.create(model=settings.embedding_model, input=texts)
    vectors = [list(item.embedding) for item in response.data]
    for vec in vectors:
        _validate_dimensions(vec)
    return vectors


def embed_query(text: str) -> list[float]:
    print("USING KEY:", settings.openai_api_key[:10])
    response = client.embeddings.create(model=settings.embedding_model, input=[text])
    vector = list(response.data[0].embedding)
    _validate_dimensions(vector)
    return vector
