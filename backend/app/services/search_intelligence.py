from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
import re


KNOWN_SOURCE_BOOSTS = {
    "reuters.com": 3.0,
    "apnews.com": 3.0,
    "bbc.com": 2.5,
    "nytimes.com": 2.0,
    "wikipedia.org": 2.0,
    "github.com": 2.0,
    "developer.mozilla.org": 2.5,
    "docs.python.org": 2.5,
    "openai.com": 2.5,
    "microsoft.com": 2.0,
    "support.google.com": 2.0,
}


def normalize_and_rank_results(query: str, raw_results: list[dict[str, Any]] | None, intent: str) -> list[dict[str, Any]]:
    cleaned_query = (query or "").strip()
    normalized_results: list[dict[str, Any]] = []

    for item in raw_results or []:
        if not isinstance(item, dict):
            continue

        url = str(item.get("url") or item.get("link") or "").strip()
        title = str(item.get("title") or item.get("headline") or "").strip()
        snippet = str(item.get("snippet") or item.get("description") or item.get("summary") or "").strip()
        source = str(item.get("source") or _domain_from_url(url) or "Unknown source").strip()
        date = str(item.get("date") or item.get("publishedAt") or item.get("published_at") or "").strip()

        if not url or not title:
            continue

        score, signals = _score_result(cleaned_query, title, snippet, url, date)
        normalized_results.append(
            {
                "title": title,
                "url": url,
                "link": url,
                "snippet": snippet,
                "source": source,
                "date": date,
                "score": score,
                "why": _build_why(cleaned_query, title, snippet, source, signals, intent),
            }
        )

    normalized_results.sort(key=lambda item: item.get("score", 0), reverse=True)

    for index, item in enumerate(normalized_results, start=1):
        item["rank"] = index

    return normalized_results


def build_answer_first_summary(intent: str, query: str, results: list[dict[str, Any]] | None) -> str:
    cleaned_query = (query or "").strip() or "your topic"
    items = results or []

    if not items:
        if intent == "news":
            return f'I could not find strong recent coverage for "{cleaned_query}".'
        return f'I could not find strong results for "{cleaned_query}".'

    top_results = items[:3]
    top_result = top_results[0]
    lead_detail = _clean_sentence(str(top_result.get("snippet") or top_result.get("title") or ""))
    source_names = [str(item.get("source") or "").strip() for item in top_results if str(item.get("source") or "").strip()]
    distinct_sources: list[str] = []
    for source in source_names:
        if source not in distinct_sources:
            distinct_sources.append(source)

    if intent == "news":
        source_text = f" Coverage below is led by {', '.join(distinct_sources[:2])}." if distinct_sources else ""
        if lead_detail:
            return f"The clearest current signal on {cleaned_query} is {lead_detail}.{source_text}".replace("..", ".").strip()
        return f"I found recent coverage for {cleaned_query}.{source_text}".replace("..", ".").strip()

    if lead_detail:
        return (
            f"The strongest results for {cleaned_query} point to {lead_detail}. "
            "The ranked sources below add supporting detail."
        ).strip()

    return f"I found several relevant results for {cleaned_query}. The ranked sources below provide the supporting detail."


def _score_result(query: str, title: str, snippet: str, url: str, date: str) -> tuple[float, dict[str, bool]]:
    lowered_query = query.lower()
    lowered_title = title.lower()
    lowered_snippet = snippet.lower()
    terms = _extract_terms(lowered_query)
    title_term_matches = sum(1 for term in terms if term in lowered_title)
    snippet_term_matches = sum(1 for term in terms if term in lowered_snippet)
    exact_phrase_match = bool(lowered_query and (lowered_query in lowered_title or lowered_query in lowered_snippet))
    source_boost = _source_boost(url)
    recency_boost = _recency_boost(date)

    score = 0.0
    score += title_term_matches * 3.0
    score += snippet_term_matches * 1.5
    score += source_boost
    score += recency_boost

    if exact_phrase_match:
      score += 4.0

    return score, {
        "title_match": title_term_matches > 0,
        "snippet_match": snippet_term_matches > 0,
        "source_boost": source_boost > 0,
        "recent": recency_boost > 0,
        "exact_phrase": exact_phrase_match,
    }


def _build_why(query: str, title: str, snippet: str, source: str, signals: dict[str, bool], intent: str) -> str:
    cleaned_query = (query or "").strip() or "your query"

    if signals.get("exact_phrase"):
        return f"Relevant because it directly matches the phrasing of {cleaned_query}."
    if signals.get("title_match"):
        return f"Relevant because the title directly addresses {cleaned_query}."
    if signals.get("snippet_match"):
        return f"Relevant because the snippet explicitly discusses {cleaned_query}."
    if intent == "news" and signals.get("recent"):
        return "Relevant because it appears recent and adds current context."
    if signals.get("source_boost"):
        return f"Relevant because it comes from {source}, which is usually a stronger source for this kind of topic."
    if snippet:
        return f"Relevant because it adds context on {cleaned_query}."
    return f"Relevant because it appears to cover {cleaned_query}."


def _extract_terms(query: str) -> list[str]:
    return [term for term in re.findall(r"[a-z0-9]+", query) if len(term) > 2]


def _source_boost(url: str) -> float:
    domain = _domain_from_url(url)
    for known_domain, boost in KNOWN_SOURCE_BOOSTS.items():
        if domain == known_domain or domain.endswith(f".{known_domain}"):
            return boost
    return 0.0


def _recency_boost(date_value: str) -> float:
    if not date_value:
        return 0.0

    parsed = _parse_datetime(date_value)
    if not parsed:
        return 0.0

    age = datetime.now(timezone.utc) - parsed
    age_days = age.total_seconds() / 86400
    if age_days < 0:
        return 0.0
    if age_days <= 3:
        return 2.5
    if age_days <= 7:
        return 2.0
    if age_days <= 30:
        return 1.0
    if age_days <= 365:
        return 0.5
    return 0.0


def _parse_datetime(value: str) -> datetime | None:
    cleaned_value = value.strip()
    if not cleaned_value:
        return None

    try:
        normalized = cleaned_value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "").strip().lower()
    except Exception:
        return ""


def _clean_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    return cleaned.rstrip(" .")