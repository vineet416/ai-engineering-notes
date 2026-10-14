import pytest


def test_creates_task(client):
    res = client.post("/tasks", json={"title": "Write unit tests"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Write unit tests"
    assert data["done"] is False
    assert isinstance(data["id"], int)


def test_spaces_around_title_are_removed(client):
    assert client.post("/tasks", json={"title": "  Fix login bug  "}).json()["title"] == "Fix login bug"


@pytest.mark.parametrize(
    "body",
    [
        {"title": "ab"},
        {"title": "x" * 101},
        {"title": ""},
        {"title": None},
        {"title": 42},
        {},
    ],
    ids=["too-short", "too-long", "empty", "null", "number", "missing"],
)
def test_pydantic_rejects_bad_body(client, body):
    assert client.post("/tasks", json=body).status_code == 422


def test_short_title_error_message(client):
    detail = client.post("/tasks", json={"title": "ab"}).json()["detail"][0]
    assert detail["loc"] == ["body", "title"]
    assert "at least 3 characters" in detail["msg"]


def test_duplicate_title_is_400(client, add_task):
    add_task("Deploy to staging")
    res = client.post("/tasks", json={"title": "Deploy to staging"})
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


@pytest.mark.parametrize("same", ["deploy to staging", "DEPLOY TO STAGING", " Deploy to staging "])
def test_duplicate_check_ignores_case_and_spaces(client, add_task, same):
    add_task("Deploy to staging")
    assert client.post("/tasks", json={"title": same}).status_code == 400


def test_sixth_open_task_is_refused(client, add_task):
    for n in range(5):
        add_task(f"Open task {n}")
    res = client.post("/tasks", json={"title": "Sixth task"})
    assert res.status_code == 400
    assert "5 open tasks" in res.json()["detail"]


def test_done_tasks_dont_count_toward_limit(client, add_task):
    ids = [add_task(f"Open task {n}")["id"] for n in range(5)]
    client.patch(f"/tasks/{ids[0]}", json={"done": True})
    assert client.post("/tasks", json={"title": "Sixth task"}).status_code == 201
