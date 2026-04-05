from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    document_id: UUID
    filename: str
    status: str
    task_id: str


class SourceItem(BaseModel):
    document_id: UUID
    filename: str
    chunk_index: int
    score: float
    excerpt: str


class AuthRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern="^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=128)


class AuthLoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class AuthUserResponse(BaseModel):
    user_id: str
    username: str
    display_name: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: AuthUserResponse


class AuthLogoutResponse(BaseModel):
    revoked: bool


class AuthProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=128)


class AuthPasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class Insight(BaseModel):
    insight_id: UUID | None = None
    generated_text: str | None = None
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    retrieval_notes: str
    recommended_next_question: str | None = None


class RAGChatRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)
    user_id: str = Field(default="default")


class UserMemoryProfileResponse(BaseModel):
    user_id: str
    recurring_topics: list[str]
    goals: list[str]
    patterns: dict[str, int]
    interaction_count: int


class PlanningQualityResponse(BaseModel):
    action_plan_scores: list[float] = Field(default_factory=list)
    action_plan_average: float | None = Field(default=None, ge=0.0, le=1.0)
    priority_score: float | None = Field(default=None, ge=0.0, le=1.0)
    goal_title_score: float | None = Field(default=None, ge=0.0, le=1.0)
    goal_description_score: float | None = Field(default=None, ge=0.0, le=1.0)


class RAGChatResponse(BaseModel):
    sources: list[SourceItem]
    insight: Insight
    action_plan: list[str] = Field(default_factory=list, min_length=0, max_length=3)
    next_likely_priority: str | None = None
    planning_quality: PlanningQualityResponse | None = None
    user_profile: UserMemoryProfileResponse | None = None
    raw_context: list[dict[str, Any]]


class ActionStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(pending|in_progress|completed|blocked)$")
    note: str | None = None


class ActionResponse(BaseModel):
    action_id: UUID
    insight_id: UUID
    goal_id: UUID | None = None
    step_number: int
    action_text: str
    status: str
    score: float
    completed_at: datetime | None = None
    updated_at: datetime


class ProgressHistoryItem(BaseModel):
    history_id: UUID
    action_id: UUID
    previous_status: str | None = None
    new_status: str
    note: str | None = None
    created_at: datetime


class InsightProgressResponse(BaseModel):
    insight_id: UUID
    progress_percent: float
    total_actions: int
    completed_actions: int
    actions: list[ActionResponse]
    history: list[ProgressHistoryItem]


class BriefInsightItem(BaseModel):
    insight_id: UUID
    question: str
    insight_text: str
    score: float
    created_at: datetime


class BriefActionItem(BaseModel):
    action_id: UUID
    insight_id: UUID
    step_number: int
    action_text: str
    status: str
    score: float
    completed_at: datetime | None = None


class GoalCreateRequest(BaseModel):
    user_id: str = Field(default="default")
    title: str
    description: str | None = None
    priority_weight: float = Field(default=1.0, ge=0.1, le=3.0)
    target_date: date | None = None


class GoalUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(active|paused|completed|archived)$")
    progress_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    priority_weight: float | None = Field(default=None, ge=0.1, le=3.0)
    target_date: date | None = None
    note: str | None = None


class GoalResponse(BaseModel):
    goal_id: UUID
    user_id: str
    title: str
    description: str | None = None
    status: str
    progress_percent: float
    priority_weight: float
    target_date: date | None = None
    created_at: datetime
    updated_at: datetime


class GoalHistoryItem(BaseModel):
    history_id: UUID
    goal_id: UUID
    previous_status: str | None = None
    new_status: str
    previous_progress: float | None = None
    new_progress: float
    note: str | None = None
    created_at: datetime


class GoalMilestoneCreateRequest(BaseModel):
    title: str
    target_percent: float = Field(ge=0.0, le=100.0)


class GoalMilestoneResponse(BaseModel):
    milestone_id: UUID
    goal_id: UUID
    user_id: str
    title: str
    target_percent: float
    achieved_at: datetime | None = None
    created_at: datetime


class GoalProgressDetailResponse(BaseModel):
    goal: GoalResponse
    linked_actions: list[ActionResponse]
    milestones: list[GoalMilestoneResponse]
    completion_percent: float
    total_linked_actions: int
    completed_linked_actions: int


class GoalActionLinkResponse(BaseModel):
    linked: bool
    goal_id: UUID
    action_id: UUID


class GoalFrontendStatusResponse(BaseModel):
    goal: GoalResponse
    progress_percent: float
    urgency_level: str
    priority_status: str
    next_step: str
    next_milestone: GoalMilestoneResponse | None = None
    milestones: list[GoalMilestoneResponse] = Field(default_factory=list)
    total_linked_actions: int
    completed_linked_actions: int


class DashboardPriorityStatus(BaseModel):
    text: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    urgency_level: str


class DashboardActionItem(BaseModel):
    action_id: UUID
    insight_id: UUID
    goal_id: UUID | None = None
    step_number: int
    action_text: str
    status: str
    score: float
    updated_at: datetime


class DashboardActionProgress(BaseModel):
    total: int = 0
    completed: int = 0
    pending: int = 0
    completion_percent: float = Field(default=0.0, ge=0.0, le=100.0)


class DashboardInsightItem(BaseModel):
    insight_id: UUID
    question: str
    insight_text: str
    score: float
    created_at: datetime


class HomepageDashboardResponse(BaseModel):
    user_id: str
    generated_at: datetime
    top_goals: list[GoalFrontendStatusResponse] = Field(default_factory=list)
    todays_priority: DashboardPriorityStatus
    active_actions: list[DashboardActionItem] = Field(default_factory=list)
    completed_actions: list[DashboardActionItem] = Field(default_factory=list)
    action_progress: DashboardActionProgress = Field(default_factory=DashboardActionProgress)
    latest_insights: list[DashboardInsightItem] = Field(default_factory=list)


class DailyBriefResponse(BaseModel):
    brief_date: str
    summary: str
    next_likely_priority: str | None = None
    top_insights: list[BriefInsightItem]
    completed_actions: list[BriefActionItem]
    remaining_priorities: list[BriefActionItem]
    active_goals: list[GoalResponse] = Field(default_factory=list)


class NotificationResponse(BaseModel):
    notification_id: UUID
    user_id: str
    priority_text: str
    confidence: float
    status: str
    source: str
    effective_threshold: float | None = None
    created_at: datetime


class NotificationStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(new|read|accept|accepted|ignore|ignored|dismiss|dismissed)$")


class HomepageHighlightsResponse(BaseModel):
    user_id: str
    generated_at: datetime
    highlights: list[NotificationResponse]


class DocumentStatusResponse(BaseModel):
    document_id: UUID
    status: str
    filename: str
    content_type: str
    created_at: datetime
