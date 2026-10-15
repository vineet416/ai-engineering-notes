# URL shortener (FastAPI)

A small, working URL shortener: create short links, redirect, and count clicks.
Built to see what changes when you move a whiteboard design into real code.

## What's inside

| Part | How it works here | What I'd change at bigger scale |
|---|---|---|
| ID generation | Insert the row, take the database's auto-increment id, add an offset, encode it in base62 (`0-9a-zA-Z`). Codes are 6 characters and can never collide. | Hand each server a block of ids (e.g. 1,000 at a time) from a shared counter so servers don't fight over one sequence. |
| Storage | SQLite + SQLAlchemy. `links` table (unique index on `code`) and a `clicks` table (index on `link_id`). | Postgres. Clicks go to a queue and a separate analytics store. |
| Redirects | `302`, not `301`. A 301 is cached by the browser, so repeat clicks never reach the server and never get counted. | Same. |
| Caching | In-memory LRU cache for code to URL. Links never change, so nothing to invalidate. See `/health` for hits and misses. | Redis, shared by every server. |
| Analytics | Each click is saved in a FastAPI `BackgroundTask`, after the redirect is already sent. `/stats/{code}` returns total, clicks per day and top referrers. | Push click events to a queue (Kafka, SQS) and aggregate in batches. |
| Validation | Pydantic `HttpUrl` rejects `javascript:` and other non-http links. Custom aliases are checked against reserved words like `docs`. | Also check URLs against a malware/phishing list. |

Why not hash the URL? Run `python scripts/hash_collisions.py`. Taking the first 7 characters of an MD5 hash gives **1,935 collisions in 1,000,000 URLs**. Each one would need an extra database check and a retry. The counter gives 0.

```
app/
  core/config.py            settings (BASE_URL, ID_OFFSET, reserved aliases)
  core/database.py          engine, get_db(), get_session_factory()
  core/cache.py             LRU cache (stand-in for Redis)
  models/link.py            Link and Click tables
  schemas/link.py           Pydantic request/response models
  services/codes.py         base62 encode/decode
  services/link_service.py  create, resolve (cache first), record_click, stats
  routers/links.py          POST /shorten, GET /{code}, GET /stats/{code}
scripts/
  hash_collisions.py        the experiment that changed my ID design
tests/                      28 tests, in-memory SQLite
```

## Run it (Windows, from this folder)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs, use `POST /shorten` with `{"url": "https://github.com"}`, then open the `short_url` it returns in your browser. Check `GET /stats/{code}` and `GET /health` afterwards.
