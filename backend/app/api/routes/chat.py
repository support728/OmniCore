from fastapi import APIRouter
from pydantic import BaseModel
import requests

router = APIRouter()

class ChatRequest(BaseModel):
    message: str


def search_web(query: str):
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        data = requests.get(url).json()

        results = []
        links = []

        if data.get("AbstractText"):
            results.append(data["AbstractText"])

        for item in data.get("RelatedTopics", [])[:5]:
            if "Text" in item:
                results.append(item["Text"])
            if "FirstURL" in item:
                links.append(item["FirstURL"])

        response = "\n".join(results)

        if links:
            response += "\n\nLinks:\n"
            for i, link in enumerate(links, 1):
                response += f"{i}. {link}\n"

        return response if response else "No useful results found."

    except Exception as e:
        return f"Error: {str(e)}"


@router.post("/chat")
def chat(req: ChatRequest):
    text = req.message.lower()

    if "search" in text:
        query = text.replace("search", "").strip()
        return {"response": search_web(query)}

    return {"response": "Say: search something"}