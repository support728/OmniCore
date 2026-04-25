from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# FORCE load .env manually
load_dotenv("backend/.env")

class Settings(BaseSettings):
    openweather_api_key: str

settings = Settings()