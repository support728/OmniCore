from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rag_backend.app.models import InsightRecord


def _compact(text: str, max_len: int = 140) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3].rstrip() + "..."


def _fallback_insight(question: str) -> str:
    focus = _compact(question or "the current objective", max_len=120)
    return (
        f"Strategic read: '{focus}' is likely constrained by unclear scope, owner, or success metric. "
        "Recommended move: define one concrete outcome for the next 72 hours, assign a single owner, "
        "and track one KPI baseline before execution. "
        "This keeps momentum while deeper evidence is being collected."
    )


def generate_insight(question: str, contexts: list[dict[str, Any]]) -> tuple[str, float, UUID | None]:
    if not contexts:
        return (
            _fallback_insight(question),
            0.62,
            None,
        )

    top = contexts[0]
    top_text = str(top.get("content", "")).strip()
    if len(top_text) > 240:
        top_text = top_text[:240] + "..."

    score = max(0.1, min(1.0, float(top.get("score", 0.0))))
    source_document_id = top.get("document_id")

    insight_text = (
        f"Primary evidence for '{question}' is concentrated in chunk #{int(top.get('chunk_index', 0))} "
        f"from '{top.get('filename', 'unknown')}'. Key signal: {top_text}"
    )

    return insight_text, score, source_document_id


async def store_insight(
    db: AsyncSession,
    user_id: str,
    question: str,
    insight_text: str,
    score: float,
    source_document_id: UUID | None,
) -> InsightRecord:
    row = InsightRecord(
        user_id=user_id,
        question=question,
        insight_text=insight_text,
        score=score,
        source_document_id=source_document_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
