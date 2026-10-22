"""Producer side: the counter. Takes the order, puts a ticket on the rail, answers right away."""
import time

import redis
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import jobqueue
from app.config import REDIS_URL
from app.tasks import summarize

app = FastAPI(title="Background job queue demo")
_redis = redis.Redis.from_url(REDIS_URL)


def get_redis() -> redis.Redis:
    return _redis


class SummaryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)


@app.post("/summaries/sync")
def create_summary_sync(body: SummaryRequest):
    """The 'cook it at the counter' version: the caller waits for the whole job."""
    start = time.perf_counter()
    result = summarize(body.model_dump())
    return {"result": result, "seconds": round(time.perf_counter() - start, 2)}


@app.post("/summaries", status_code=202)
def create_summary(body: SummaryRequest, r: redis.Redis = Depends(get_redis)):
    """The queue version: save the job, return its id, let a worker do the rest."""
    job_id = jobqueue.enqueue(r, "summarize", body.model_dump())
    return {"job_id": job_id, "status": "queued", "check": f"/summaries/{job_id}"}


@app.get("/summaries/{job_id}")
def get_summary(job_id: str, r: redis.Redis = Depends(get_redis)):
    job = jobqueue.get_job(r, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {k: job.get(k) for k in ("id", "status", "attempts", "result", "error") if k in job}


@app.get("/queue")
def queue_counts(r: redis.Redis = Depends(get_redis)):
    return jobqueue.counts(r)
