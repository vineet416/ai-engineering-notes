"""What happens to a job when things go wrong."""
from app import jobqueue
from app.config import MAX_ATTEMPTS

TEXT = {"text": "Order 1042 arrived empty."}


def test_pop_and_forget_loses_job_if_worker_dies(r):
    job_id = jobqueue.enqueue(r, "summarize", TEXT)
    jobqueue.claim_unsafe(r)
    # worker crashes here: no ack, no result
    assert jobqueue.reap(r) == []
    assert jobqueue.counts(r) == {"queued": 0, "processing": 0, "dead": 0}
    assert jobqueue.get_job(r, job_id)["status"] == "running"  # stuck forever


def test_claimed_job_stays_in_processing_until_ack(r):
    job_id = jobqueue.enqueue(r, "summarize", TEXT)
    assert jobqueue.claim(r) == job_id
    assert jobqueue.counts(r) == {"queued": 0, "processing": 1, "dead": 0}

    jobqueue.ack(r, job_id, "ok")
    assert jobqueue.counts(r) == {"queued": 0, "processing": 0, "dead": 0}


def test_reaper_leaves_job_alone_while_lease_is_alive(r):
    jobqueue.enqueue(r, "summarize", TEXT)
    jobqueue.claim(r)
    assert jobqueue.reap(r) == []
    assert jobqueue.counts(r)["processing"] == 1


def test_reaper_requeues_job_when_worker_died(r):
    job_id = jobqueue.enqueue(r, "summarize", TEXT)
    jobqueue.claim(r)
    r.delete(jobqueue.lease_key(job_id))  # same as the lease timing out after a crash

    assert jobqueue.reap(r) == [job_id]
    assert jobqueue.counts(r) == {"queued": 1, "processing": 0, "dead": 0}
    assert jobqueue.claim(r) == job_id
    assert jobqueue.get_job(r, job_id)["attempts"] == 2  # it ran twice: jobs must be safe to repeat


def test_failing_job_retries_then_goes_to_dead_letter(r):
    job_id = jobqueue.enqueue(r, "summarize", TEXT)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        assert jobqueue.claim(r) == job_id
        jobqueue.fail(r, job_id, "LLM timed out")
        expected = "dead" if attempt == MAX_ATTEMPTS else "queued"
        assert jobqueue.get_job(r, job_id)["status"] == expected

    assert jobqueue.counts(r) == {"queued": 0, "processing": 0, "dead": 1}


def test_worker_routes_exception_to_retry(r, monkeypatch):
    from app import tasks, worker

    def boom(payload, seconds=None):
        raise RuntimeError("LLM timed out")

    monkeypatch.setitem(tasks.TASKS, "summarize", boom)
    job_id = jobqueue.enqueue(r, "summarize", TEXT)
    worker.run_one(r)
    job = jobqueue.get_job(r, job_id)
    assert job["status"] == "queued" and job["error"] == "LLM timed out"
