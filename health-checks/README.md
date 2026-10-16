# Health checks that actually check health (FastAPI)

A small FastAPI app with two health endpoints that answer two different questions:

| Endpoint | Question it answers | What it checks | If it fails |
|---|---|---|---|
| `GET /health/live` | Is the process alive? | Nothing. It just answers. | Restart the app (Kubernetes `livenessProbe`) |
| `GET /health/ready` | Can this instance do real work right now? | Database round trip + outside API, each with a 2s timeout, all at the same time | Stop sending it traffic until it recovers (Kubernetes `readinessProbe`) |

Why the database is NOT in the liveness check: if the DB goes down and liveness fails, Kubernetes restarts every pod. The new pods still can't reach the DB, so they get restarted too. Restarting never fixes a database outage.

## What the readiness check does

- **Real database query.** `SELECT 1 FROM tasks LIMIT 1` on a fresh connection, so a missing file, a missing table or a locked DB all show up.
- **Status code, not just JSON.** Returns `503` when a critical dependency is down. Load balancers and Kubernetes only read the status code; `{"database": "down"}` inside a `200` still counts as healthy.
- **Timeouts.** Every check gets `CHECK_TIMEOUT_SECONDS` (2s). A hanging dependency is reported as `timed out after 2.0s` instead of hanging the probe.
- **Runs in parallel.** `asyncio.gather`, so three slow checks cost 2s, not 6s.
- **Critical vs non-critical.** The database is critical (`503`, out of traffic). The outside API is not: if it's down the response is `200` with `"status": "degraded"`, so one third-party outage doesn't pull every instance out of rotation.
- **SQLite opened with `mode=rw`.** By default SQLite silently creates a new empty database if the file is missing. Here a missing file is an error.

Example response when the database is gone:

```json
{
  "status": "not_ready",
  "checks": {
    "database": {"status": "down", "error": "unable to open database file", "critical": true, "latency_ms": 0.9},
    "external_api": {"status": "up", "critical": false, "latency_ms": 75.9}
  }
}
```

```
app/
  core/config.py         settings (DB_PATH, EXTERNAL_API_URL, CHECK_TIMEOUT_SECONDS)
  core/database.py       engine (mode=rw, NullPool), get_db(), get_engine()
  health/checks.py       database_check, http_check, run_checks (timeouts, parallel, critical flag)
  routers/health.py      GET /health/live, GET /health/ready
  routers/tasks.py       tiny tasks API so the app really needs its database
k8s/deployment.yaml      example liveness + readiness probes
tests/                   12 tests, each with its own temp database, no internet needed
```

## Run it (Windows, from this folder)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/health/live and http://127.0.0.1:8000/health/ready (or use http://127.0.0.1:8000/docs).

Then break the database while the server is running. In a second terminal in this folder:

```
ren app.db app.db.bak
```

Refresh both URLs. `/health/live` still says alive. `/health/ready` returns `503` with the reason. Rename it back (`ren app.db.bak app.db`) and readiness turns green again, no restart.

## In production I'd also

- Keep `/health/ready` off the public internet (or hide the `error` text), since it shows internal details.
- Cache the readiness result for a second or two if probes come from many places, so health checks don't become load on the database.
- Add a startup probe for apps that take a long time to boot (loading an ML model, warming a cache).
