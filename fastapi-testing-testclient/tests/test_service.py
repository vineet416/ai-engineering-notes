# The business rules, called directly. No HTTP, no TestClient.
import pytest

from app.services import task_service
from app.services.task_service import TaskError, TaskNotFound


def test_service_create_and_list(db):
    task_service.create_task(db, "Plan sprint")
    assert [t.title for t in task_service.list_tasks(db)] == ["Plan sprint"]


def test_service_refuses_duplicate(db):
    task_service.create_task(db, "Plan sprint")
    with pytest.raises(TaskError):
        task_service.create_task(db, "plan SPRINT")


def test_service_open_task_limit(db):
    for n in range(5):
        task_service.create_task(db, f"Open task {n}")
    with pytest.raises(TaskError):
        task_service.create_task(db, "One more")


def test_service_missing_task(db):
    with pytest.raises(TaskNotFound):
        task_service.get_task(db, 1)
