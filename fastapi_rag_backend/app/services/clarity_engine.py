from fastapi_rag_backend.app.schemas import Insight, RAGChatResponse, SourceItem


def _build_sources(contexts: list[dict]) -> list[SourceItem]:
    sources: list[SourceItem] = []
    for row in contexts:
        content = str(row.get("content", ""))
        excerpt = content[:240] + ("..." if len(content) > 240 else "")
        sources.append(
            SourceItem(
                document_id=row["document_id"],
                filename=row.get("filename", "unknown"),
                chunk_index=int(row.get("chunk_index", 0)),
                score=round(float(row.get("score", 0.0)), 4),
                excerpt=excerpt,
            )
        )
    return sources


def _build_insight(contexts: list[dict]) -> Insight:
    if not contexts:
        return Insight(
            confidence=0.1,
            retrieval_notes="No similar chunks were retrieved.",
            recommended_next_question="Can you upload a relevant document first?",
        )

    top_score = float(contexts[0].get("score", 0.0))
    confidence = max(0.1, min(1.0, top_score))
    return Insight(
        confidence=round(confidence, 3),
        retrieval_notes=f"Retrieved {len(contexts)} chunk(s). Top similarity score: {top_score:.3f}.",
        recommended_next_question="Do you want a deeper comparison across the top sources?",
    )


def build_clarity_response(question: str, contexts: list[dict]) -> RAGChatResponse:
    return RAGChatResponse(
        sources=_build_sources(contexts),
        insight=_build_insight(contexts),
        raw_context=contexts,
    )
