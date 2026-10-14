# A very small API key check, used as a dependency on the write endpoints.
from typing import Optional

from fastapi import Header, HTTPException

from app.core.config import API_KEY


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Missing or wrong API key")
    return x_api_key
