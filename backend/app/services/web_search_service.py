from __future__ import annotations

from typing import Any

import requests
from openai import OpenAI

from ..config import get_settings
from .search_intelligence import build_answer_first_summary, normalize_and_rank_results


SEARCH_SYSTEM_PROMPT = """
You are OmniCore global web search.

Your job:
- Search the public web globally and answer with current, practical information.
- Prefer recent, broadly useful information over narrow local snippets unless the user asked for a location.
- Give a direct answer first.
- Then include exactly 3 high-value source links.
- Keep the answer compact and easy to scan.
- If the question is simple and stable, answer it directly in one sentence before listing sources.
- If the topic is current or changing, summarize only the most important updates.
- Do not invent facts or sources.

Required format:
Answer: <2-4 short sentences>

Sources:
1. <title> - <url>
2. <title> - <url>
3. <title> - <url>
""".strip()


SEARCH_RESULTS_SUMMARY_PROMPT = """
You summarize web search results for OmniCore.

Your job:
- Read the top search results and produce a short overview.
- Keep it to 2 sentences maximum.
- Focus on the common thread and the most useful takeaway.
- Do not mention that you are an AI.
- Do not invent details that are not present in the results.
""".strip()


def _mock_results(query: str) -> list[dict[str, str]]:
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    return [
        {
            "title": f"Search results for {cleaned_query}",
            "link": f"https://duckduckgo.com/?q={requests.utils.quote(cleaned_query)}",
            "url": f"https://duckduckgo.com/?q={requests.utils.quote(cleaned_query)}",
            "snippet": f"Live search is unavailable right now, so OmniCore returned a fallback result for \"{cleaned_query}\".",
        }
    ]


def _append_result(results: list[dict[str, str]], title: str, link: str, snippet: str):
    clean_title = (title or "").strip()
    clean_link = (link or "").strip()
    clean_snippet = (snippet or "").strip()
    if not clean_title or not clean_link:
        return

    if any(existing["link"] == clean_link for existing in results):
        return

    results.append(
        {
            "title": clean_title,
            "link": clean_link,
            "url": clean_link,
            "snippet": clean_snippet or f"Search result for {clean_title}.",
        }
    )


def _extract_related_topics(items: list[dict[str, Any]], results: list[dict[str, str]]):
    for item in items:
        if len(results) >= 5:
            return

        nested_topics = item.get("Topics")
        if isinstance(nested_topics, list):
            _extract_related_topics(nested_topics, results)
            continue

        text = str(item.get("Text") or "").strip()
        link = str(item.get("FirstURL") or "").strip()
        if not text or not link:
            continue

        title, _, snippet = text.partition(" - ")
        _append_result(results, title or text, link, snippet or text)


def _fallback_search_results_summary(query: str, results: list[dict[str, str]]) -> str:
    return build_answer_first_summary("web_search", query, results)


def _extract_serpapi_results(payload: dict[str, Any]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    for item in payload.get("organic_results", [])[:5]:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title") or "").strip()
        url = str(item.get("link") or "").strip()
        rich_snippet = item.get("rich_snippet")
        rich_top = rich_snippet.get("top", {}) if isinstance(rich_snippet, dict) else {}
        extensions = rich_top.get("extensions", []) if isinstance(rich_top, dict) else []
        fallback_extension = str(extensions[0]).strip() if isinstance(extensions, list) and extensions else ""
        snippet = str(item.get("snippet") or fallback_extension).strip()

        if not title or not url:
            continue

        results.append(
            {
                "title": title,
                "link": url,
                "url": url,
                "snippet": snippet,
            }
        )

    return results


def search_web(query: str) -> dict[str, object]:
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return {
            "summary": "Please enter something to search for.",
            "results": [],
        }

    settings = get_settings()
    serp_api_key = (settings.serpapi_api_key or "").strip()
    if not serp_api_key:
        fallback_results = _mock_results(cleaned_query)
        return {
            "summary": _fallback_search_results_summary(cleaned_query, fallback_results),
            "results": fallback_results,
        }

    try:
        response = requests.get(
            "https://serpapi.com/search.json",
            params={
                "q": cleaned_query,
                "api_key": serp_api_key,
                "engine": "google",
            },
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        fallback_results = _mock_results(cleaned_query)
        return {
            "summary": _fallback_search_results_summary(cleaned_query, fallback_results),
            "results": fallback_results,
        }

    results = _extract_serpapi_results(payload)
    if not results:
        results = _mock_results(cleaned_query)

    ranked_results = normalize_and_rank_results(cleaned_query, results, "web_search")

    return {
        "summary": _fallback_search_results_summary(cleaned_query, ranked_results),
        "results": ranked_results,
    }


def search_web_results(query: str) -> list[dict[str, str]]:
    payload = search_web(query)
    results = payload.get("results") if isinstance(payload, dict) else []
    return results if isinstance(results, list) else []


def summarize_search_results(query: str, results: list[dict[str, str]]) -> str:
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return ""

    if not results:
        return _fallback_search_results_summary(cleaned_query, results)

    try:
        settings = get_settings()
        if not settings.openai_api_key:
            return _fallback_search_results_summary(cleaned_query, results)

        client = OpenAI(api_key=settings.openai_api_key)
        top_results = [
            {
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", ""),
                "why": result.get("why", ""),
                "source": result.get("source", ""),
            }
            for result in results[:5]
        ]

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=SEARCH_RESULTS_SUMMARY_PROMPT,
            input=(
                f"Query: {cleaned_query}\n"
                f"Top results: {top_results}\n"
                "Write a concise summary for the user."
            ),
        )

        output_text = getattr(response, "output_text", None)
        if output_text and output_text.strip():
            return output_text.strip()
    except Exception:
        pass

    return _fallback_search_results_summary(cleaned_query, results)