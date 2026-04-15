from fastapi import APIRouter
from pydantic import BaseModel
from services.intent_router import handle_chat

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):
    return await handle_chat(req.message)
