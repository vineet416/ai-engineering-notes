def test_create_and_list_tasks(client):
    res = client.post("/tasks", json={"title": "Write health checks"})
    assert res.status_code == 201
    assert client.get("/tasks").json() == [{"id": 1, "title": "Write health checks"}]


def test_short_title_rejected_by_pydantic(client):
    assert client.post("/tasks", json={"title": "ab"}).status_code == 422
