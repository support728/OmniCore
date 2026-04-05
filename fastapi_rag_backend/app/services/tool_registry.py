from app.tools.weather import run_weather
from app.tools.news import run_news
from app.tools.web_search import run_web_search
from app.tools.time_tool import run_time
from app.tools.identity import run_identity

TOOLS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather summary.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_news",
        "description": "Get the top US news headline.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "web_search",
        "description": "Search the web for a user query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_time",
        "description": "Get the current local server time.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_identity",
        "description": "Tell the user the assistant identity.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
]

def execute_tool(name: str, arguments: dict) -> dict:
    if name == "get_weather":
        return {"output": run_weather()}

    if name == "get_news":
        return {"output": run_news()}

    if name == "web_search":
        return run_web_search(arguments["query"])

    if name == "get_time":
        return {"output": run_time()}

    if name == "get_identity":
        return {"output": run_identity()}

    return {"output": f"Unknown tool: {name}"}
