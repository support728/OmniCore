import requests

def run_weather() -> str:
    try:
        response = requests.get("https://wttr.in/?format=3", timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except Exception:
        return "Weather unavailable"
