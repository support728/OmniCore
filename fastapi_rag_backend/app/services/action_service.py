from datetime import datetime
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rag_backend.app.models import ActionProgressHistory, ActionRecord, InsightRecord
from fastapi_rag_backend.app.services.planning_quality import normalize_action_plan


_GENERIC_ACTION_HINTS = {
    "validate",
    "prioritize",
    "execute",
    "insight",
    "evidence",
    "source",
    "retrieved",
    "claim",
    "user",
    "intent",
    "captured",
}


def _compact_text(text: str, max_len: int = 120) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3].rstrip() + "..."


def _extract_focus_phrase(insight_text: str) -> str:
    source = (insight_text or "").strip()
    if not source:
        return "the highest-impact workstream"

    quoted = re.search(r"for\s+'([^']+)'", source, flags=re.IGNORECASE)
    if quoted and quoted.group(1).strip():
        return _compact_text(quoted.group(1), max_len=100)

    key_signal = re.search(r"key signal\s*:\s*(.+)$", source, flags=re.IGNORECASE)
    captured = re.search(r"captured\s*:\s*(.+)$", source, flags=re.IGNORECASE)
    candidate = key_signal.group(1).strip() if key_signal else (captured.group(1).strip() if captured else source)
    candidate = re.split(r"\s*\|\s*", candidate)[0]
    candidate = re.sub(r"^[^a-zA-Z0-9]+", "", candidate)

    if re.search(r"\b\d+(?:\.\d+)?%\b", candidate):
        return _compact_text(candidate, max_len=100)

    tokens = re.findall(r"[A-Za-z0-9%][A-Za-z0-9%\-_/]+", candidate)
    meaningful = [tok for tok in tokens if tok.lower() not in _GENERIC_ACTION_HINTS]
    if len(meaningful) >= 3:
        return _compact_text(" ".join(meaningful[:10]), max_len=100)

    return _compact_text(candidate, max_len=100) or "the highest-impact workstream"


def generate_action_plan(insight_text: str) -> list[str]:
    focus = _extract_focus_phrase(insight_text)

    actions = [
        f"Validate '{focus}' using 2 independent sources, assign a reviewer, and capture one confirmed fact plus one open risk within 24 hours.",
        f"Choose one concrete decision for '{focus}', assign an owner, and set a due date within the next 72 hours.",
        f"Execute the decision for '{focus}' and record a before/after metric so you can evaluate impact in the next review.",
    ]
    return normalize_action_plan(actions, focus=focus)


async def store_action_plan(
    db: AsyncSession,
    insight_id: UUID,
    actions: list[str],
    score: float,
) -> list[ActionRecord]:
    saved: list[ActionRecord] = []

    for idx, text in enumerate(actions[:3], start=1):
        row = ActionRecord(
            insight_id=insight_id,
            step_number=idx,
            action_text=text,
            status="pending",
            score=score,
            updated_at=datetime.utcnow(),
        )
        db.add(row)
        saved.append(row)

    await db.commit()

    for row in saved:
        await db.refresh(row)

    # Log initial action states for per-insight progress history.
    for row in saved:
        db.add(
            ActionProgressHistory(
                insight_id=insight_id,
                action_id=row.id,
                previous_status=None,
                new_status=row.status,
                note="Action created",
            )
        )

    await db.commit()

    return saved


async def update_action_status(
    db: AsyncSession,
    action_id: UUID,
    new_status: str,
    note: str | None = None,
    user_id: str | None = None,
) -> ActionRecord | None:
    stmt = select(ActionRecord).where(ActionRecord.id == action_id)
    if user_id is not None:
        stmt = (
            stmt.join(InsightRecord, InsightRecord.id == ActionRecord.insight_id)
            .where(InsightRecord.user_id == user_id)
        )

    result = await db.execute(stmt)
    action = result.scalar_one_or_none()
    if action is None:
        return None

    previous_status = action.status
    action.status = new_status
    action.updated_at = datetime.utcnow()

    if new_status == "completed":
        action.completed_at = datetime.utcnow()
    elif previous_status == "completed" and new_status != "completed":
        action.completed_at = None

    db.add(action)
    db.add(
        ActionProgressHistory(
            insight_id=action.insight_id,
            action_id=action.id,
            previous_status=previous_status,
            new_status=new_status,
            note=note,
        )
    )
    await db.commit()
    await db.refresh(action)

    if action.goal_id is not None:
        from fastapi_rag_backend.app.services.goal_service import recalculate_goal_progress
        await recalculate_goal_progress(db, action.goal_id)

    return action


async def get_insight_progress(db: AsyncSession, insight_id: UUID) -> tuple[list[ActionRecord], list[ActionProgressHistory]]:
    actions_result = await db.execute(
        select(ActionRecord)
        .where(ActionRecord.insight_id == insight_id)
        .order_by(ActionRecord.step_number.asc())
    )
    actions = list(actions_result.scalars().all())

    history_result = await db.execute(
        select(ActionProgressHistory)
        .where(ActionProgressHistory.insight_id == insight_id)
        .order_by(ActionProgressHistory.created_at.asc())
    )
    history = list(history_result.scalars().all())

    return actions, history
