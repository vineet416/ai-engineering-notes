"""Settings come from environment variables or a .env file in the project folder.

With GROQ_API_KEY set, the worker makes a real LLM call (Groq, OpenAI-compatible API).
Without it, a fixed delay stands in for the LLM so everything still runs offline.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Where Redis lives. Locally: docker run -p 6379:6379 redis:7
    redis_url: str = "redis://localhost:6379/0"

    # Real LLM (leave the key empty to use the fake delay instead)
    groq_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-20b"

    # How long the fake "LLM call" takes when there is no key
    job_seconds: float = 3

    # A claimed job must be finished (acked) within this many seconds,
    # or the reaper puts it back on the queue for another worker.
    lease_seconds: int = 10

    # After this many tries a job goes to the dead-letter list instead of retrying forever.
    max_attempts: int = 3


settings = Settings()

REDIS_URL = settings.redis_url
JOB_SECONDS = settings.job_seconds
LEASE_SECONDS = settings.lease_seconds
MAX_ATTEMPTS = settings.max_attempts
USE_LLM = bool(settings.groq_api_key)
