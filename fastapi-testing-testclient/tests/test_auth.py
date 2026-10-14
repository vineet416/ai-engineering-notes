# Write endpoints need X-API-Key. Reading doesn't.
import pytest

from app.core.security import require_api_key
from app.main import app


def test_reading_needs_no_key(anon_client):
    assert anon_client.get("/tasks").status_code == 200


@pytest.mark.parametrize(
    "method, url, body",
    [("post", "/tasks", {"title": "Sneaky task"}), ("patch", "/tasks/1", {"done": True}), ("delete", "/tasks/1", None)],
    ids=["create", "update", "delete"],
)
def test_writes_without_key_are_401(anon_client, method, url, body):
    kwargs = {"json": body} if body is not None else {}
    assert anon_client.request(method, url, **kwargs).status_code == 401


def test_wrong_key_is_401(anon_client):
    res = anon_client.post("/tasks", json={"title": "Sneaky task"}, headers={"X-API-Key": "guess"})
    assert res.status_code == 401


def test_auth_can_be_overridden_too(anon_client):
    # Same trick as the database: swap the dependency for the length of one test
    app.dependency_overrides[require_api_key] = lambda: "test-user"
    assert anon_client.post("/tasks", json={"title": "No key needed"}).status_code == 201
