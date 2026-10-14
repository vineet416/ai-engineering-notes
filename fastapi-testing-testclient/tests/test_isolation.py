# Proof that the override + cleanup work.
from app.models.task import Task


def test_api_writes_go_to_the_test_db(client, db):
    client.post("/tasks", json={"title": "Where did I go?"})
    assert [t.title for t in db.query(Task).all()] == ["Where did I go?"]


def test_a_test_leaves_data_behind(client, add_task):
    add_task("Leftover?")
    assert len(client.get("/tasks").json()) == 1


def test_next_test_sees_nothing(client):
    assert client.get("/tasks").json() == []


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
