from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rag_backend.app.models import ActionRecord, GoalRecord, InsightRecord
from fastapi_rag_backend.app.services.priority_service import predict_next_priority
from fastapi_rag_backend.app.schemas import BriefActionItem, BriefInsightItem, DailyBriefResponse, GoalResponse


def _utc_day_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now or datetime.utcnow()
    start = datetime(current.year, current.month, current.day)
    end = start + timedelta(days=1)
    return start, end


async def build_daily_brief(db: AsyncSession, user_id: str = "default") -> DailyBriefResponse:
    day_start, day_end = _utc_day_window()

    insight_result = await db.execute(
        select(InsightRecord)
        .where(
            InsightRecord.user_id == user_id,
            InsightRecord.created_at >= day_start,
            InsightRecord.created_at < day_end,
        )
        .order_by(InsightRecord.score.desc(), InsightRecord.created_at.desc())
        .limit(10)
    )
    insight_rows = list(insight_result.scalars().all())

    completed_result = await db.execute(
        select(ActionRecord)
        .join(InsightRecord, InsightRecord.id == ActionRecord.insight_id)
        .where(
            InsightRecord.user_id == user_id,
            ActionRecord.status == "completed",
            ActionRecord.completed_at.is_not(None),
            ActionRecord.completed_at >= day_start,
            ActionRecord.completed_at < day_end,
        )
        .order_by(ActionRecord.completed_at.desc())
        .limit(20)
    )
    completed_rows = list(completed_result.scalars().all())

    remaining_result = await db.execute(
        select(ActionRecord)
        .join(InsightRecord, InsightRecord.id == ActionRecord.insight_id)
        .where(
            InsightRecord.user_id == user_id,
            ActionRecord.status.in_(["pending", "in_progress", "blocked"]),
        )
        .order_by(ActionRecord.score.desc(), ActionRecord.updated_at.desc())
        .limit(20)
    )
    remaining_rows = list(remaining_result.scalars().all())

    goals_result = await db.execute(
        select(GoalRecord)
        .where(GoalRecord.user_id == user_id, GoalRecord.status.in_(["active", "paused"]))
        .order_by(GoalRecord.priority_weight.desc(), GoalRecord.updated_at.desc())
        .limit(10)
    )
    goal_rows = list(goals_result.scalars().all())

    top_insights = [
        BriefInsightItem(
            insight_id=i.id,
            question=i.question,
            insight_text=i.insight_text,
            score=i.score,
            created_at=i.created_at,
        )
        for i in insight_rows
    ]

    completed_actions = [
        BriefActionItem(
            action_id=a.id,
            insight_id=a.insight_id,
            step_number=a.step_number,
            action_text=a.action_text,
            status=a.status,
            score=a.score,
            completed_at=a.completed_at,
        )
        for a in completed_rows
    ]

    remaining_priorities = [
        BriefActionItem(
            action_id=a.id,
            insight_id=a.insight_id,
            step_number=a.step_number,
            action_text=a.action_text,
            status=a.status,
            score=a.score,
            completed_at=a.completed_at,
        )
        for a in remaining_rows
    ]

    summary = (
        f"Daily brief for {day_start.date().isoformat()}: "
        f"{len(top_insights)} top insights, "
        f"{len(completed_actions)} completed actions, "
        f"{len(remaining_priorities)} remaining priorities."
    )

    next_likely_priority = await predict_next_priority(db, user_id)

    active_goals = [
        GoalResponse(
            goal_id=g.id,
            user_id=g.user_id,
            title=g.title,
            description=g.description,
            status=g.status,
            progress_percent=g.progress_percent,
            priority_weight=g.priority_weight,
            target_date=g.target_date,
            created_at=g.created_at,
            updated_at=g.updated_at,
        )
        for g in goal_rows
    ]

    return DailyBriefResponse(
        brief_date=day_start.date().isoformat(),
        summary=summary,
        next_likely_priority=next_likely_priority,
        top_insights=top_insights,
        completed_actions=completed_actions,
        remaining_priorities=remaining_priorities,
        active_goals=active_goals,
    )
