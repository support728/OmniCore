from backend.app.config import settings
import requests

def get_weather_reply(city: str):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={settings.openweather_api_key}"
        response = requests.get(url)
        data = response.json()

        return {
            "type": "weather",
            "message": {
                "city": data.get("name"),
                "country": data.get("sys", {}).get("country"),
                "temperature": data.get("main", {}).get("temp"),
                "description": data.get("weather", [{}])[0].get("description"),
                "humidity": data.get("main", {}).get("humidity"),
                "wind_speed": data.get("wind", {}).get("speed")
            }
        }

    except Exception as e:
        return {
            "type": "error",
            "message": str(e)
        }
