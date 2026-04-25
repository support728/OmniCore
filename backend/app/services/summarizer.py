from __future__ import annotations

from typing import Any

from openai import OpenAI

from ..config import get_settings
from .response_style import SUMMARY_SYSTEM_PROMPT, format_conversational_response
from .search_intelligence import build_answer_first_summary


def summarize_results(intent: str, query: str, results: Any) -> str:
    normalized_intent = (intent or "general").strip().lower()
    fallback = _fallback_summary(normalized_intent, query, results)
    payload = _build_summary_payload(normalized_intent, results)

    if not payload:
        return fallback

    try:
        settings = get_settings()
        if not settings.openai_api_key:
            return fallback

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(
            model=settings.openai_model,
            instructions=SUMMARY_SYSTEM_PROMPT,
            input=(
                f"Intent: {normalized_intent}\n"
                f"User query: {query}\n"
                f"Results: {payload}\n"
                "Return only the user-facing summary."
            ),
        )

        output_text = getattr(response, "output_text", None)
        if output_text and output_text.strip():
            return format_conversational_response(output_text)
    except Exception:
        pass

    return format_conversational_response(fallback)


def _build_summary_payload(intent: str, results: Any) -> list[dict[str, Any]]:
    if intent == "weather":
        return _build_weather_payload(results)

    if not isinstance(results, list):
        return []

    payload: list[dict[str, Any]] = []
    for item in results[:5]:
        if not isinstance(item, dict):
            continue

        if intent == "news":
            payload.append(
                {
                    "title": str(item.get("title") or "").strip(),
                    "snippet": str(item.get("snippet") or "").strip(),
                    "source": str(item.get("source") or "").strip(),
                    "date": str(item.get("publishedAt") or item.get("date") or "").strip(),
                }
            )
        else:
            payload.append(
                {
                    "title": str(item.get("title") or "").strip(),
                    "snippet": str(item.get("snippet") or "").strip(),
                    "source": str(item.get("source") or "").strip(),
                }
            )

    return [item for item in payload if any(item.values())]


def _build_weather_payload(results: Any) -> list[dict[str, Any]]:
    if not isinstance(results, dict):
        return []

    payload = [
        {
            "city": str(results.get("city") or "").strip(),
            "country": str(results.get("country") or "").strip(),
            "request_type": str(results.get("request_type") or "current").strip(),
            "temperature": results.get("temperature") if results.get("temperature") is not None else results.get("temp"),
            "description": str(results.get("description") or "").strip(),
        }
    ]

    forecast_days = results.get("forecast_days")
    if isinstance(forecast_days, list):
        for day in forecast_days[:3]:
            if not isinstance(day, dict):
                continue
            payload.append(
                {
                    "label": str(day.get("label") or day.get("date") or "").strip(),
                    "temperature": day.get("temperature"),
                    "description": str(day.get("description") or "").strip(),
                }
            )

    return payload


def _fallback_summary(intent: str, query: str, results: Any) -> str:
    cleaned_query = (query or "").strip() or "your request"

    if intent == "web_search":
        items = results if isinstance(results, list) else []
        return build_answer_first_summary("web_search", cleaned_query, items)

    if intent == "news":
        items = results if isinstance(results, list) else []
        return build_answer_first_summary("news", cleaned_query, items)

    if intent == "weather":
        weather = results if isinstance(results, dict) else {}
        if not weather:
            return f"Weather details for {cleaned_query} are unavailable right now."
        city = str(weather.get("city") or cleaned_query or "that location")
        temperature = weather.get("temperature") if weather.get("temperature") is not None else weather.get("temp")
        description = str(weather.get("description") or "conditions unavailable")
        forecast_days = weather.get("forecast_days") if isinstance(weather.get("forecast_days"), list) else []
        next_step = ""
        if forecast_days:
            next_day = forecast_days[0]
            if isinstance(next_day, dict):
                next_label = str(next_day.get("label") or next_day.get("date") or "next").strip()
                next_desc = str(next_day.get("description") or "conditions").strip()
                next_temp = next_day.get("temperature")
                if next_temp is not None:
                    next_step = f" Expect {next_label} to be around {next_temp}°F with {next_desc}."
                else:
                    next_step = f" Expect {next_label} to bring {next_desc}."
        if temperature is not None:
            return f"{city} is currently {temperature}°F with {description}.{next_step}".strip()
        return f"{city} currently has {description}.{next_step}".strip()

    return f"Here is a concise summary for {cleaned_query}."