print("CHAT ROUTER FILE LOADED")
from fastapi import APIRouter
from pydantic import BaseModel

# import your core chat logic (this must exist)
from backend.app.services.intent_router import chat

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        # Debug print before calling weather service
        print("CALLING WEATHER SERVICE")
        result = chat(req.message)

        # Enforce single weather pipeline
        if isinstance(result, dict) and result.get("type") == "weather":
            weather = result.get("weather", result)
            print("FINAL WEATHER OBJECT:", weather)
            from backend.app.services.response_style import format_weather_reply
            return format_weather_reply(weather)

        return result

    except Exception as e:
        return {
            "error": "chat_failed",
            "detail": str(e)
        }