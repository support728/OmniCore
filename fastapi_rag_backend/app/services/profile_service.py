from collections import Counter
from datetime import datetime
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rag_backend.app.models import ActionRecord, GoalRecord, InsightRecord, UserMemoryProfile
from fastapi_rag_backend.app.schemas import UserMemoryProfileResponse


_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "for", "of", "in", "on", "with", "is", "are", "be",
    "i", "me", "my", "you", "your", "it", "this", "that", "from", "at", "as", "by", "about",
    "what", "how", "why", "when", "where", "can", "could", "would", "should", "please",
}


def _extract_topic_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}", text.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def _extract_goals(question: str) -> list[str]:
    q = question.strip()
    goals: list[str] = []

    patterns = [
        r"(?:i want to|goal is to|i need to)\s+(.+)",
        r"(?:help me)\s+(.+)",
        r"(?:plan to)\s+(.+)",
    ]

    for pat in patterns:
        match = re.search(pat, q, flags=re.IGNORECASE)
        if match:
            goal_text = match.group(1).strip().rstrip("?.!")
            if goal_text:
                goals.append(goal_text)

    return goals


def _update_patterns(existing: dict, question: str) -> dict:
    patterns = dict(existing or {})

    def bump(key: str) -> None:
        patterns[key] = int(patterns.get(key, 0)) + 1

    q = question.lower()
    if any(x in q for x in ["compare", "difference", "vs", "versus"]):
        bump("comparison_queries")
    if any(x in q for x in ["latest", "today", "recent", "current"]):
        bump("freshness_queries")
    if any(x in q for x in ["plan", "next step", "action", "priority"]):
        bump("planning_queries")
    if any(x in q for x in ["how", "guide", "tutorial", "learn"]):
        bump("learning_queries")

    return patterns


async def update_user_profile(
    db: AsyncSession,
    user_id: str,
    question: str,
    contexts: list[dict],
) -> UserMemoryProfile:
    result = await db.execute(select(UserMemoryProfile).where(UserMemoryProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = UserMemoryProfile(
            user_id=user_id,
            recurring_topics={},
            goals=[],
            patterns={},
            interaction_count=0,
            updated_at=datetime.utcnow(),
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    topics_counter = Counter(profile.recurring_topics or {})

    question_tokens = _extract_topic_tokens(question)
    context_tokens: list[str] = []
    for ctx in contexts[:3]:
        context_tokens.extend(_extract_topic_tokens(str(ctx.get("content", ""))[:400]))

    for token in question_tokens + context_tokens:
        topics_counter[token] += 1

    updated_goals = list(profile.goals or [])
    for g in _extract_goals(question):
        if g not in updated_goals:
            updated_goals.append(g)

    profile.recurring_topics = dict(topics_counter)
    profile.goals = updated_goals[-20:]
    profile.patterns = _update_patterns(profile.patterns or {}, question)
    profile.interaction_count = int(profile.interaction_count or 0) + 1
    profile.updated_at = datetime.utcnow()

    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


def prioritize_contexts_for_profile(contexts: list[dict], profile: UserMemoryProfile) -> list[dict]:
    topic_counts = profile.recurring_topics or {}
    top_topics = {k for k, _ in sorted(topic_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]}
    goal_keywords = set()
    for goal in profile.goals or []:
        goal_keywords.update(_extract_topic_tokens(goal))

    prioritized: list[dict] = []
    for row in contexts:
        content = str(row.get("content", "")).lower()
        tokens = set(_extract_topic_tokens(content[:1000]))

        topic_overlap = len(tokens.intersection(top_topics))
        goal_overlap = len(tokens.intersection(goal_keywords))

        base = float(row.get("score", 0.0))
        personalized_score = base + (0.03 * topic_overlap) + (0.05 * goal_overlap)

        new_row = dict(row)
        new_row["personalized_score"] = round(personalized_score, 4)
        prioritized.append(new_row)

    prioritized.sort(key=lambda r: (float(r.get("personalized_score", 0.0)), float(r.get("score", 0.0))), reverse=True)
    return prioritized


def personalize_insight_text(insight_text: str, profile: UserMemoryProfile) -> str:
    topics = sorted((profile.recurring_topics or {}).items(), key=lambda kv: kv[1], reverse=True)
    top_topics = [k for k, _ in topics[:3]]
    goals = list(profile.goals or [])[-2:]

    additions: list[str] = []
    if top_topics:
        additions.append("Recurring focus: " + ", ".join(top_topics))
    if goals:
        additions.append("Active goals: " + " | ".join(goals))

    if not additions:
        return insight_text

    return insight_text + " | Personalized context -> " + " ; ".join(additions)


def profile_snapshot(profile: UserMemoryProfile) -> UserMemoryProfileResponse:
    topics = sorted((profile.recurring_topics or {}).items(), key=lambda kv: kv[1], reverse=True)
    return UserMemoryProfileResponse(
        user_id=profile.user_id,
        recurring_topics=[k for k, _ in topics[:8]],
        goals=list(profile.goals or [])[-5:],
        patterns={k: int(v) for k, v in (profile.patterns or {}).items()},
        interaction_count=int(profile.interaction_count or 0),
    )


def _compact(text: str, max_len: int = 140) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3].rstrip() + "..."


async def get_personalization_memory(
    db: AsyncSession,
    user_id: str,
    profile: UserMemoryProfile | None = None,
) -> dict:
    local_profile = profile
    if local_profile is None:
        profile_result = await db.execute(select(UserMemoryProfile).where(UserMemoryProfile.user_id == user_id))
        local_profile = profile_result.scalar_one_or_none()

    top_topics: list[str] = []
    remembered_goals: list[str] = []
    if local_profile is not None:
        top_topics = [
            key for key, _ in sorted((local_profile.recurring_topics or {}).items(), key=lambda kv: kv[1], reverse=True)[:3]
        ]
        remembered_goals = [str(g) for g in (local_profile.goals or [])[-3:]]

    active_goals_result = await db.execute(
        select(GoalRecord)
        .where(GoalRecord.user_id == user_id, GoalRecord.status.in_(["active", "paused"]))
        .order_by(GoalRecord.priority_weight.desc(), GoalRecord.updated_at.desc())
        .limit(3)
    )
    active_goals = [g.title for g in active_goals_result.scalars().all()]

    recent_insights_result = await db.execute(
        select(InsightRecord)
        .where(InsightRecord.user_id == user_id)
        .order_by(InsightRecord.created_at.desc())
        .limit(3)
    )
    recent_insights = [i.question for i in recent_insights_result.scalars().all()]

    recent_actions_result = await db.execute(
        select(ActionRecord, InsightRecord)
        .join(InsightRecord, InsightRecord.id == ActionRecord.insight_id)
        .where(
            InsightRecord.user_id == user_id,
            ActionRecord.status.in_(["pending", "in_progress", "blocked"]),
        )
        .order_by(ActionRecord.updated_at.desc())
        .limit(3)
    )
    recent_actions = [a.action_text for a, _ in recent_actions_result.all()]

    return {
        "top_topics": top_topics,
        "remembered_goals": remembered_goals,
        "active_goals": active_goals,
        "recent_insights": recent_insights,
        "recent_actions": recent_actions,
    }


def personalize_goal_text(title: str, description: str, memory: dict | None = None) -> tuple[str, str]:
    mem = memory or {}
    active_goal = (mem.get("active_goals") or [None])[0]
    top_topic = (mem.get("top_topics") or [None])[0]

    new_title = _compact(title, max_len=110)
    if active_goal and active_goal.lower() not in new_title.lower():
        new_title = _compact(f"{new_title} | Supports: {active_goal}", max_len=120)

    new_description = _compact(description, max_len=220)
    additions: list[str] = []
    if top_topic:
        additions.append(f"recurring focus '{top_topic}'")
    if active_goal:
        additions.append(f"active goal '{_compact(active_goal, 80)}'")

    if additions:
        suffix = " Personalized from memory: " + " and ".join(additions) + "."
        new_description = _compact(new_description + suffix, max_len=260)

    return new_title, new_description


def personalize_action_plan_with_memory(actions: list[str], memory: dict | None = None) -> list[str]:
    mem = memory or {}
    anchor_goal = (mem.get("active_goals") or mem.get("remembered_goals") or [None])[0]
    anchor_action = (mem.get("recent_actions") or [None])[0]

    if not anchor_goal and not anchor_action:
        return actions

    personalized: list[str] = []
    for idx, step in enumerate(actions[:3]):
        text = _compact(step, max_len=220)
        if idx == 0 and anchor_goal and anchor_goal.lower() not in text.lower():
            text = _compact(f"{text} Keep this aligned with active goal '{anchor_goal}'.", max_len=245)
        elif idx == 1 and anchor_action and anchor_action.lower() not in text.lower():
            text = _compact(f"{text} Reuse momentum from recent action '{anchor_action}'.", max_len=245)
        personalized.append(text)

    return personalized


def build_priority_context(intent: str, memory: dict | None = None) -> str:
    mem = memory or {}
    parts = [_compact(intent, max_len=120)]

    active_goal = (mem.get("active_goals") or [None])[0]
    recent_action = (mem.get("recent_actions") or [None])[0]
    recent_insight = (mem.get("recent_insights") or [None])[0]

    if active_goal:
        parts.append(f"active goal: {_compact(active_goal, 70)}")
    if recent_action:
        parts.append(f"recent action: {_compact(recent_action, 70)}")
    elif recent_insight:
        parts.append(f"recent intent: {_compact(recent_insight, 70)}")

    return _compact(" | ".join([p for p in parts if p]), max_len=230)
