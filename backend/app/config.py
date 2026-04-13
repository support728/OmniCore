from pydantic_settings import BaseSettings  


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-5.4-mini"

    weather_api_key: str
    weather_api_base_url: str = "https://api.weatherapi.com/v1"

    news_api_key: str
    news_api_base_url: str = "https://newsapi.org/v2"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings():
    return Settings()