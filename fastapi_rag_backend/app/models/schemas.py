from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    user_input: str = Field(min_length=1)
    session_id: str = Field(min_length=1)

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    request_id: str
