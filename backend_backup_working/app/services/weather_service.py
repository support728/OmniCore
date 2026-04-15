def is_city_match(requested_city: str, api_city: str) -> bool:
    if not requested_city or not api_city:
        return False
    requested = requested_city.strip().lower()
    returned = api_city.strip().lower()
    # Exact or strong partial match
    return requested in returned or returned in requested
import httpx
from app.config import get_settings


class WeatherService:
    def __init__(self, client):
        self.client = client
        self.settings = get_settings()
        print("API KEY:", self.settings.weather_api_key)  # TEMP DEBUG

    async def handle(self, request):
        from fastapi.responses import JSONResponse
        try:
            import re
            # Normalize user input
            msg = request.message.lower()
            msg = re.sub(r'\s+', ' ', msg).strip()
            # Remove state abbreviations (e.g., mn, tx, ca, ny, etc.)
            state_abbr = r'(\b[a-z]{2}\b)'
            # Try to extract after 'weather in'
            match = re.search(r"weather in ([a-zA-Z\s]+)", msg)
            if match:
                location = match.group(1).strip()
            else:
                # Fallback: extract after 'in'
                match = re.search(r"in ([a-zA-Z\s]+)", msg)
                if match:
                    location = match.group(1).strip()
                else:
                    # Fallback: use the whole message
                    location = msg.strip()
            # Remove state abbreviations at the end
            location = re.sub(r'\b([a-z]{2})\b$', '', location).strip()
            # Remove trailing commas, question marks, etc.
            location = re.sub(r'[\?,]+$', '', location).strip()

            # First API query: append ',US' for better accuracy
            query_city = f"{location},US"
            url = "http://api.weatherapi.com/v1/current.json"
            params = {
                "key": self.settings.weather_api_key,
                "q": query_city
            }
            response = await self.client.get(url, params=params)
            print("FULL RESPONSE (1):", response.text)  # TEMP DEBUG
            if response.status_code != 200:
                # Try fallback: just the city name
                params["q"] = location
                response = await self.client.get(url, params=params)
                print("FULL RESPONSE (2):", response.text)  # TEMP DEBUG
                if response.status_code != 200:
                    return JSONResponse(
                        status_code=404,
                        content={"error": "City not found", "requested_city": location, "message": f"Sorry, I couldn't find weather for '{location}'. Please check the city name."}
                    )

            data = response.json()
            loc = data.get('location', {})
            curr = data.get('current', {})
            condition = curr.get('condition', {})
            name = loc.get('name', '?')
            country = loc.get('country', '?')
            temp_c = curr.get('temp_c', '?')
            temp_f = curr.get('temp_f', '?')
            humidity = curr.get('humidity', '?')
            wind_kph = curr.get('wind_kph', '?')
            icon = condition.get('icon', '')
            text = condition.get('text', '')

            # 🔒 Validation check
            if not is_city_match(location, name):
                # Safe auto-correct: retry with just city name if not already tried
                if params["q"] != f"{location},US":
                    retry_params = {
                        "key": self.settings.weather_api_key,
                        "q": f"{location}, US"
                    }
                    retry_response = await self.client.get(url, params=retry_params)
                    print("FULL RESPONSE (auto-correct):", retry_response.text)  # TEMP DEBUG
                    if retry_response.status_code == 200:
                        retry_data = retry_response.json()
                        retry_loc = retry_data.get('location', {})
                        retry_name = retry_loc.get('name', '?')
                        if is_city_match(location, retry_name):
                            curr = retry_data.get('current', {})
                            condition = curr.get('condition', {})
                            country = retry_loc.get('country', '?')
                            temp_c = curr.get('temp_c', '?')
                            temp_f = curr.get('temp_f', '?')
                            humidity = curr.get('humidity', '?')
                            wind_kph = curr.get('wind_kph', '?')
                            icon = condition.get('icon', '')
                            text = condition.get('text', '')
                            answer = (
                                f"Weather for {retry_name}, {country}:\n"
                                f"{text} "
                                f"{'🌞' if 'sun' in text.lower() else '☁️' if 'cloud' in text.lower() else '🌧️' if 'rain' in text.lower() else ''}\n"
                                f"Temperature: {temp_c}°C / {temp_f}°F\n"
                                f"Humidity: {humidity}%\n"
                                f"Wind: {wind_kph} kph\n"
                                f"[icon]({icon})" if icon else ""
                            )
                            return {"answer": answer}
                        else:
                            return JSONResponse(
                                status_code=400,
                                content={
                                    "error": "City mismatch detected",
                                    "requested_city": location,
                                    "resolved_city": retry_name,
                                    "message": f"Did you mean '{retry_name}'?"
                                }
                            )
                # If already tried both, return error
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "City mismatch detected",
                        "requested_city": location,
                        "resolved_city": name,
                        "message": f"Did you mean '{name}'?"
                    }
                )

            answer = (
                f"Weather for {name}, {country}:\n"
                f"{text} "
                f"{'🌞' if 'sun' in text.lower() else '☁️' if 'cloud' in text.lower() else '🌧️' if 'rain' in text.lower() else ''}\n"
                f"Temperature: {temp_c}°C / {temp_f}°F\n"
                f"Humidity: {humidity}%\n"
                f"Wind: {wind_kph} kph\n"
                f"[icon]({icon})" if icon else ""
            )
            return {"answer": answer}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": "Weather service failed", "details": str(e)}
            )