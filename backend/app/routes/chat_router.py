// MOVED TO backend/app/chat_router.py
from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.intent_router import chat
from backend.app.services.response_style import format_weather_reply
import logging


router = APIRouter()
logger = logging.getLogger("chat_router")

class ChatRequest(BaseModel):
	message: str

from datetime import datetime


# Cleanup Step 1: Remove hardcoded city logic from /api/chat weather path
import re
def extract_city_from_message(message: str) -> str:
	if not message:
		return "London"
	match = re.search(r"weather in ([a-zA-Z ]+)", message, re.IGNORECASE)
	if match:
		return match.group(1).strip().title()
	return "London"

@router.post("/api/chat")
def chat_endpoint(req: ChatRequest):
	message = req.message
	now = datetime.utcnow().isoformat()
	logger.info(f"POST /api/chat - message: {message} - timestamp: {now}")

	if any(term in message.lower() for term in ["weather", "forecast", "temperature"]):
		from backend.app.services.weather_service import get_weather_reply
		city = extract_city_from_message(message)
		response = get_weather_reply(city)
		logger.info(f"/api/chat response: {response}")
		return response

	response = {"type": "unknown", "message": "Unsupported request"}
	logger.info(f"/api/chat response: {response}")
	return response