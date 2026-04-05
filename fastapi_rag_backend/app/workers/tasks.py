import asyncio
import uuid

from sqlalchemy import delete, select, update

from fastapi_rag_backend.app.db import SessionLocal
from fastapi_rag_backend.app.models import Chunk, Document
from fastapi_rag_backend.app.services.ingestion_service import build_embeddings_for_chunks, chunk_text, extract_text
from fastapi_rag_backend.app.services.s3_service import download_bytes
from fastapi_rag_backend.app.workers.celery_app import celery_app


async def _ingest_document(document_id: str) -> None:
    doc_uuid = uuid.UUID(document_id)

    async with SessionLocal() as db:
        stmt = select(Document).where(Document.id == doc_uuid)
        result = await db.execute(stmt)
        doc = result.scalar_one_or_none()

        if doc is None:
            return

        await db.execute(update(Document).where(Document.id == doc_uuid).values(status="processing"))
        await db.commit()

        try:
            blob = download_bytes(doc.s3_key)
            text = extract_text(blob, doc.content_type)
            chunks = chunk_text(text)
            vectors = build_embeddings_for_chunks(chunks)

            await db.execute(delete(Chunk).where(Chunk.document_id == doc_uuid))

            for i, (chunk, vec) in enumerate(zip(chunks, vectors, strict=False)):
                db.add(
                    Chunk(
                        document_id=doc_uuid,
                        chunk_index=i,
                        content=chunk,
                        embedding=vec,
                        meta={"length": len(chunk)},
                    )
                )

            await db.execute(update(Document).where(Document.id == doc_uuid).values(status="ready"))
            await db.commit()
        except Exception:
            await db.execute(update(Document).where(Document.id == doc_uuid).values(status="failed"))
            await db.commit()
            raise


@celery_app.task(name="tasks.ingest_document")
def ingest_document(document_id: str) -> str:
    asyncio.run(_ingest_document(document_id))
    return document_id
