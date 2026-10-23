import logging
import math

import redis
from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import JSONResponse

from app import config
from app.limiters import RedisFixedWindow, RedisTokenBucket

log = logging.getLogger("ratelimit")
app = FastAPI(title="Rate limiter demo")

_redis = redis.Redis.from_url(config.REDIS_URL, socket_timeout=0.2)


def get_redis():
    return _redis


def get_limiter(r=Depends(get_redis)):
    cls = RedisTokenBucket if config.ALGORITHM == "token_bucket" else RedisFixedWindow
    return cls(r, config.LIMIT, config.WINDOW_SECONDS)


class RateLimited(Exception):
    def __init__(self, status, body, headers):
        self.status, self.body, self.headers = status, body, headers


@app.exception_handler(RateLimited)
def rate_limited(_: Request, exc: RateLimited):
    return JSONResponse(exc.body, status_code=exc.status, headers=exc.headers)


def rate_limit(
    request: Request,
    x_api_key: str | None = Header(default=None),
    limiter=Depends(get_limiter),
):
    # Limit per API key; fall back to the client IP for anonymous calls.
    who = x_api_key or (request.client.host if request.client else "unknown")
    try:
        d = limiter.allow(who)
    except redis.RedisError as e:
        if config.FAIL_OPEN:
            log.warning("Redis down, letting request through: %s", e)
            return
        raise RateLimited(503, {"detail": "Rate limiter unavailable"}, {"Retry-After": "1"})

    request.state.remaining = d.remaining
    if not d.allowed:
        raise RateLimited(
            429,
            {"detail": "Too many requests"},
            {
                "Retry-After": str(math.ceil(d.retry_after)),
                "X-RateLimit-Limit": str(config.LIMIT),
                "X-RateLimit-Remaining": "0",
            },
        )


@app.get("/api/quote", dependencies=[Depends(rate_limit)])
def quote(request: Request):
    remaining = getattr(request.state, "remaining", None)
    return {"quote": "Ship small, measure, repeat.", "remaining": remaining}
