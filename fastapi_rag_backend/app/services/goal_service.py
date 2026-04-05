from datetime import datetime
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rag_backend.app.models import ActionRecord, GoalMilestone, GoalProgressHistory, GoalRecord


def _goal_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}", (text or "").lower())
    return set(tokens)


async def create_goal(
    db: AsyncSession,
    user_id: str,
    title: str,
    description: str | None = None,
    priority_weight: float = 1.0,
    target_date=None,
) -> GoalRecord:
    goal = GoalRecord(
        user_id=user_id,
        title=title.strip(),
        description=(description or "").strip() or None,
        status="active",
        progress_percent=0.0,
        priority_weight=max(0.1, min(3.0, float(priority_weight))),
        target_date=target_date,
        updated_at=datetime.utcnow(),
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    db.add(
        GoalProgressHistory(
            goal_id=goal.id,
            user_id=user_id,
            previous_status=None,
            new_status=goal.status,
            previous_progress=None,
            new_progress=goal.progress_percent,
            note="Goal created",
        )
    )
    await db.commit()
    return goal


async def list_goals(db: AsyncSession, user_id: str, include_completed: bool = True) -> list[GoalRecord]:
    stmt = select(GoalRecord).where(GoalRecord.user_id == user_id)
    if not include_completed:
        stmt = stmt.where(GoalRecord.status.in_(["active", "paused"]))
    stmt = stmt.order_by(GoalRecord.priority_weight.desc(), GoalRecord.updated_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_goal(db: AsyncSession, goal_id: UUID, user_id: str) -> GoalRecord | None:
    result = await db.execute(
        select(GoalRecord).where(GoalRecord.id == goal_id, GoalRecord.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_goal(
    db: AsyncSession,
    goal_id: UUID,
    user_id: str,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    progress_percent: float | None = None,
    priority_weight: float | None = None,
    target_date=None,
    note: str | None = None,
) -> GoalRecord | None:
    goal = await get_goal(db, goal_id, user_id)
    if goal is None:
        return None

    prev_status = goal.status
    prev_progress = goal.progress_percent

    if title is not None:
        goal.title = title.strip() or goal.title
    if description is not None:
        goal.description = description.strip() or None
    if status is not None:
        goal.status = status
    if progress_percent is not None:
        goal.progress_percent = max(0.0, min(100.0, float(progress_percent)))
    if priority_weight is not None:
        goal.priority_weight = max(0.1, min(3.0, float(priority_weight)))
    if target_date is not None:
        goal.target_date = target_date

    if goal.progress_percent >= 100.0 and goal.status != "archived":
        goal.status = "completed"

    goal.updated_at = datetime.utcnow()
    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    db.add(
        GoalProgressHistory(
            goal_id=goal.id,
            user_id=user_id,
            previous_status=prev_status,
            new_status=goal.status,
            previous_progress=prev_progress,
            new_progress=goal.progress_percent,
            note=note,
        )
    )
    await db.commit()
    return goal


async def list_goal_history(db: AsyncSession, user_id: str, goal_id: UUID) -> list[GoalProgressHistory]:
    result = await db.execute(
        select(GoalProgressHistory)
        .where(GoalProgressHistory.user_id == user_id, GoalProgressHistory.goal_id == goal_id)
        .order_by(GoalProgressHistory.created_at.asc())
    )
    return list(result.scalars().all())


def goal_alignment_bonus(question: str, contexts: list[dict], goals: list[GoalRecord]) -> tuple[float, list[str]]:
    if not goals:
        return 0.0, []

    q_tokens = _goal_tokens(question)
    c_tokens = set()
    for row in contexts[:5]:
        c_tokens.update(_goal_tokens(str(row.get("content", ""))[:500]))

    matched: list[str] = []
    bonus = 0.0

    for g in goals:
        goal_tokens = _goal_tokens((g.title or "") + " " + (g.description or ""))
        overlap = len((q_tokens | c_tokens).intersection(goal_tokens))
        if overlap <= 0:
            continue

        weight = float(g.priority_weight)
        progress_factor = 1.0 - min(1.0, max(0.0, float(g.progress_percent) / 100.0))
        goal_bonus = min(0.2, 0.02 * overlap * weight * max(0.3, progress_factor))
        bonus += goal_bonus
        matched.append(g.title)

    return min(0.25, bonus), matched[:3]


async def add_milestone(
    db: AsyncSession,
    goal_id: UUID,
    user_id: str,
    title: str,
    target_percent: float,
) -> GoalMilestone:
    milestone = GoalMilestone(
        goal_id=goal_id,
        user_id=user_id,
        title=title.strip(),
        target_percent=max(0.0, min(100.0, float(target_percent))),
    )
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return milestone


async def list_milestones(db: AsyncSession, user_id: str, goal_id: UUID) -> list[GoalMilestone]:
    result = await db.execute(
        select(GoalMilestone)
        .where(GoalMilestone.goal_id == goal_id, GoalMilestone.user_id == user_id)
        .order_by(GoalMilestone.target_percent.asc())
    )
    return list(result.scalars().all())


async def _achieve_milestones(db: AsyncSession, goal: GoalRecord) -> None:
    result = await db.execute(
        select(GoalMilestone).where(
            GoalMilestone.goal_id == goal.id,
            GoalMilestone.achieved_at.is_(None),
            GoalMilestone.target_percent <= goal.progress_percent,
        )
    )
    pending = list(result.scalars().all())
    for m in pending:
        m.achieved_at = datetime.utcnow()
        db.add(m)
    if pending:
        await db.commit()


async def recalculate_goal_progress(db: AsyncSession, goal_id: UUID) -> GoalRecord | None:
    """Recompute goal.progress_percent from its linked ActionRecords."""
    result = await db.execute(select(GoalRecord).where(GoalRecord.id == goal_id))
    goal = result.scalar_one_or_none()
    if goal is None:
        return None

    actions_result = await db.execute(
        select(ActionRecord).where(ActionRecord.goal_id == goal_id)
    )
    actions = list(actions_result.scalars().all())

    if not actions:
        await _achieve_milestones(db, goal)
        return goal

    total = len(actions)
    completed_count = sum(1 for a in actions if a.status == "completed")
    new_progress = round((completed_count / total) * 100.0, 2)

    prev_progress = goal.progress_percent
    prev_status = goal.status

    if abs(new_progress - prev_progress) < 0.01:
        await _achieve_milestones(db, goal)
        return goal

    goal.progress_percent = new_progress
    if new_progress >= 100.0 and goal.status not in ("archived", "completed"):
        goal.status = "completed"
    goal.updated_at = datetime.utcnow()
    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    db.add(
        GoalProgressHistory(
            goal_id=goal.id,
            user_id=goal.user_id,
            previous_status=prev_status,
            new_status=goal.status,
            previous_progress=prev_progress,
            new_progress=new_progress,
            note="Auto-recalculated from linked action progress",
        )
    )
    await db.commit()
    await _achieve_milestones(db, goal)
    return goal


async def link_action_to_goal(
    db: AsyncSession,
    goal_id: UUID,
    action_id: UUID,
    user_id: str,
) -> bool:
    goal = await get_goal(db, goal_id, user_id)
    if goal is None:
        return False
    actions_result = await db.execute(
        select(ActionRecord).where(ActionRecord.id == action_id)
    )
    action = actions_result.scalar_one_or_none()
    if action is None:
        return False
    action.goal_id = goal_id
    db.add(action)
    await db.commit()
    await recalculate_goal_progress(db, goal_id)
    return True


async def get_goal_progress_detail(
    db: AsyncSession,
    goal_id: UUID,
    user_id: str,
) -> dict | None:
    goal = await get_goal(db, goal_id, user_id)
    if goal is None:
        return None
    actions_result = await db.execute(
        select(ActionRecord)
        .where(ActionRecord.goal_id == goal_id)
        .order_by(ActionRecord.step_number.asc(), ActionRecord.created_at.asc())
    )
    linked_actions = list(actions_result.scalars().all())
    milestones = await list_milestones(db, user_id, goal_id)
    total = len(linked_actions)
    completed_count = sum(1 for a in linked_actions if a.status == "completed")
    completion = round((completed_count / total) * 100.0, 2) if total > 0 else float(goal.progress_percent)
    return {
        "goal": goal,
        "linked_actions": linked_actions,
        "milestones": milestones,
        "completion_percent": completion,
        "total_linked_actions": total,
        "completed_linked_actions": completed_count,
    }


def _goal_urgency_level(goal: GoalRecord, completion_percent: float) -> str:
    if goal.status in {"completed", "archived"}:
        return "low"

    today = datetime.utcnow().date()
    if goal.target_date is not None:
        days_left = (goal.target_date - today).days
        if days_left < 0 and completion_percent < 100.0:
            return "high"
        if days_left <= 3 and completion_percent < 70.0:
            return "high"
        if days_left <= 10:
            return "medium"

    if float(goal.priority_weight) >= 2.0 and completion_percent < 50.0:
        return "high"
    if float(goal.priority_weight) >= 1.4:
        return "medium"
    return "low"


def _goal_priority_status(goal: GoalRecord, completion_percent: float, urgency_level: str) -> str:
    if goal.status == "paused":
        return "paused"
    if goal.status in {"completed", "archived"} or completion_percent >= 100.0:
        return "completed"

    today = datetime.utcnow().date()
    if goal.target_date is not None and goal.target_date < today and completion_percent < 100.0:
        return "overdue"
    if urgency_level == "high":
        return "at_risk"
    return "on_track"


def _next_step_text(linked_actions: list[ActionRecord], milestones: list[GoalMilestone], completion_percent: float) -> tuple[str, GoalMilestone | None]:
    in_progress = next((a for a in linked_actions if a.status == "in_progress"), None)
    if in_progress is not None:
        return in_progress.action_text, None

    pending = next((a for a in linked_actions if a.status == "pending"), None)
    if pending is not None:
        return pending.action_text, None

    next_milestone = next((m for m in milestones if m.achieved_at is None), None)
    if next_milestone is not None:
        return f"Reach {round(float(next_milestone.target_percent), 1)}% milestone: {next_milestone.title}", next_milestone

    if completion_percent >= 100.0:
        return "Goal completed. Define a follow-up goal.", None

    return "Define one concrete next action with owner, due date, and a measurable success metric.", None


async def list_goal_frontend_status(
    db: AsyncSession,
    user_id: str,
    include_completed: bool = False,
) -> list[dict]:
    goals = await list_goals(db, user_id, include_completed=include_completed)
    items: list[dict] = []

    for goal in goals:
        detail = await get_goal_progress_detail(db, goal.id, user_id)
        if detail is None:
            continue

        linked_actions = detail["linked_actions"]
        milestones = detail["milestones"]
        completion_percent = float(detail["completion_percent"])
        urgency_level = _goal_urgency_level(goal, completion_percent)
        priority_status = _goal_priority_status(goal, completion_percent, urgency_level)
        next_step, next_milestone = _next_step_text(linked_actions, milestones, completion_percent)

        items.append(
            {
                "goal": goal,
                "progress_percent": round(completion_percent, 2),
                "urgency_level": urgency_level,
                "priority_status": priority_status,
                "next_step": next_step,
                "next_milestone": next_milestone,
                "milestones": milestones,
                "total_linked_actions": int(detail["total_linked_actions"]),
                "completed_linked_actions": int(detail["completed_linked_actions"]),
            }
        )

    return items
