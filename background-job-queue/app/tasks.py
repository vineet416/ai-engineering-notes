"""The actual work: summarize text with an LLM.
No GROQ_API_KEY? A fixed delay stands in for the LLM call, so it all still runs offline."""
import time
from typing import Optional

from app import config


def summarize(payload: dict, seconds: Optional[float] = None) -> str:
    text = payload["text"]
    if config.USE_LLM and seconds is None:
        from app.llm import summarize_with_llm
        return summarize_with_llm(text)
    time.sleep(config.JOB_SECONDS if seconds is None else seconds)  # stand-in for the LLM call
    first = text.split(".")[0].strip()
    return f"Summary ({len(text.split())} words): {first}."


TASKS = {"summarize": summarize}
