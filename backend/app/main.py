


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import openai

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
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return {"response": "OpenAI API key not set."}
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.message}
            ]
        )
        ai_response = completion.choices[0].message["content"]
    except Exception as e:
        ai_response = f"OpenAI error: {str(e)}"
    return {
        "response": ai_response
    }
