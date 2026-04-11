conversation = [
    {"role": "system", "content": "You are OmniCore AI."}
]



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
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
    # Add user message to conversation
    conversation.append({
        "role": "user",
        "content": request.message
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation
    )

    reply = response.choices[0].message.content

    # Add assistant reply to conversation
    conversation.append({
        "role": "assistant",
        "content": reply
    })

    return {
        "response": reply
    }
