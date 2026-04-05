from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4.1-mini"

    REDIS_URL: str = "redis://localhost:6379/0"

    SERPAPI_API_KEY: str | None = None
    NEWS_API_KEY: str | None = None

    APP_NAME: str = "OmniCore API"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    MEMORY_MAX_MESSAGES: int = 24
    REQUEST_TIMEOUT_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
