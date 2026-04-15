from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core API keys
    openai_api_key: str
    serpapi_api_key: str | None = None

    # OpenAI model
    openai_model: str = "gpt-4o-mini"

    # Weather API
    weather_api_key: str
    weather_api_base_url: str = "https://api.weatherapi.com/v1"

    # News API
    news_api_key: str
    news_api_base_url: str = "https://newsapi.org/v2"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()