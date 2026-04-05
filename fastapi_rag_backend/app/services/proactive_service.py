import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rag_backend.app.config import settings
from fastapi_rag_backend.app.db import SessionLocal
from fastapi_rag_backend.app.models import ProactiveNotification, UserMemoryProfile
from fastapi_rag_backend.app.schemas import HomepageHighlightsResponse, NotificationResponse
from fastapi_rag_backend.app.services.priority_service import predict_next_priority_with_confidence


def _normalize_feedback_status(status: str) -> str:
    s = (status or "").strip().lower()
    if s in {"accept", "accepted"}:
        return "accepted"
    if s in {"ignore", "ignored", "read"}:
        return "ignored"
    if s in {"dismiss", "dismissed"}:
        return "dismissed"
    return "new"


def _clamp_threshold(value: float) -> float:
    return max(settings.proactive_threshold_min, min(settings.proactive_threshold_max, value))


def _effective_threshold(profile: UserMemoryProfile | None) -> float:
    if profile is None:
        return settings.proactive_confidence_threshold
    return _clamp_threshold(float(profile.proactive_threshold))


async def trigger_proactive_for_user(db: AsyncSession, user_id: str) -> ProactiveNotification | None:
    profile_result = await db.execute(select(UserMemoryProfile).where(UserMemoryProfile.user_id == user_id))
    profile = profile_result.scalar_one_or_none()

    priority_text, confidence = await predict_next_priority_with_confidence(db, user_id)
    if not priority_text:
        return None

    if confidence < _effective_threshold(profile):
        return None

    dedupe_after = datetime.utcnow() - timedelta(minutes=settings.proactive_dedupe_minutes)
    existing_result = await db.execute(
        select(ProactiveNotification)
        .where(
            ProactiveNotification.user_id == user_id,
            ProactiveNotification.priority_text == priority_text,
            ProactiveNotification.created_at >= dedupe_after,
            ProactiveNotification.status.in_(["new", "read", "accepted", "ignored"]),
        )
        .order_by(ProactiveNotification.created_at.desc())
        .limit(1)
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return existing

    row = ProactiveNotification(
        user_id=user_id,
        priority_text=priority_text,
        confidence=confidence,
        status="new",
        source="prediction",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def apply_notification_feedback(
    db: AsyncSession,
    notification_id,
    status: str,
) -> tuple[ProactiveNotification | None, float | None]:
    result = await db.execute(select(ProactiveNotification).where(ProactiveNotification.id == notification_id))
    row = result.scalar_one_or_none()
    if row is None:
        return None, None

    normalized = _normalize_feedback_status(status)
    row.status = normalized
    db.add(row)

    profile_result = await db.execute(select(UserMemoryProfile).where(UserMemoryProfile.user_id == row.user_id))
    profile = profile_result.scalar_one_or_none()

    if profile is not None and normalized in {"accepted", "ignored", "dismissed"}:
        feedback = dict(profile.feedback_stats or {})
        feedback[normalized] = int(feedback.get(normalized, 0)) + 1
        profile.feedback_stats = feedback

        delta = 0.0
        if normalized == "accepted":
            delta = settings.proactive_adjust_accept
        elif normalized == "ignored":
            delta = settings.proactive_adjust_ignore
        elif normalized == "dismissed":
            delta = settings.proactive_adjust_dismiss

        profile.proactive_threshold = _clamp_threshold(float(profile.proactive_threshold) + delta)
        profile.updated_at = datetime.utcnow()
        db.add(profile)

    await db.commit()
    await db.refresh(row)

    new_threshold = _effective_threshold(profile)
    return row, new_threshold


async def run_proactive_cycle() -> int:
    count = 0
    async with SessionLocal() as db:
        users_result = await db.execute(select(UserMemoryProfile.user_id))
        user_ids = [r[0] for r in users_result.all() if r[0]]

        for uid in user_ids:
            created = await trigger_proactive_for_user(db, uid)
            if created is not None and created.status == "new":
                count += 1

    return count


async def proactive_loop(stop_event: asyncio.Event) -> None:
    if not settings.proactive_enabled:
        return

    while not stop_event.is_set():
        try:
            await run_proactive_cycle()
        except Exception:
            # Keep scheduler alive even if one cycle fails.
            pass

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.proactive_interval_seconds)
        except asyncio.TimeoutError:
            continue


async def fetch_user_notifications(db: AsyncSession, user_id: str, limit: int = 20) -> list[ProactiveNotification]:
    result = await db.execute(
        select(ProactiveNotification)
        .where(ProactiveNotification.user_id == user_id)
        .order_by(ProactiveNotification.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


def map_notifications(rows: list[ProactiveNotification]) -> list[NotificationResponse]:
    return [
        NotificationResponse(
            notification_id=r.id,
            user_id=r.user_id,
            priority_text=r.priority_text,
            confidence=float(r.confidence),
            status=r.status,
            source=r.source,
            created_at=r.created_at,
        )
        for r in rows
    ]


def build_homepage_highlights(user_id: str, rows: list[ProactiveNotification]) -> HomepageHighlightsResponse:
    return HomepageHighlightsResponse(
        user_id=user_id,
        generated_at=datetime.utcnow(),
        highlights=map_notifications(rows),
    )
