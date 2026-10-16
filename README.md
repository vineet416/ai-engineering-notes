# AI Engineering Notes

Small, working projects I build while learning backend and AI engineering.
Each folder is one topic: real code you can run, with tests, and a short README explaining how it works.

## Projects

| Folder | What it shows | Stack |
|---|---|---|
| [fastapi-project-structure](./fastapi-project-structure) | How to split a growing FastAPI app into routers, services, schemas (Pydantic), models and core, so business logic stays out of the routes | FastAPI, Pydantic, pytest |
| [fastapi-testing-testclient](./fastapi-testing-testclient) | Testing FastAPI routes with pytest and TestClient. `dependency_overrides` swaps the real database for an in-memory SQLite one (and swaps the API key check in one test). 44 tests, under a second | FastAPI, SQLAlchemy, Pydantic, pytest |
| [url-shortener](./url-shortener) | A working URL shortener built from the classic system design question: counter + base62 IDs (and a script showing 1,935 collisions per 1M links with hashing), 302 redirects, an LRU cache in front of the database, click analytics saved in a background task. 28 tests | FastAPI, SQLAlchemy, Pydantic, pytest |
| [health-checks](./health-checks) | Liveness vs readiness health checks. `/health/live` only says the process is up; `/health/ready` runs a real DB query and checks an outside API with timeouts, in parallel, and returns 503 when the database is down (degraded, not 503, when only a non-critical API fails). Example Kubernetes probes. 12 tests | FastAPI, SQLAlchemy, Pydantic, pytest |

More topics get added here as I build them.

## Running any project

Each folder is self-contained. From inside a project folder:

```
python -m venv venv
venv\Scripts\activate        # on Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Then follow that folder's README.

## About

I'm Vineet. I'm sharing what I learn and build, one topic at a time, on LinkedIn and here on GitHub.

Follow along on LinkedIn: [linkedin.com/in/vineet416](https://www.linkedin.com/in/vineet416/)
