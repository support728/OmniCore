import httpx
from app.core.config import get_settings


class WeatherService:
    def __init__(self, client):
        self.client = client
        self.settings = get_settings()
        print("API KEY:", self.settings.weather_api_key)  # TEMP DEBUG

    async def handle(self, request):
        # Extract clean location
        location = request.message.replace("weather in", "").strip()

        url = "http://api.weatherapi.com/v1/current.json"
        params = {
            "key": self.settings.weather_api_key,
            "q": location
        }
        response = await self.client.get(url, params=params)
        print("FULL RESPONSE:", response.text)  # TEMP DEBUG
        data = response.json()
        return {
            "answer": f"{data['location']['name']}: {data['current']['temp_c']}°C"
        }