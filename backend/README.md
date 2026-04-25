# Backend Notes

## Weather Endpoint

The backend exposes real-time weather through both of these routes:

- `GET /weather?city=Boston`
- `GET /weather/Boston`

Both routes use the configured OpenWeather API key and return a structured JSON payload with a human-readable `reply` field.