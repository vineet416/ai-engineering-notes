"""Shows the 3 ways a rate limiter goes wrong, against a real Redis.

Run Redis first (Docker):  docker run -d --name rl-redis -p 6379:6379 redis:7
Then:                      python -m scripts.demo

Limit everywhere: 10 requests per 60 seconds for one API key.
"""
import os
import threading

import redis

from app.limiters import (
    InMemoryFixedWindow,
    RedisFixedWindow,
    RedisFixedWindowNaive,
    RedisTokenBucket,
)

LIMIT, WINDOW = 10, 60
r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
r.flushdb()


def count_allowed(limiter, times, key):
    return sum(limiter.allow(key, now=t).allowed for t in times)


print(f"Limit: {LIMIT} requests per {WINDOW} s, one API key\n")

# 1. The window edge: 10 requests at 0:59.5 and 10 more at 1:00.5
print("1. Burst at the window edge (20 requests in 1 second)")
times = [59.5] * 10 + [60.5] * 10
fw = count_allowed(RedisFixedWindow(r, LIMIT, WINDOW), times, "edge")
tb = count_allowed(RedisTokenBucket(r, LIMIT, WINDOW), [t + 1000 for t in times], "edge")
print(f"   fixed window   allowed {fw:>2} / 20")
print(f"   token bucket   allowed {tb:>2} / 20\n")

# 2. Where the counter lives: 3 servers behind a round-robin load balancer
print("2. Counter in each server's memory vs one counter in Redis (3 servers, 30 requests)")
local = [InMemoryFixedWindow(LIMIT, WINDOW) for _ in range(3)]
shared = [RedisFixedWindow(r, LIMIT, WINDOW) for _ in range(3)]
in_mem = sum(local[i % 3].allow("lb", now=5.0).allowed for i in range(30))
in_redis = sum(shared[i % 3].allow("lb", now=5.0).allowed for i in range(30))
print(f"   in memory      allowed {in_mem:>2} / 30")
print(f"   shared Redis   allowed {in_redis:>2} / 30\n")


# 3. Race: 50 requests at the same moment from many threads
def hammer(limiter, key, n=50):
    results = []
    barrier = threading.Barrier(n)

    def one():
        barrier.wait()  # all threads fire together
        results.append(limiter.allow(key, now=7.0).allowed)

    threads = [threading.Thread(target=one) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sum(results)


print("3. 50 requests at the same instant (read-then-write vs atomic)")
naive = hammer(RedisFixedWindowNaive(r, LIMIT, WINDOW), "race")
atomic_fw = hammer(RedisFixedWindow(r, LIMIT, WINDOW), "race")
atomic_tb = hammer(RedisTokenBucket(r, LIMIT, WINDOW), "race")
print(f"   GET then SET        allowed {naive:>2} / 50")
print(f"   INCR (atomic)       allowed {atomic_fw:>2} / 50")
print(f"   Lua token bucket    allowed {atomic_tb:>2} / 50")
