from fastapi import APIRouter, Depends, HTTPException
import httpx

from app.schemas import ChatRequest, ChatResponse
from app.services.intent_router import detect_route
from app.services.weather_service import WeatherService
from app.services.news_service import NewsService
from app.services.openai_service import OpenAIService
from app.core.http import build_async_client

router = APIRouter()


async def get_http_client():
    async with build_async_client() as client:
        yield client


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
):
    try:
        msg = request.message.lower()

        # WEATHER FIRST
        if any(k in msg for k in ["weather", "temperature", "forecast"]):
            result = await WeatherService(http_client).handle(request)
            route = "weather"
        # NEWS SECOND (smarter detection)
        elif any(k in msg for k in [
            "news",
            "headline",
            "headlines",
            "latest",
            "breaking",
            "today",
            "current",
            "happening",
            "update"
        ]):
            result = await NewsService(http_client).handle(request)
            route = "news"
        # ONLY fallback to AI
        else:
            result = await OpenAIService().handle(request)
            route = "general"

        return ChatResponse(route=route, answer=result["answer"])

    except httpx.HTTPStatusError:
        raise HTTPException(status_code=502, detail="Upstream service error")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))