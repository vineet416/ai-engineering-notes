"""Settings for the API models, read from a .env file in this folder.

The key never goes in code. Copy .env.example to .env and fill it in.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    euri_api_key: str = ""
    euri_base_url: str = "https://api.euron.one/api/v1/euri"
    embedding_model: str = "gemini-embedding-2"
    llm_model: str = "gpt-5.4-mini"


settings = Settings()
