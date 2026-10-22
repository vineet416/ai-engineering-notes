"""Two measurements:
1. How long the caller waits: cook-at-the-counter endpoint vs queue endpoint.
2. How long 12 queued jobs take to drain with 1 worker vs 4 workers.

Needs Redis running:  docker run -p 6379:6379 redis:7
Run from the project folder:  python scripts/measure.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import jobqueue  # noqa: E402
from app.config import JOB_SECONDS, REDIS_URL, USE_LLM, settings  # noqa: E402
from app.main import app  # noqa: E402
from scripts._helpers import start_worker, wait_for  # noqa: E402

TEXT = {"text": "Customer says the refund never arrived. They want it before Friday."}


def reset(r):
    for key in (jobqueue.QUEUE, jobqueue.PROCESSING, jobqueue.DEAD):
        r.delete(key)


def caller_wait(r):
    reset(r)
    client = TestClient(app)
    sync_runs = []
    for _ in range(3 if USE_LLM else 1):
        t = time.perf_counter()
        resp = client.post("/summaries/sync", json=TEXT)
        sync_runs.append((time.perf_counter() - t) * 1000)
    sync_ms = sorted(sync_runs)[len(sync_runs) // 2]
    sample = resp.json()["result"]

    client.post("/summaries", json=TEXT)  # warm-up
    times = []
    for _ in range(20):
        t = time.perf_counter()
        resp = client.post("/summaries", json=TEXT)
        times.append((time.perf_counter() - t) * 1000)
    assert resp.status_code == 202
    times.sort()
    reset(r)
    job = f"real LLM call, {settings.llm_model}" if USE_LLM else f"fake LLM delay, {JOB_SECONDS:g} s"
    print(f"\nCaller waits (job = {job})")
    print(f"  POST /summaries/sync   {sync_ms:8.0f} ms   (cooked at the counter{', median of 3' if USE_LLM else ''})")
    print(f"  POST /summaries        {times[len(times) // 2]:8.1f} ms   (median of 20, returns 202 + job id)")
    print(f"  sample summary: {sample}")


def drain(r, workers, jobs=12, seconds="1"):
    reset(r)
    ids = [jobqueue.enqueue(r, "summarize", TEXT) for _ in range(jobs)]
    t = time.perf_counter()
    procs = [start_worker(env_overrides={"JOB_SECONDS": seconds}) for _ in range(workers)]
    wait_for(lambda: all(jobqueue.get_job(r, i)["status"] == "done" for i in ids), timeout=120)
    took = time.perf_counter() - t
    for p in procs:
        p.kill()
        p.wait()
    return took


def main():
    r = redis.Redis.from_url(REDIS_URL)
    r.ping()
    caller_wait(r)
    print("\n12 jobs on the queue" + ("" if USE_LLM else ", 1 s each"))
    for n in (1, 4):
        if USE_LLM and n > 1:
            print("  (waiting 60 s so we stay inside Groq's free-tier rate limit)")
            time.sleep(60)
        print(f"  {n} worker{'s' if n > 1 else ' '}  drained in {drain(r, n):5.1f} s")


if __name__ == "__main__":
    main()
