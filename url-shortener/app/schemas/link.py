# Pydantic schemas: what the API accepts and what it sends back.
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ShortenRequest(BaseModel):
    # HttpUrl rejects things like "hello", "ftp://..." and "javascript:alert(1)"
    url: HttpUrl
    # optional custom code, e.g. "my-resume". Letters, digits, - and _ only.
    alias: Optional[str] = Field(default=None, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")


class LinkOut(BaseModel):
    code: str
    short_url: str
    long_url: str


class ReferrerCount(BaseModel):
    referrer: str
    clicks: int


class StatsOut(BaseModel):
    code: str
    long_url: str
    total_clicks: int
    clicks_by_day: Dict[str, int]
    top_referrers: List[ReferrerCount]
