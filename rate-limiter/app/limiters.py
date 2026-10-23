"""Four rate limiters, from wrong to right.

Every limiter has the same method:
    allow(key, now=None) -> Decision
`now` is only passed by the demos and tests so they can fake the clock.
In the real app it is None and the time comes from Redis (see token bucket).
"""
import math
import time
from dataclasses import dataclass


@dataclass
class Decision:
    allowed: bool
    remaining: int
    retry_after: float  # seconds until the next request would be allowed


class InMemoryFixedWindow:
    """Counter in a Python dict. Fine on 1 process, wrong on many.

    Each API server (and each uvicorn worker) gets its own dict,
    so a user who is spread over 3 servers gets 3x the limit.
    """

    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.counts = {}

    def allow(self, key, now=None):
        now = time.time() if now is None else now
        bucket = (key, int(now // self.window))
        count = self.counts.get(bucket, 0) + 1
        self.counts[bucket] = count
        reset = (bucket[1] + 1) * self.window - now
        if count <= self.limit:
            return Decision(True, self.limit - count, 0.0)
        return Decision(False, 0, reset)


class RedisFixedWindowNaive:
    """Shared counter in Redis, but read and write are 2 separate steps.

    Two servers can both read 9, both decide "under 10", both write 10.
    Kept here only to show the race.
    """

    def __init__(self, r, limit, window):
        self.r, self.limit, self.window = r, limit, window

    def allow(self, key, now=None):
        now = time.time() if now is None else now
        k = f"naive:{key}:{int(now // self.window)}"
        count = int(self.r.get(k) or 0)  # step 1: read
        if count >= self.limit:
            return Decision(False, 0, self.window - now % self.window)
        self.r.set(k, count + 1, ex=self.window)  # step 2: write
        return Decision(True, self.limit - count - 1, 0.0)


class RedisFixedWindow:
    """Fixed window done right: INCR is atomic, so no race.

    Weak spot: the window edge. 10 requests at 0:59 and 10 more at 1:00
    are in different windows, so 20 get through in about 1 second.
    """

    def __init__(self, r, limit, window):
        self.r, self.limit, self.window = r, limit, window

    def allow(self, key, now=None):
        now = time.time() if now is None else now
        k = f"fw:{key}:{int(now // self.window)}"
        pipe = self.r.pipeline()
        pipe.incr(k)
        pipe.expire(k, self.window)
        count, _ = pipe.execute()
        if count <= self.limit:
            return Decision(True, self.limit - count, 0.0)
        return Decision(False, 0, self.window - now % self.window)


# Runs inside Redis, so "read tokens, refill, take one, save" is one step
# that no other server can interrupt.
TOKEN_BUCKET_LUA = """
local key      = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate     = tonumber(ARGV[2])   -- tokens added per second
local now      = tonumber(ARGV[3])
if now == nil then
  -- No time given: use Redis's own clock, so servers with slightly
  -- different clocks still agree.
  local t = redis.call('TIME')
  now = tonumber(t[1]) + tonumber(t[2]) / 1000000
end

local data   = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1]) or capacity
local ts     = tonumber(data[2]) or now

-- refill for the time that passed, never above capacity
tokens = math.min(capacity, tokens + math.max(0, now - ts) * rate)

local allowed = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
end

redis.call('HSET', key, 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', key, math.ceil(capacity / rate) + 1)
return {allowed, tostring(tokens)}
"""


class RedisTokenBucket:
    """Bucket holds up to `capacity` tokens and refills at `limit/window` per second.

    Same average limit as the fixed window, but no double burst at the edge:
    after a burst you have to wait for tokens to drip back in.
    """

    def __init__(self, r, limit, window):
        self.capacity = limit
        self.rate = limit / window
        self.script = r.register_script(TOKEN_BUCKET_LUA)

    def allow(self, key, now=None):
        args = [self.capacity, self.rate, "" if now is None else now]
        allowed, tokens = self.script(keys=[f"tb:{key}"], args=args)
        tokens = float(tokens)
        retry = 0.0 if allowed else (1 - tokens) / self.rate
        return Decision(bool(allowed), math.floor(tokens), retry)
