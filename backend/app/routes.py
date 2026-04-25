from datetime import datetime
import inspect

# Global plugin-based route registry
from datetime import datetime

ROUTES = {}

# Decorator for registering commands
def route(name: str, description: str = ""):
    def decorator(func):
        ROUTES[name] = {
            "handler": func,
            "description": description
        }
        return func
    return decorator

# Register built-in commands using the new decorator
@route("help", description="Show help information")
def help_handler():
    # Help now reads from ROUTES
    help_text = "Available commands:\n"
    for cmd, meta in ROUTES.items():
        desc = meta["description"] if meta["description"] else ""
        help_text += f"- {cmd} {f'- {desc}' if desc else ''}\n"
    return {
        "route": "help",
        "answer": help_text.strip()
    }

@route("status", description="Show API status")
def status_handler():
    return {
        "type": "status",
        "message": "API is running"
    }

@route("time", description="Show current server time")
def time_handler():
    return {
        "type": "time",
        "message": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@route("news", description="Show news (placeholder)")
def news_handler():
    return {
        "route": "news",
        "answer": "News feature coming soon."
    }

import inspect

def handle_route(message: str):
    # Always treat message as string
    if not isinstance(message, str):
        message = str(message)
    message = message.strip()
    normalized = message.lower()
    parts = normalized.split()
    if not parts:
        return None
    command = parts[0]
    args = parts[1:]

    # Weather command special handling
    if command == "weather":
        # Remove 'in' if present as first arg
        if args and args[0] == "in":
            args = args[1:]
        city = " ".join(args) if args else "Tokyo"
        from backend.app.services.weather_service import get_weather_reply
        return get_weather_reply(city)

    # For simple commands, match only the first word
    if command in ROUTES:
        handler = ROUTES[command]["handler"]
        sig = inspect.signature(handler)
        valid_params = sig.parameters.keys()
        # Parse args into positional and keyword arguments
        positional_args = []
        keyword_args = {}
        for arg in args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                keyword_args[key] = value
            else:
                positional_args.append(arg)
        filtered_kwargs = {k: v for k, v in keyword_args.items() if k in valid_params}
        if len(sig.parameters) == 0:
            return handler()
        if not filtered_kwargs:
            return handler(*positional_args)
        return handler(*positional_args, **filtered_kwargs)

    # Unknown command structured response
    return {
        "type": "error",
        "message": f"Unknown command '{command}'",
        "available": list(ROUTES.keys())
    }
# --- Plugin auto-import system ---
import os
import importlib

plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
if os.path.isdir(plugins_dir):
    for file in os.listdir(plugins_dir):
        if file.endswith(".py") and not file.startswith("_"):
            module_name = file[:-3]
            importlib.import_module(f"app.plugins.{module_name}")
