import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.services.intent_router import handle_message
from backend.app.services.news_service import get_weather_analysis
from backend.app.services.weather_service import detect_weather_request_type, format_weather_reply, get_weather_reply


class MockResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _settings_stub():
    return SimpleNamespace(
        weather_api_key="test-weather-key",
        weather_api_base_url="https://api.openweathermap.org/data/2.5/weather",
        weather_forecast_api_base_url="https://api.openweathermap.org/data/2.5/forecast",
    )


def _current_payload():
    return {
        "name": "Paris",
        "sys": {"country": "FR"},
        "main": {"temp": 71.4, "feels_like": 70.8, "humidity": 58},
        "weather": [{"description": "clear skies"}],
    }


def _forecast_payload():
    return {
        "city": {"name": "Paris", "country": "FR"},
        "list": [
            {"dt_txt": "2026-04-17 09:00:00", "main": {"temp": 68.2, "feels_like": 67.8, "humidity": 54}, "weather": [{"description": "sunny"}]},
            {"dt_txt": "2026-04-18 12:00:00", "main": {"temp": 73.4, "feels_like": 72.9, "humidity": 49}, "weather": [{"description": "light clouds"}]},
            {"dt_txt": "2026-04-19 12:00:00", "main": {"temp": 70.1, "feels_like": 69.2, "humidity": 61}, "weather": [{"description": "scattered showers"}]},
            {"dt_txt": "2026-04-20 12:00:00", "main": {"temp": 66.0, "feels_like": 65.2, "humidity": 63}, "weather": [{"description": "cool breeze"}]},
        ],
    }


class WeatherIntentTests(unittest.TestCase):
    def test_detect_weather_request_type(self):
        self.assertEqual(detect_weather_request_type("weather in Paris"), "current")
        self.assertEqual(detect_weather_request_type("weather tomorrow in Paris"), "tomorrow")
        self.assertEqual(detect_weather_request_type("weekend weather in Paris"), "weekend")
        self.assertEqual(detect_weather_request_type("forecast for Paris"), "forecast")

    @patch("backend.app.services.weather_service.get_settings", side_effect=_settings_stub)
    @patch("backend.app.services.weather_service.requests.get")
    def test_current_weather_uses_current_endpoint(self, requests_get_mock, _settings_mock):
        requests_get_mock.return_value = MockResponse(200, _current_payload())

        result = get_weather_reply("weather in Paris")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["request_type"], "current")
        self.assertEqual(requests_get_mock.call_args.kwargs["params"]["q"], "Paris")
        self.assertIn("/weather", requests_get_mock.call_args.args[0])
        self.assertIn("clear skies", format_weather_reply(result))

    @patch("backend.app.services.weather_service.get_settings", side_effect=_settings_stub)
    @patch("backend.app.services.weather_service.requests.get")
    def test_tomorrow_weather_uses_forecast_endpoint(self, requests_get_mock, _settings_mock):
        requests_get_mock.return_value = MockResponse(200, _forecast_payload())

        result = get_weather_reply("weather tomorrow in Paris")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["request_type"], "tomorrow")
        self.assertIn("/forecast", requests_get_mock.call_args.args[0])
        self.assertEqual(result["forecast_days"][0]["label"], "Saturday")
        self.assertIn("Tomorrow in Paris, FR", format_weather_reply(result))

    @patch("backend.app.services.weather_service.get_settings", side_effect=_settings_stub)
    @patch("backend.app.services.weather_service.requests.get")
    def test_weekend_weather_returns_multi_day_forecast(self, requests_get_mock, _settings_mock):
        requests_get_mock.return_value = MockResponse(200, _forecast_payload())

        result = get_weather_reply("weekend forecast for Paris")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["request_type"], "weekend")
        self.assertEqual(len(result["forecast_days"]), 2)
        reply = format_weather_reply(result)
        self.assertIn("This weekend in Paris, FR", reply)
        self.assertIn("Saturday", reply)
        self.assertIn("Sunday", reply)

    @patch("backend.app.services.weather_service.get_settings", side_effect=_settings_stub)
    @patch("backend.app.services.weather_service.requests.get")
    def test_forecast_weather_returns_general_multi_day_forecast(self, requests_get_mock, _settings_mock):
        requests_get_mock.return_value = MockResponse(200, _forecast_payload())

        result = get_weather_reply("forecast for Paris")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["request_type"], "forecast")
        self.assertEqual(len(result["forecast_days"]), 3)
        self.assertIn("Forecast in Paris, FR", format_weather_reply(result))

    @patch("backend.app.services.weather_service.get_settings", side_effect=_settings_stub)
    @patch("backend.app.services.weather_service.requests.get")
    def test_legacy_chat_reply_changes_with_weather_intent(self, requests_get_mock, _settings_mock):
        requests_get_mock.side_effect = [
            MockResponse(200, _current_payload()),
            MockResponse(200, _forecast_payload()),
            MockResponse(200, _forecast_payload()),
        ]

        current_result = handle_message("weather in Paris", "weather-intent-session")
        tomorrow_result = handle_message("weather tomorrow in Paris", "weather-intent-session")
        weekend_result = handle_message("weekend forecast for Paris", "weather-intent-session")

        self.assertNotEqual(current_result["reply"], tomorrow_result["reply"])
        self.assertNotEqual(tomorrow_result["reply"], weekend_result["reply"])
        self.assertEqual(current_result["weather"]["request_type"], "current")
        self.assertEqual(tomorrow_result["weather"]["request_type"], "tomorrow")
        self.assertEqual(weekend_result["weather"]["request_type"], "weekend")

    @patch("backend.app.services.news_service.get_last_weather_city", return_value=None)
    @patch("backend.app.services.weather_service.get_settings", side_effect=_settings_stub)
    @patch("backend.app.services.weather_service.requests.get")
    def test_structured_weather_analysis_changes_by_request_type(self, requests_get_mock, _settings_mock, _last_city_mock):
        requests_get_mock.return_value = MockResponse(200, _forecast_payload())

        result = get_weather_analysis("forecast for Paris", "structured-weather-session")

        self.assertEqual(result["tool"], "weather")
        self.assertIn("Forecast in Paris, FR", result["content"]["summary"])
        self.assertIn("forecast periods", result["content"]["insight"])
        self.assertIn("weekend outlook", result["content"]["actions"][1])


if __name__ == "__main__":
    unittest.main()