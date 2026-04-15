from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat(req: ChatRequest):
    user_message = req.message.strip()

    if not user_message:
        return {"reply": "Please type a message."}

    lower_msg = user_message.lower()

    if lower_msg in ["hello", "hi", "help"]:
        return {"reply": f"You said: {user_message}"}

    return {"reply": f"You said: {user_message} (but I don't know how to respond to that yet)"}