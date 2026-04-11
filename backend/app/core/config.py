

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    weather_api_key: str
    weather_api_base_url: str
    news_api_key: str
    news_api_base_url: str

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

def get_settings():
    return Settings()
