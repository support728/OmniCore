
# In-memory user-based conversation memory
memory = {}



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    user_id: str
    message: str

app = FastAPI()

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for now, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}


# /chat endpoint

@app.post("/chat")
def chat(request: ChatRequest):
    # Initialize user memory if not present
    if request.user_id not in memory:
        memory[request.user_id] = [
            {"role": "system", "content": "You are OmniCore AI."}
        ]

    user_convo = memory[request.user_id]

    # Add user message to user's conversation
    user_convo.append({
        "role": "user",
        "content": request.message
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=user_convo
    )

    reply = response.choices[0].message.content

    # Add assistant reply to user's conversation
    user_convo.append({
        "role": "assistant",
        "content": reply
    })

    return {
        "response": reply
    }
