# Rate limiter (FastAPI + Redis)

A small API with a real rate limiter: 10 requests per 60 seconds per API key. The 11th request gets `429 Too Many Requests` with a `Retry-After` header.

It has 4 limiters in `app/limiters.py`, from wrong to right, so you can see each mistake happen:

| Limiter | Counter lives in | Problem it shows |
|---|---|---|
| `InMemoryFixedWindow` | a Python dict in each server | 3 servers = 3x the limit (same with `uvicorn --workers 4` on one machine) |
| `RedisFixedWindowNaive` | Redis, GET then SET | race: requests at the same instant all read the same count |
| `RedisFixedWindow` | Redis, `INCR` (atomic) | correct count, but 2 bursts at a window edge get through |
| `RedisTokenBucket` | Redis, one Lua script | no edge burst, no race, uses Redis's clock so servers agree |

The app uses the token bucket by default (`RATE_LIMIT_ALGORITHM=fixed_window` to switch).

If Redis is down the app **fails open** (lets requests through and logs a warning). Set `RATE_LIMIT_FAIL_OPEN=false` to return 503 instead.

## What the demo prints

`python -m scripts.demo` (needs a real Redis):

```
Limit: 10 requests per 60 s, one API key

1. Burst at the window edge (20 requests in 1 second)
   fixed window   allowed 20 / 20
   token bucket   allowed 10 / 20

2. Counter in each server's memory vs one counter in Redis (3 servers, 30 requests)
   in memory      allowed 30 / 30
   shared Redis   allowed 10 / 30

3. 50 requests at the same instant (read-then-write vs atomic)
   GET then SET        allowed 50 / 50
   INCR (atomic)       allowed 10 / 50
   Lua token bucket    allowed 10 / 50
```

The race number in part 3 can change from run to run. It is always above 10.

## Run it on Windows

Start Docker Desktop, then run Redis:

```
docker run -d --name rl-redis -p 6379:6379 redis:7
```

In PowerShell, inside this folder:

```
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m scripts.demo
python -m pytest -v
python -m uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs and call `GET /api/quote` 11 times.

Tests use fakeredis (with Lua), so `pytest` doesn't need Docker.

## Files

```
app/
  config.py     limit, window, algorithm, fail open or closed
  limiters.py   the 4 limiters + the token bucket Lua script
  main.py       FastAPI app, rate_limit dependency, 429 / 503 responses
scripts/
  demo.py       the 3 experiments above
tests/
  test_limiters.py   edge burst, refill, capacity, 3 servers
  test_api.py        429 + Retry-After, per-key limits, Redis down
```
