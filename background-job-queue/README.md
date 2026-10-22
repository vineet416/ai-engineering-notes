# Background job queue (FastAPI + Redis)

A small, working example of producers, a queue and workers.
The API takes a "summarize this text" request, puts a job on a Redis queue and answers in a few milliseconds with `202 Accepted` and a job id. A separate worker process picks the job up and does the slow part: a real LLM call (Groq, `openai/gpt-oss-20b`) when `GROQ_API_KEY` is set in `.env`, otherwise a fixed delay that stands in for it so everything runs offline.

Same idea as a restaurant: the counter takes your order and hands you a token, the ticket goes on the rail, and the cooks work through the rail at their own pace.

| Kitchen | Here |
|---|---|
| Counter / waiter (producer) | `POST /summaries` in `app/main.py` |
| Ticket rail (queue) | Redis list `jobs:queue` |
| Ticket clipped at a cook's station | Redis list `jobs:processing` + a `lease:<id>` key with a timeout |
| Cook (consumer / worker) | `python -m app.worker`, run as many as you like |
| Dish goes out, ticket spiked | `ack()` saves the result, then removes the id from `jobs:processing` |
| Cook walks out mid-order | lease expires, `reap()` puts the ticket back on the rail |
| Order that keeps burning | after 3 failed tries it moves to `jobs:dead` for a human to look at |

## What the scripts showed

Real LLM run (Groq, `openai/gpt-oss-20b`, on my laptop):

```
Caller waits (job = real LLM call, openai/gpt-oss-20b)
  POST /summaries/sync       1002 ms   (cooked at the counter, median of 3)
  POST /summaries             3.8 ms   (median of 20, returns 202 + job id)

12 jobs on the queue
  1 worker   drained in  10.7 s
  4 workers  drained in   3.4 s
```

Offline run (no key, fake 3 s LLM delay):

`python scripts/measure.py`

```
Caller waits (job = 3 s of work)
  POST /summaries/sync       3047 ms   (cooked at the counter)
  POST /summaries             2.7 ms   (median of 20, returns 202 + job id)

12 jobs on the queue, 1 s each
  1 worker   drained in  12.2 s
  4 workers  drained in   3.5 s
```

`python scripts/crash_demo.py` kills a worker in the middle of a job:

- **Pop and forget** (`BRPOP`): the job is off the queue and nowhere else. Status stays `running` forever. Nobody runs it again.
- **Claim + ack** (`BLMOVE` into a processing list, plus a lease): the job waits in `jobs:processing`. When the lease runs out, the next worker puts it back and finishes it. `attempts=2`, which is the catch: **a job can run twice**, so it must be safe to repeat (use an idempotency key for anything like refunds or emails).

Celery has the same switch: by default it acknowledges a task right before running it; `acks_late=True` moves the ack to after the task finishes. SQS does it with a visibility timeout.

## Files

```
app/
  config.py      REDIS_URL, JOB_SECONDS, LEASE_SECONDS, MAX_ATTEMPTS
  jobqueue.py    enqueue, claim, ack, fail (retry / dead-letter), reap
  llm.py         the real LLM call (OpenAI-compatible client pointed at Groq)
  tasks.py       the slow job: real LLM if GROQ_API_KEY is set, else a fixed delay
  worker.py      the worker loop  (--unsafe = pop and forget)
  main.py        FastAPI: POST /summaries, GET /summaries/{id}, GET /queue, POST /summaries/sync
scripts/
  measure.py     caller wait time + 1 vs 4 workers
  crash_demo.py  kill a worker mid-job, unsafe vs safe
tests/           12 tests, use fakeredis and never call the real LLM
.env.example     copy to .env and add your Groq key (.env is gitignored)
```

## Run it (Windows)

Start Redis with Docker (any terminal):

```
docker run -d --name jobs-redis -p 6379:6379 redis:7
```

Set up the project (PowerShell, in this folder):

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Real LLM (optional): copy `.env.example` to `.env` and put your Groq key in it. Free key at https://console.groq.com/keys

```
copy .env.example .env
```

Tests (no Redis, no key needed):

```
pytest -v
```

API in one terminal, a worker in another:

```
uvicorn app.main:app --reload
```

```
python -m app.worker
```

Then open http://127.0.0.1:8000/docs, call `POST /summaries`, and poll `GET /summaries/{job_id}`.

Not production-ready on purpose: no worker heartbeats (a job longer than the lease would be handed out twice), no priorities, no scheduling. For real projects use Celery, RQ, arq, Dramatiq or a managed queue (SQS, Pub/Sub); this exists to show what they do for you.
