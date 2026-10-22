"""Consumer side: a cook. Run as many of these as you want, in separate terminals.

    python -m app.worker            safe mode (claim, then ack after the work is done)
    python -m app.worker --unsafe   pop-and-forget mode, to see a job get lost
"""
import argparse
import os
import time

import redis

from app import jobqueue
from app.config import REDIS_URL, USE_LLM, settings
from app.tasks import TASKS


def run_one(r: redis.Redis, unsafe: bool = False, timeout: int = 1, seconds=None) -> bool:
    """Take one job, do it, mark it done. Returns False if the rail was empty."""
    if not unsafe:
        jobqueue.reap(r)
    claim = jobqueue.claim_unsafe if unsafe else jobqueue.claim
    job_id = claim(r, timeout=timeout)
    if job_id is None:
        return False
    job = jobqueue.get_job(r, job_id)
    print(f"[worker {os.getpid()}] picked {job_id}", flush=True)
    try:
        task = TASKS[job["kind"]]
        result = task(job["payload"]) if seconds is None else task(job["payload"], seconds)
    except Exception as exc:  # noqa: BLE001 - any failure should go to retry/dead-letter
        print(f"[worker {os.getpid()}] {job_id} failed: {exc}", flush=True)
        jobqueue.fail(r, job_id, str(exc))
        return True
    if unsafe:
        r.hset(jobqueue.job_key(job_id), mapping={"status": "done", "result": result})
    else:
        jobqueue.ack(r, job_id, result)
    print(f"[worker {os.getpid()}] done   {job_id}", flush=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unsafe", action="store_true", help="pop and forget (loses jobs on crash)")
    args = parser.parse_args()
    r = redis.Redis.from_url(REDIS_URL)
    mode = "UNSAFE pop-and-forget" if args.unsafe else "safe claim + ack"
    llm = settings.llm_model if USE_LLM else "fake LLM delay"
    print(f"[worker {os.getpid()}] started ({mode}, {llm}), waiting for jobs...", flush=True)
    while True:
        try:
            run_one(r, unsafe=args.unsafe)
        except redis.ConnectionError:
            print("Redis not reachable, retrying in 2 s", flush=True)
            time.sleep(2)


if __name__ == "__main__":
    main()
