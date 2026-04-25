def test_weather_output():
    from backend.app.services.weather_service import format_weather_reply
    result = format_weather_reply({
        "city": "London",
        "description": "clear sky",
        "temperature": 6.9
    })
    assert result == "Weather in London: clear sky, 6.9°C"
