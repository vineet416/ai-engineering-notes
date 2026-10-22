"""A small job queue on top of Redis lists.

Kitchen version:
  queue        = the ticket rail. Waiters (the API) add tickets, cooks (workers) take them.
  processing   = tickets clipped at a cook's station. Not done yet, not thrown away.
  lease:<id>   = "a cook is still on this". Expires if the cook disappears.
  dead         = tickets that failed MAX_ATTEMPTS times. A human looks at these.
"""
import json
import uuid
from typing import Optional

import redis

from app.config import LEASE_SECONDS, MAX_ATTEMPTS

QUEUE = "jobs:queue"
PROCESSING = "jobs:processing"
DEAD = "jobs:dead"


def job_key(job_id: str) -> str:
    return f"job:{job_id}"


def lease_key(job_id: str) -> str:
    return f"lease:{job_id}"


def enqueue(r: redis.Redis, kind: str, payload: dict) -> str:
    """Producer side. Save the job, put its id on the rail, return right away."""
    job_id = uuid.uuid4().hex[:12]
    r.hset(job_key(job_id), mapping={
        "kind": kind,
        "payload": json.dumps(payload),
        "status": "queued",
        "attempts": 0,
    })
    r.lpush(QUEUE, job_id)
    return job_id


def get_job(r: redis.Redis, job_id: str) -> Optional[dict]:
    data = r.hgetall(job_key(job_id))
    if not data:
        return None
    job = {k.decode(): v.decode() for k, v in data.items()}
    job["payload"] = json.loads(job["payload"])
    job["attempts"] = int(job["attempts"])
    job["id"] = job_id
    return job


def claim_unsafe(r: redis.Redis, timeout: int = 1) -> Optional[str]:
    """Pop and forget. If the worker dies after this line, the job is gone for good."""
    item = r.brpop(QUEUE, timeout=timeout)
    if item is None:
        return None
    job_id = item[1].decode()
    r.hset(job_key(job_id), "status", "running")
    return job_id


def claim(r: redis.Redis, timeout: int = 1) -> Optional[str]:
    """Move the id from the rail to the processing list in one atomic step,
    and start a lease. The job is never in zero places."""
    item = r.blmove(QUEUE, PROCESSING, timeout, "RIGHT", "LEFT")
    if item is None:
        return None
    job_id = item.decode()
    r.set(lease_key(job_id), "1", ex=LEASE_SECONDS)
    r.hincrby(job_key(job_id), "attempts", 1)
    r.hset(job_key(job_id), "status", "running")
    return job_id


def ack(r: redis.Redis, job_id: str, result: str) -> None:
    """Dish is out. Save the result, then take the ticket off the station."""
    pipe = r.pipeline()
    pipe.hset(job_key(job_id), mapping={"status": "done", "result": result})
    pipe.lrem(PROCESSING, 1, job_id)
    pipe.delete(lease_key(job_id))
    pipe.execute()


def fail(r: redis.Redis, job_id: str, error: str) -> None:
    """Job raised an error. Retry it, or park it in the dead-letter list."""
    attempts = int(r.hget(job_key(job_id), "attempts") or 0)
    pipe = r.pipeline()
    pipe.lrem(PROCESSING, 1, job_id)
    pipe.delete(lease_key(job_id))
    if attempts >= MAX_ATTEMPTS:
        pipe.hset(job_key(job_id), mapping={"status": "dead", "error": error})
        pipe.lpush(DEAD, job_id)
    else:
        pipe.hset(job_key(job_id), mapping={"status": "queued", "error": error})
        pipe.rpush(QUEUE, job_id)  # back of the rail = next to be picked
    pipe.execute()


def reap(r: redis.Redis) -> list:
    """Find jobs whose worker vanished (lease expired) and put them back.
    Any worker can run this; it's cheap."""
    recovered = []
    for raw in r.lrange(PROCESSING, 0, -1):
        job_id = raw.decode()
        if r.exists(lease_key(job_id)):
            continue  # someone is still cooking it
        if r.lrem(PROCESSING, 1, job_id):  # only one reaper wins this
            r.hset(job_key(job_id), "status", "queued")
            r.rpush(QUEUE, job_id)
            recovered.append(job_id)
    return recovered


def counts(r: redis.Redis) -> dict:
    return {
        "queued": r.llen(QUEUE),
        "processing": r.llen(PROCESSING),
        "dead": r.llen(DEAD),
    }
