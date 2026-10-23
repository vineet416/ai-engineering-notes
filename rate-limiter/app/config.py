import os

# Where the shared counter lives. Every API server points at the same Redis.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# "token_bucket" or "fixed_window"
ALGORITHM = os.getenv("RATE_LIMIT_ALGORITHM", "token_bucket")

# 10 requests per 60 seconds per API key.
LIMIT = int(os.getenv("RATE_LIMIT", "10"))
WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# What to do if Redis is down: True = let requests through (fail open),
# False = reject everything with 503 (fail closed).
FAIL_OPEN = os.getenv("RATE_LIMIT_FAIL_OPEN", "true").lower() == "true"
