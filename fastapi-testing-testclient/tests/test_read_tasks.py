def test_empty_list(client):
    assert client.get("/tasks").json() == []


def test_list_keeps_creation_order(client, add_task):
    for title in ["First task", "Second task", "Third task"]:
        add_task(title)
    assert [t["title"] for t in client.get("/tasks").json()] == ["First task", "Second task", "Third task"]


def test_filter_only_done(client, add_task):
    done = add_task("Finished one")
    add_task("Still open")
    client.patch(f"/tasks/{done['id']}", json={"done": True})
    assert [t["title"] for t in client.get("/tasks", params={"done": True}).json()] == ["Finished one"]


def test_filter_only_open(client, add_task):
    done = add_task("Finished one")
    add_task("Still open")
    client.patch(f"/tasks/{done['id']}", json={"done": True})
    assert [t["title"] for t in client.get("/tasks", params={"done": False}).json()] == ["Still open"]


def test_get_by_id(client, add_task):
    task = add_task("Look me up")
    res = client.get(f"/tasks/{task['id']}")
    assert res.status_code == 200
    assert res.json() == task


def test_unknown_id_is_404(client):
    res = client.get("/tasks/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Task 999 not found"


def test_id_must_be_a_number(client):
    assert client.get("/tasks/abc").status_code == 422
