from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rag_backend.app.models import ActionRecord, GoalRecord, InsightRecord, UserMemoryProfile
from fastapi_rag_backend.app.services.planning_quality import normalize_priority_text


_GENERIC_PRIORITY_PHRASES = (
    "validate the core claim",
    "prioritize one high-impact decision",
    "execute and measure outcome",
    "create a new action plan",
)


def _is_generic_priority_text(text: str | None) -> bool:
    if not text:
        return True
    lowered = text.lower()
    return any(phrase in lowered for phrase in _GENERIC_PRIORITY_PHRASES)


def _specific_priority_from_context(action_text: str | None, question: str | None, insight_text: str | None = None) -> str:
    source = (question or "").strip() or (insight_text or "").strip() or (action_text or "").strip()
    return normalize_priority_text(action_text, context=source)


def _topic_goal_bonus(text: str, profile: UserMemoryProfile | None) -> float:
    if profile is None:
        return 0.0

    lowered = text.lower()
    bonus = 0.0

    topics = sorted((profile.recurring_topics or {}).items(), key=lambda kv: kv[1], reverse=True)
    top_topics = [k for k, _ in topics[:8]]
    for topic in top_topics:
        if topic.lower() in lowered:
            bonus += 0.03

    for goal in (profile.goals or []):
        goal_text = str(goal).lower()
        if goal_text and goal_text in lowered:
            bonus += 0.08

    return bonus


def _explicit_goal_bonus(text: str, goals: list[GoalRecord]) -> float:
    lowered = text.lower()
    bonus = 0.0
    for goal in goals:
        if goal.status in {"completed", "archived"}:
            continue
        parts = [goal.title or "", goal.description or ""]
        goal_text = " ".join(parts).strip().lower()
        if not goal_text:
            continue
        if goal_text in lowered or any(tok in lowered for tok in goal_text.split()[:6]):
            progress_factor = 1.0 - min(1.0, max(0.0, float(goal.progress_percent) / 100.0))
            bonus += min(0.18, 0.04 * float(goal.priority_weight) * max(0.3, progress_factor))
    return min(0.25, bonus)


def _confidence_from_signal(best_value: float, profile: UserMemoryProfile | None, recent_count: int) -> float:
    # Base from ranking value, with mild boosts from profile richness and activity volume.
    profile_richness = 0.0
    if profile is not None:
        profile_richness += min(0.12, 0.01 * len(profile.goals or []))
        profile_richness += min(0.12, 0.01 * len(profile.recurring_topics or {}))

    activity_bonus = min(0.12, 0.01 * recent_count)
    conf = best_value + profile_richness + activity_bonus
    return round(max(0.0, min(1.0, conf)), 4)


async def predict_next_priority_with_confidence(db: AsyncSession, user_id: str) -> tuple[str | None, float]:
    profile_result = await db.execute(select(UserMemoryProfile).where(UserMemoryProfile.user_id == user_id))
    profile = profile_result.scalar_one_or_none()

    goals_result = await db.execute(
        select(GoalRecord)
        .where(GoalRecord.user_id == user_id)
        .order_by(GoalRecord.priority_weight.desc(), GoalRecord.updated_at.desc())
        .limit(30)
    )
    goals = list(goals_result.scalars().all())

    # Pull recent non-completed actions for this user's insights.
    pending_result = await db.execute(
        select(ActionRecord, InsightRecord)
        .join(InsightRecord, InsightRecord.id == ActionRecord.insight_id)
        .where(
            InsightRecord.user_id == user_id,
            ActionRecord.status.in_(["pending", "in_progress", "blocked"]),
        )
        .order_by(ActionRecord.score.desc(), ActionRecord.updated_at.desc())
        .limit(30)
    )

    rows = pending_result.all()
    if not rows:
        # If no pending actions, suggest from latest high-scoring insight.
        insight_result = await db.execute(
            select(InsightRecord)
            .where(InsightRecord.user_id == user_id)
            .order_by(InsightRecord.score.desc(), InsightRecord.created_at.desc())
            .limit(1)
        )
        latest = insight_result.scalar_one_or_none()
        if latest is None:
            return None, 0.0
        return _specific_priority_from_context(
            action_text=None,
            question=latest.question,
            insight_text=latest.insight_text,
        ), round(max(0.2, min(1.0, latest.score)), 4)

    best_text: str | None = None
    best_question: str | None = None
    best_insight_text: str | None = None
    best_value = float("-inf")

    for action, insight in rows:
        base = float(action.score)
        status_bonus = 0.07 if action.status == "in_progress" else 0.0
        profile_bonus = _topic_goal_bonus(action.action_text + " " + insight.question, profile)
        explicit_goal_bonus = _explicit_goal_bonus(action.action_text + " " + insight.question, goals)
        value = base + status_bonus + profile_bonus + explicit_goal_bonus

        if value > best_value:
            best_value = value
            best_text = action.action_text
            best_question = insight.question
            best_insight_text = insight.insight_text

    if _is_generic_priority_text(best_text):
        best_text = _specific_priority_from_context(best_text, best_question, best_insight_text)
    else:
        context = (best_question or "").strip() or (best_insight_text or "").strip()
        best_text = normalize_priority_text(best_text, context=context)

    confidence = _confidence_from_signal(best_value, profile, recent_count=len(rows))
    return best_text, confidence


async def predict_next_priority(db: AsyncSession, user_id: str) -> str | None:
    text, _ = await predict_next_priority_with_confidence(db, user_id)
    return text
