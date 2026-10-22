"""Kill a worker in the middle of a job and see what happens to that job.

Needs Redis running:  docker run -p 6379:6379 redis:7
Run from the project folder:  python scripts/crash_demo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis  # noqa: E402

from app import jobqueue  # noqa: E402
from app.config import REDIS_URL  # noqa: E402
from scripts._helpers import start_worker, wait_for  # noqa: E402

LEASE = "5"  # short lease so the demo doesn't take long
ENV = {"JOB_SECONDS": "5", "LEASE_SECONDS": LEASE}


def status(r, job_id):
    job = jobqueue.get_job(r, job_id)
    return job["status"], job["attempts"]


def run(r, unsafe):
    for key in (jobqueue.QUEUE, jobqueue.PROCESSING, jobqueue.DEAD):
        r.delete(key)
    label = "pop and forget (BRPOP)" if unsafe else "claim + ack (BLMOVE + lease)"
    print(f"\n=== {label} ===")
    job_id = jobqueue.enqueue(r, "summarize", {"text": "Refund request for order 1042. Customer says the box arrived empty."})
    args = ["--unsafe"] if unsafe else []
    w1 = start_worker(args, ENV)
    wait_for(lambda: status(r, job_id)[0] == "running")
    print(f"job {job_id} picked up by worker 1, now killing worker 1 mid-job")
    w1.kill()
    w1.wait()
    print(f"right after the crash:    status={status(r, job_id)[0]:8} {jobqueue.counts(r)}")

    w2 = start_worker(args, ENV)
    finished = wait_for(lambda: status(r, job_id)[0] == "done", timeout=15)
    st, attempts = status(r, job_id)
    print(f"worker 2 running 15 s on: status={st:8} {jobqueue.counts(r)} attempts={attempts}")
    print("RESULT:", "job finished by worker 2" if finished else "job LOST, nobody will ever run it")
    w2.kill()
    w2.wait()


def main():
    r = redis.Redis.from_url(REDIS_URL)
    r.ping()
    run(r, unsafe=True)
    run(r, unsafe=False)


if __name__ == "__main__":
    main()
