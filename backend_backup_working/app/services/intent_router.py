from fastapi import APIRouter
from pydantic import BaseModel
from app.services.openai_service import get_ai_response

router = APIRouter()

class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    try:
        ai_response = await get_ai_response(user_message)
    except Exception as e:
        ai_response = f"Something went wrong: {str(e)}"

    return {"response": ai_response}