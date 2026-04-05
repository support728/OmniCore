from fastapi_rag_backend.app.config import settings
from fastapi_rag_backend.app.services.embeddings import embed_texts


def extract_text(file_bytes: bytes, content_type: str) -> str:
    return file_bytes.decode("utf-8", errors="ignore")


def chunk_text(text: str) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    size = settings.chunk_size
    overlap = settings.chunk_overlap

    while start < len(cleaned):
        end = min(start + size, len(cleaned))
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(end - overlap, 0)

    return chunks


def build_embeddings_for_chunks(chunks: list[str]) -> list[list[float]]:
    return embed_texts(chunks)
