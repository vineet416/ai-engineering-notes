# Two kinds of tests, made possible by the folder split:
# 1) service tests: test business rules directly, no web server needed
# 2) API tests: test the full HTTP request

import pytest
from fastapi.testclient import TestClient

from app.core import database
from app.main import app
from app.services import task_service
from app.services.task_service import TaskError

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    database.reset()


# ---- service tests (plain Python, no HTTP) ----

def test_service_blocks_duplicate_titles():
    task_service.create_task("Learn FastAPI")
    with pytest.raises(TaskError):
        task_service.create_task("learn fastapi")


def test_service_limits_open_tasks():
    for i in range(5):
        task_service.create_task(f"Task number {i}")
    with pytest.raises(TaskError):
        task_service.create_task("One too many")


# ---- API tests (full request through the router) ----

def test_api_create_and_list():
    res = client.post("/tasks/", json={"title": "Write LinkedIn post"})
    assert res.status_code == 201
    assert res.json()["title"] == "Write LinkedIn post"
    assert len(client.get("/tasks/").json()) == 1


def test_api_rejects_short_title():
    # schema check: Pydantic rejects it before our code runs
    res = client.post("/tasks/", json={"title": "hi"})
    assert res.status_code == 422


def test_api_duplicate_returns_400():
    client.post("/tasks/", json={"title": "Read docs"})
    res = client.post("/tasks/", json={"title": "Read docs"})
    assert res.status_code == 400


def test_api_complete_task():
    task_id = client.post("/tasks/", json={"title": "Push to GitHub"}).json()["id"]
    res = client.patch(f"/tasks/{task_id}/done")
    assert res.json()["done"] is True
