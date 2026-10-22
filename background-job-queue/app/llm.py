"""One real LLM call: summarize a piece of text in one sentence."""
from openai import OpenAI

from app.config import settings

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.llm_base_url,
            # Groq sits behind Cloudflare, which can block requests without a User-Agent
            default_headers={"User-Agent": "background-job-queue/1.0"},
            timeout=60,
        )
    return _client


def summarize_with_llm(text: str) -> str:
    resp = get_client().chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "Summarize the user's text in one short sentence."},
            {"role": "user", "content": text},
        ],
        reasoning_effort="low",
        max_tokens=1000,
    )
    return (resp.choices[0].message.content or "").strip()
