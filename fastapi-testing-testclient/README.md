# Testing FastAPI routes with pytest + TestClient

A small Task Tracker API (FastAPI, SQLAlchemy, SQLite, Pydantic) with **44 tests that finish in under a second**.
The tests never touch the real `tasks.db`. They use FastAPI's `dependency_overrides` to swap the database (and, in one test, the API key check).

## How the test setup works

All of it is in [`tests/conftest.py`](tests/conftest.py):

1. One in-memory SQLite database is created for the whole test run. Tables are created once.
2. `app.dependency_overrides[get_db] = lambda: db` makes every route that asks for `get_db` use that in-memory database.
3. After each test, every row is deleted, so the next test starts empty.
4. `TestClient` sends real HTTP requests to the app in-process. No server, no port.

```
app/
  core/config.py       settings (DATABASE_URL, API_KEY, MAX_OPEN_TASKS)
  core/database.py     engine + get_db()   <- swapped in tests
  core/security.py     require_api_key()   <- can be swapped too
  models/  schemas/  services/  routers/
tests/
  conftest.py          in-memory DB, the override, cleanup
  test_create_task.py  201, Pydantic 422s, duplicate + "max 5 open" rules
  test_read_tasks.py   list, filters, get by id, 404
  test_update_delete.py
  test_auth.py         401 without key, overriding the auth dependency
  test_isolation.py    proves writes land in the test DB and don't leak
  test_service.py      business rules called directly, no HTTP
```

## Run the tests (Windows, from this folder)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

Expected last line: `44 passed in 0.xx s`.

Want to see why the override matters? Comment out the `app.dependency_overrides[get_db]` line in the `client` fixture and run again: 25 tests fail with `no such table: tasks`, because they're now hitting the real database file.

## Run the API

```
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. Creating, updating and deleting need the header `X-API-Key: dev-key`. In /docs, each write endpoint shows an `x-api-key` field you can fill in.
