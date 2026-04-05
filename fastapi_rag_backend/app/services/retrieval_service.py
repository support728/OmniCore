import math

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rag_backend.app.db import is_postgres_backend
from fastapi_rag_backend.app.models import Chunk, Document


def _to_pgvector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in vector) + "]"


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


async def _search_similar_chunks_sqlite(
    db: AsyncSession,
    query_vector: list[float],
    top_k: int,
) -> list[dict]:
    stmt = (
        select(Chunk, Document)
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.status == "ready")
    )
    result = await db.execute(stmt)
    ranked_rows: list[dict] = []

    for chunk, document in result.all():
        score = max(0.0, min(1.0, _cosine_similarity(list(chunk.embedding or []), query_vector)))
        ranked_rows.append(
            {
                "document_id": chunk.document_id,
                "filename": document.filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "meta": chunk.meta or {},
                "distance": 1.0 - score,
                "score": score,
            }
        )

    ranked_rows.sort(key=lambda row: row["score"], reverse=True)
    return ranked_rows[:top_k]


async def search_similar_chunks(
    db: AsyncSession,
    query_vector: list[float],
    top_k: int,
) -> list[dict]:
    if not is_postgres_backend():
        return await _search_similar_chunks_sqlite(db, query_vector, top_k)

    query_literal = _to_pgvector_literal(query_vector)

    sql = text(
        """
        SELECT
            c.document_id,
            d.filename,
            c.chunk_index,
            c.content,
            c.meta,
            (c.embedding <=> CAST(:query_vec AS vector)) AS distance,
            GREATEST(0, LEAST(1, 1 - (c.embedding <=> CAST(:query_vec AS vector)))) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE d.status = 'ready'
        ORDER BY distance ASC
        LIMIT :top_k
        """
    )

    result = await db.execute(sql, {"query_vec": query_literal, "top_k": top_k})
    rows = result.mappings().all()
    return [dict(r) for r in rows]
