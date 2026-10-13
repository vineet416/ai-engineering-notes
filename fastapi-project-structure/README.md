# FastAPI project structure (small working example)

A tiny Task Tracker API, split the way a growing FastAPI project should be.

```
app/
  main.py          front door: creates the app, plugs in routers
  core/            shared settings + database connection
  models/          how data is STORED (database shape)
  schemas/         what comes IN and goes OUT (Pydantic checks)
  services/        business rules (no HTTP here)
  routers/         HTTP only: request in, call service, response out
tests/             service tests + API tests
```

How a request flows:
`POST /tasks/` -> router -> schema checks the body -> service applies the rules -> model saved in database -> schema shapes the response

## Run it (Windows, from this folder)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to try the endpoints.

## Run the tests

```
pytest -q
```
