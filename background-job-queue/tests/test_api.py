import time

from app import jobqueue
from app.worker import run_one

TEXT = {"text": "The parcel arrived late. Customer wants a partial refund."}


def test_post_returns_202_with_job_id_fast(client, r):
    start = time.perf_counter()
    resp = client.post("/summaries", json=TEXT)
    took = time.perf_counter() - start

    assert resp.status_code == 202
    assert resp.json()["status"] == "queued"
    assert took < 0.5  # no waiting for the 3 s job
    assert jobqueue.counts(r)["queued"] == 1


def test_worker_finishes_job_and_status_shows_result(client, r):
    job_id = client.post("/summaries", json=TEXT).json()["job_id"]
    assert run_one(r, seconds=0) is True

    body = client.get(f"/summaries/{job_id}").json()
    assert body["status"] == "done"
    assert body["result"].startswith("Summary (9 words): The parcel arrived late")
    assert jobqueue.counts(r) == {"queued": 0, "processing": 0, "dead": 0}


def test_unknown_job_is_404(client):
    assert client.get("/summaries/nope").status_code == 404


def test_empty_text_is_rejected(client):
    assert client.post("/summaries", json={"text": ""}).status_code == 422


def test_empty_queue_means_worker_has_nothing_to_do(r):
    assert run_one(r, timeout=1) is False


def test_summarize_uses_real_llm_when_key_is_set(monkeypatch):
    from app import config, llm, tasks

    monkeypatch.setattr(config, "USE_LLM", True)
    monkeypatch.setattr(llm, "summarize_with_llm", lambda text: "LLM says: late parcel, refund asked.")
    assert tasks.summarize(TEXT) == "LLM says: late parcel, refund asked."
