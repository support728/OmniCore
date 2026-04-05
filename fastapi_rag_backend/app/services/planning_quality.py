import re


_GENERIC_PHRASES = (
    "do better",
    "improve things",
    "take action",
    "follow up",
    "next steps",
    "create a new action plan",
    "prioritize one high-impact decision",
    "execute and measure outcome",
)

_ACTION_VERBS = {
    "validate",
    "define",
    "assign",
    "schedule",
    "execute",
    "review",
    "measure",
    "deliver",
    "ship",
    "launch",
    "draft",
    "finalize",
    "complete",
}

_INTENT_FILLER_PREFIXES = (
    "can you",
    "could you",
    "please",
    "i want to",
    "i need to",
    "help me",
    "how can i",
    "how do i",
)

_OBJECTIVE_PREFIXES = (
    "we need to",
    "we should",
    "we want to",
    "i need to",
    "i want to",
    "i think we should",
    "can you",
    "please",
)

_VAGUE_PATTERNS = (
    "help",
    "something",
    "anything",
    "stuff",
    "do this",
    "do it",
    "improve",
    "better",
    "optimize",
    "fix it",
)

_EXPLICIT_PLANNING_PATTERNS = (
    r"\bcreate\s+(?:a\s+)?goal\b",
    r"\bcreate\s+goals\b",
    r"\bset\s+(?:a\s+)?priority\b",
    r"\bset\s+priorities\b",
    r"\bwhat\s+should\s+my\s+priority\s+be\b",
    r"\bwhat\s+should\s+our\s+priority\s+be\b",
    r"\bgenerate\s+(?:an\s+)?action(?:\s+plan)?\b",
    r"\bgive\s+me\s+actions\b",
    r"\bgive\s+me\s+an\s+action\s+plan\b",
    r"\bbuild\s+(?:me\s+)?(?:a\s+)?plan\b",
    r"\bgive\s+me\s+(?:a\s+)?plan\b",
    r"\bmake\s+(?:me\s+)?(?:a\s+)?plan\b",
    r"\bhelp\s+me\s+plan\b",
    r"\bplan\s+how\s+to\b",
    r"\bnext\s+steps\b",
    r"\baction\s+plan\b",
    r"\broadmap\b",
    r"\bplan\s+this\b",
    r"\bturn\s+this\s+into\s+(?:a\s+)?plan\b",
    r"\bbreak\s+this\s+down\s+into\s+actions\b",
    r"\bwhat\s+should\s+i\s+do\s+next\b",
    r"\bwhat\s+should\s+we\s+do\s+next\b",
    r"\bwhat\s+should\s+i\s+focus\s+on\s+next\b",
    r"\bwhat\s+should\s+we\s+focus\s+on\s+next\b",
)

_CLEAR_ACTION_VERB_PATTERNS = (
    r"\b(create|build|generate|set|define|prioritize|improve|increase|reduce|fix|optimize|launch|ship|analyze|validate|update|revise|edit|modify|refine|adjust)\b",
)

_CLEAR_OBJECTIVE_PATTERNS = (
    r"\b(plan|goal|priority|action|roadmap|kpi|metric|conversion|onboarding|retention|churn|revenue|pricing|pipeline|latency|performance|funnel|activation|support|ticket)\b",
)

_CLEAR_OUTCOME_PATTERNS = (
    r"\b(\d+(?:\.\d+)?%|today|tomorrow|this week|this month|this quarter|next week|next month|next quarter|deadline|due|baseline|target|kpi|metric)\b",
)

_GOAL_PREFIX_NOISE_PATTERNS = (
    r"^turn\s+this\s+into\s+",
    r"^turn\s+this\s+to\s+",
    r"^make\s+this\s+into\s+",
    r"^make\s+this\s+",
    r"^convert\s+this\s+into\s+",
    r"^plan\s+this\s+for\s+",
    r"^plan\s+this\s+",
    r"^from\s+chat\s*:\s*",
    r"^user\s+intent\s+captured\s*:\s*",
    r"^deliver\s+outcome\s*:\s*",
    r"^target\s+outcome\s*:\s*",
    r"^(?:a\s+)?plan\s*:\s*",
    r"^(?:a\s+)?plan\s+for\s+",
)

_SEMANTIC_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into", "is",
    "it", "of", "on", "or", "that", "the", "this", "to", "with", "your", "our", "my",
    "turn", "make", "create", "plan", "goal", "action", "priority",
}


def _extract_metric_snippet(text: str) -> str | None:
    source = text or ""
    # No trailing \b — % is non-word so \b after it never fires against a space.
    pct_match = re.search(r"\b\d+(?:\.\d+)?%", source)
    if pct_match:
        return pct_match.group(0)
    metric_match = re.search(r"\b\d+(?:\.\d+)?\s*(users?|leads?|sales?|days?|weeks?|hours?)\b", source, flags=re.IGNORECASE)
    if metric_match:
        return metric_match.group(0)
    return None


def _extract_timeframe_hint(text: str) -> str | None:
    source = (text or "").lower()
    explicit = re.search(
        r"\b(today|tomorrow|this week|this month|this quarter|this year|next week|next month|next quarter)\b",
        source,
        flags=re.IGNORECASE,
    )
    if explicit:
        return explicit.group(1)

    by_clause = re.search(r"\bby\s+([a-z0-9\-\s]{2,24})\b", source, flags=re.IGNORECASE)
    if by_clause:
        captured = by_clause.group(1).strip()
        # Skip bare numbers — they are percentage values, not timeframes (e.g. "by 20" from "by 20%")
        if not re.match(r"^\d+$", captured):
            return f"by {captured}"

    # Catch "in N days / in 30 days" style clauses
    in_clause = re.search(r"\bin\s+(\d+\s*(?:days?|weeks?|months?))\b", source, flags=re.IGNORECASE)
    if in_clause:
        return in_clause.group(1).strip()

    # Catch "before end of month/quarter/week/year"
    before_clause = re.search(
        r"\bbefore\s+(end\s+of\s+(?:the\s+)?(?:week|month|quarter|year)|(?:end\s+of\s+)?\w+\s+\d{1,2}(?:st|nd|rd|th)?)",
        source, flags=re.IGNORECASE,
    )
    if before_clause:
        return f"before {before_clause.group(1).strip()}"

    return None


def _measurable_goal_outcome(source_text: str) -> str:
    lowered = (source_text or "").lower()
    metric_hint = _extract_metric_snippet(lowered) or "15%"
    timeframe = _extract_timeframe_hint(lowered) or "this quarter"

    if re.search(r"\b(churn|retention|renewal)\b", lowered):
        objective = "Increase customer retention rate"
    elif re.search(r"\b(revenue|sales|pipeline|arr|mrr)\b", lowered):
        objective = "Increase qualified pipeline revenue"
    elif re.search(r"\b(pricing|pricing\s+page|monetiz)\b", lowered):
        # Milestone goal — prefer deadline over percentage.
        if timeframe:
            tf = timeframe if timeframe.startswith(("by ", "before ")) else f"in {timeframe}"
            return f"Ship updated pricing page {tf} and capture day-1 conversion baseline"
        return "Ship updated pricing page this month and capture day-1 conversion baseline"
    elif re.search(r"\b(onboarding|conversion|signup|activation)\b", lowered):
        objective = "Increase onboarding conversion rate"
    elif re.search(r"\b(growth|grow|acquisition|new\s*customer)\b", lowered):
        objective = "Increase user acquisition rate"
    elif re.search(r"\b(engagement|adoption|usage|dau|mau)\b", lowered):
        objective = "Increase product activation rate"
    elif re.search(r"\b(support|ticket|resolution|sla)\b", lowered):
        objective = "Reduce average support resolution time"
    elif re.search(r"\b(latency|speed|performance|load\s*time|slow|faster|fast)\b", lowered):
        objective = "Reduce median page load time"
    elif re.search(r"\b(launch|ship|go\s*live|release)\b", lowered):
        # Milestone goals don't need a percentage target — use timeframe only.
        timeframe_str = timeframe if timeframe.startswith(("by ", "before ")) else f"in {timeframe}"
        return f"Ship the planned deliverable {timeframe_str}".strip()
    elif re.search(r"\b(deals?|win\s*rate|losing\s*deals?|close\s*rate)\b", lowered):
        objective = "Increase deal win rate"
    else:
        objective = "Increase primary KPI conversion rate"

    # Avoid "in by N" — when timeframe already contains "by", omit the "in" prefix.
    timeframe_str = timeframe if timeframe.startswith(("by ", "before ")) else f"in {timeframe}"
    return f"{objective} by {metric_hint} {timeframe_str}".strip()


def interpret_business_objective(text: str | None) -> str:
    """
    Convert raw user phrasing into a measurable business objective.
    This is a required pre-generation transformation step.
    """
    source = canonical_goal_text(text or "")
    lowered = source.lower().strip()

    for prefix in _OBJECTIVE_PREFIXES:
        if lowered.startswith(prefix + " "):
            source = source[len(prefix):].strip(" :,-")
            lowered = source.lower().strip()
            break

    source = re.sub(r"\b(?:we|i)\s+need\s+to\b", "", source, flags=re.IGNORECASE).strip(" :,-")
    source = re.sub(r"\b(?:this|it)\s+is\s+not\s+a\s+chatbot\b", "", source, flags=re.IGNORECASE).strip(" :,-")
    source = re.sub(r"\bthis\s+is\s+a\b", "", source, flags=re.IGNORECASE).strip(" :,-")
    source = re.sub(r"\s+", " ", source).strip()
    lowered = source.lower()

    if re.search(r"\bchatbot\b", lowered) and re.search(r"\bdecision\s+engine\b", lowered):
        return "Increase product-site conversion by 15% this quarter by positioning the product as a decision engine"

    return _measurable_goal_outcome(source)


def resembles_input_phrasing(goal_text: str, raw_input: str) -> bool:
    """Guard: detect when generated goal still mirrors user phrasing too closely."""
    goal_key = semantic_text_key(goal_text)
    input_key = semantic_text_key(raw_input)
    if not goal_key or not input_key:
        return False

    goal_tokens = set(goal_key.split())
    input_tokens = set(input_key.split())
    if not goal_tokens or not input_tokens:
        return False

    overlap = len(goal_tokens & input_tokens)
    overlap_ratio = overlap / max(1, min(len(goal_tokens), len(input_tokens)))
    # High overlap with no explicit measurable signal usually means echoing input.
    has_metric = bool(re.search(r"\b\d+(?:\.\d+)?%\b", goal_text))
    return overlap_ratio >= 0.75 and not has_metric


def _compact(text: str, max_len: int = 120) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3].rstrip() + "..."


def _remove_repeated_segments(text: str) -> str:
    cleaned = _compact(text or "", max_len=240)
    if not cleaned:
        return ""

    parts = [p.strip(" .;:-") for p in re.split(r"[.;]+", cleaned) if p.strip()]
    if not parts:
        return cleaned

    seen: set[str] = set()
    unique_parts: list[str] = []
    for part in parts:
        key = re.sub(r"[^a-z0-9]+", " ", part.lower()).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        unique_parts.append(part)

    if not unique_parts:
        return cleaned
    return "; ".join(unique_parts)


def canonical_goal_text(text: str | None) -> str:
    cleaned = _remove_repeated_segments(text or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" \t\n\r:;,.\"'")
    lowered = cleaned.lower()

    changed = True
    while changed and lowered:
        changed = False
        for pattern in _GOAL_PREFIX_NOISE_PATTERNS:
            if re.match(pattern, lowered):
                cleaned = re.sub(pattern, "", cleaned, count=1, flags=re.IGNORECASE).strip(" \t\n\r:;,.\"'")
                lowered = cleaned.lower()
                changed = True

    # Collapse repetitive "this is ..." scaffolding into concise phrasing.
    cleaned = re.sub(r"\bthis\s+is\s+a\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bthis\s+is\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*,\s*", ", ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" \t\n\r:;,.\"'")

    return _compact(cleaned, max_len=140)


def semantic_text_key(text: str | None) -> str:
    canonical = canonical_goal_text(text).lower()
    tokens = re.findall(r"[a-z0-9]+", canonical)
    meaningful = [t for t in tokens if t not in _SEMANTIC_STOPWORDS and len(t) > 2]
    if not meaningful:
        return canonical
    return " ".join(sorted(set(meaningful))[:12])


def _action_key(text: str) -> str:
    lowered = _remove_repeated_segments(text).lower()
    lowered = re.sub(r"\b(the|a|an|to|for|and|with|within|next|one|your)\b", " ", lowered)
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def extract_user_intent(text: str) -> str:
    source = _compact(text or "", max_len=220)
    if not source:
        return "NO_INTENT"

    lowered = source.lower().strip()
    for prefix in _INTENT_FILLER_PREFIXES:
        if lowered.startswith(prefix + " "):
            source = source[len(prefix):].strip(" :,-")
            break

    source = re.sub(r"\b(user intent captured|from chat)\s*:\s*", "", source, flags=re.IGNORECASE)
    source = re.sub(r"\s+", " ", source).strip()

    canonical = canonical_goal_text(source)
    canonical_lower = canonical.lower()
    tokens = re.findall(r"[a-z0-9]+", canonical_lower)
    actionable = any(re.search(p, canonical_lower) for p in _CLEAR_ACTION_VERB_PATTERNS)
    objective = any(re.search(p, canonical_lower) for p in _CLEAR_OBJECTIVE_PATTERNS)
    outcome = any(re.search(p, canonical_lower) for p in _CLEAR_OUTCOME_PATTERNS)
    planning_phrase = any(re.search(p, canonical_lower) for p in _EXPLICIT_PLANNING_PATTERNS)

    if not canonical or len(tokens) < 4:
        return "NO_INTENT"
    if not (actionable and objective and (outcome or planning_phrase or len(tokens) >= 10)):
        return "NO_INTENT"

    return canonical


def is_vague_input(text: str) -> bool:
    intent = extract_user_intent(text)
    if intent == "NO_INTENT":
        return True
    lowered = intent.lower()
    words = re.findall(r"[a-z0-9]+", lowered)

    if len(words) < 4:
        return True

    if any(lowered == token or lowered.startswith(token + " ") for token in ("hi", "hello", "hey")):
        return True

    has_metric = bool(re.search(r"\b\d+(?:\.\d+)?%\b", lowered))
    has_timeframe = bool(re.search(r"\b(today|tomorrow|this week|this month|this quarter|by\b|deadline|due)\b", lowered))
    has_object = len([w for w in words if len(w) >= 4]) >= 2

    vague_hit = any(pattern in lowered for pattern in _VAGUE_PATTERNS)
    if vague_hit and not (has_metric or has_timeframe):
        return True

    if not has_object:
        return True

    return False


def build_clarifying_question(text: str) -> str:
    intent = extract_user_intent(text)
    if not intent or intent == "NO_INTENT":
        return "What specific outcome do you want to achieve, by when, and how will you measure success?"

    return (
        f"To make this actionable, what exact outcome do you want for '{_compact(intent, 80)}', "
        "what is the deadline, and which KPI should we optimize?"
    )


def is_explicit_planning_request(text: str) -> bool:
    intent = extract_user_intent(text)
    if intent == "NO_INTENT":
        return False
    lowered = intent.lower().strip()
    if not lowered:
        return False

    return any(re.search(pattern, lowered) for pattern in _EXPLICIT_PLANNING_PATTERNS)


def planning_quality_score(text: str) -> float:
    lowered = (text or "").lower().strip()
    if not lowered:
        return 0.0

    words = re.findall(r"[a-z0-9]+", lowered)
    has_action = any(w in _ACTION_VERBS for w in words)
    has_owner = any(x in lowered for x in ("owner", "assign", "team", "lead"))
    has_time = bool(
        re.search(r"\b\d+\s*(hour|day|week|month|quarter)s?\b", lowered)
        or re.search(r"\b(today|tomorrow|this week|this month|by\b|deadline|due)\b", lowered)
    )
    has_metric = bool(
        re.search(r"\b\d+(\.\d+)?%\b", lowered)
        or re.search(r"\b(kpi|metric|measure|baseline|before/after|success criteria)\b", lowered)
    )
    generic_hits = sum(1 for phrase in _GENERIC_PHRASES if phrase in lowered)

    score = 0.0
    score += 0.2 if len(words) >= 8 else 0.0
    score += 0.2 if has_action else 0.0
    score += 0.2 if has_owner else 0.0
    score += 0.2 if has_time else 0.0
    score += 0.2 if has_metric else 0.0
    score -= min(0.4, 0.2 * generic_hits)

    return max(0.0, min(1.0, round(score, 4)))


def normalize_priority_text(text: str | None, context: str | None = None) -> str:
    source = _compact((context or "").strip() or (text or "").strip() or "the current priority", max_len=110)
    candidate = _compact(_remove_repeated_segments((text or "").strip()), max_len=140)
    metric_hint = _extract_metric_snippet(source)
    source_tokens = set(semantic_text_key(source).split())
    candidate_tokens = set(semantic_text_key(candidate).split())
    overlap = len(source_tokens & candidate_tokens)
    related_to_context = overlap >= 2 or (overlap >= 1 and len(source_tokens) <= 3)

    if planning_quality_score(candidate) >= 0.65 and related_to_context:
        return candidate

    lowered = source.lower()
    timeframe = _extract_timeframe_hint(source)
    # Avoid "by before end of month" — when timeframe already starts with by/before, use it directly.
    if timeframe:
        if timeframe.startswith(("by ", "before ")):
            timeframe_clause = f" {timeframe}"
        else:
            timeframe_clause = f" by {timeframe}"
    else:
        timeframe_clause = " within 14 days"
    metric_clause = f" toward {metric_hint}" if metric_hint else " with measurable impact"

    # Check pricing and launch first — their goal titles often contain "conversion" as a side-word.
    if re.search(r"\b(pricing|pricing\s+page|monetiz)\b", lowered):
        return f"Finalize pricing page copy and structure{timeframe_clause}."
    elif re.search(r"\b(launch|ship|go\s*live|release|deadline)\b", lowered):
        return f"Clear all blockers for on-time delivery{timeframe_clause}."
    elif re.search(r"\b(onboarding|conversion|signup|activation|funnel)\b", lowered):
        return f"Identify the step with the highest drop-off and fix it{metric_clause}{timeframe_clause}."
    elif re.search(r"\b(revenue|sales|pipeline|arr|mrr)\b", lowered):
        return f"Shift effort to the revenue lever with the fastest payback, then confirm uplift{metric_clause}{timeframe_clause}."
    elif re.search(r"\b(retention|churn|renewal)\b", lowered):
        return f"Address the highest churn-risk segment before expansion work, and track retention change{metric_clause}{timeframe_clause}."
    elif re.search(r"\b(growth|grow|acquisition|new\s*customer)\b", lowered):
        return f"Identify the highest-performing acquisition channel and double down{metric_clause}{timeframe_clause}."
    elif re.search(r"\b(support|ticket|sla|resolution)\b", lowered):
        return f"Target the support stage causing the longest delays, then measure cycle-time reduction{timeframe_clause}."
    elif re.search(r"\b(latency|performance|load|speed|slow|fast)\b", lowered):
        return f"Fix the slowest customer-critical flow first, then record improvement{metric_clause}{timeframe_clause}."
    elif re.search(r"\b(deals?|win\s*rate|close\s*rate)\b", lowered):
        return f"Identify the top deal-blocker and build a targeted response this week."
    else:
        return f"Resolve the constraint most likely to move the KPI baseline{metric_clause}{timeframe_clause}."


def normalize_goal_title(title: str | None, question: str | None = None) -> str:
    candidate = _compact(canonical_goal_text((title or "").strip()), max_len=80)
    source = _compact(canonical_goal_text((question or "").strip()), max_len=90)
    metric_hint = _extract_metric_snippet(source)
    source_is_vague = is_vague_input(source) if source else False

    if candidate and planning_quality_score(candidate) >= 0.45 and not candidate.lower().startswith("from chat") and not source_is_vague:
        return candidate
    if source_is_vague:
        return _compact(_measurable_goal_outcome(source), max_len=80)
    if source.endswith("?"):
        source = source[:-1].rstrip()
    if source:
        if metric_hint:
            return f"{source} ({metric_hint} target)"
        return source
    return "Define the next concrete objective"


def normalize_goal_description(description: str | None, question: str | None = None) -> str:
    candidate = _compact(_remove_repeated_segments(canonical_goal_text((description or "").strip())), max_len=180)
    source = _compact(canonical_goal_text((question or "").strip()), max_len=180)
    metric_hint = _extract_metric_snippet(source)
    source_is_vague = is_vague_input(source) if source else False

    if candidate and planning_quality_score(candidate) >= 0.5 and not source_is_vague:
        return candidate
    if source_is_vague:
        outcome = _measurable_goal_outcome(source)
        return (
            f"Establish the current baseline this week and deliver {outcome.lower()}. "
            "Track progress in a weekly KPI review."
        )
    if source:
        return f"{source} ({metric_hint} target)" if metric_hint else source
    return "Define one specific outcome and one measurable KPI."


def normalize_action_plan(actions: list[str], focus: str) -> list[str]:
    normalized: list[str] = []
    seen_keys: set[str] = set()
    focus_text = _compact((focus or "").strip() or "the highest-impact workstream", max_len=100)
    fallbacks = [
        f"Validate '{focus_text}' with 2 sources, assign an owner, and log one confirmed fact by end of day.",
        f"Pick one decision for '{focus_text}', assign a driver, and commit a due date within 72 hours.",
        f"Execute the decision for '{focus_text}' and record one before/after KPI for the next review.",
        f"Share a one-paragraph update on '{focus_text}' and list one blocker plus one next move.",
        f"Review KPI trend for '{focus_text}' and choose one adjustment to ship this week.",
    ]

    def add_unique(candidate_text: str) -> None:
        candidate_text = _compact(_remove_repeated_segments(candidate_text), max_len=140)
        if not candidate_text:
            return
        key = _action_key(candidate_text)
        if not key or key in seen_keys:
            return
        seen_keys.add(key)
        normalized.append(candidate_text)

    for idx, item in enumerate((actions or [])[:3]):
        candidate = _compact(_remove_repeated_segments(str(item)), max_len=180)
        if planning_quality_score(candidate) < 0.65:
            add_unique(fallbacks[idx])
        else:
            add_unique(candidate)

    fallback_index = 0
    while len(normalized) < 3 and fallback_index < len(fallbacks):
        add_unique(fallbacks[fallback_index])
        fallback_index += 1

    while len(normalized) < 3:
        normalized.append(f"Execute step {len(normalized) + 1} for '{focus_text}' and report progress in one sentence.")

    return normalized
