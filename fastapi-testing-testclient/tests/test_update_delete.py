def test_mark_done(client, add_task):
    task = add_task("Review PR")
    res = client.patch(f"/tasks/{task['id']}", json={"done": True})
    assert res.status_code == 200
    assert res.json()["done"] is True


def test_rename(client, add_task):
    task = add_task("Review PR")
    res = client.patch(f"/tasks/{task['id']}", json={"title": "Review PR #12"})
    assert res.json()["title"] == "Review PR #12"


def test_rename_to_existing_title_is_400(client, add_task):
    add_task("Review PR")
    other = add_task("Write docs")
    assert client.patch(f"/tasks/{other['id']}", json={"title": "review pr"}).status_code == 400


def test_rename_keeping_own_title_is_fine(client, add_task):
    task = add_task("Review PR")
    assert client.patch(f"/tasks/{task['id']}", json={"title": "Review PR"}).status_code == 200


def test_update_with_too_short_title_is_422(client, add_task):
    task = add_task("Review PR")
    assert client.patch(f"/tasks/{task['id']}", json={"title": "no"}).status_code == 422


def test_update_unknown_task_is_404(client):
    assert client.patch("/tasks/77", json={"done": True}).status_code == 404


def test_delete(client, add_task):
    task = add_task("Remove me")
    res = client.delete(f"/tasks/{task['id']}")
    assert res.status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_delete_unknown_task_is_404(client):
    assert client.delete("/tasks/77").status_code == 404
