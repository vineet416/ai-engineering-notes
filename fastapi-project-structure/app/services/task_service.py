# services: the business logic. The actual rules of the app live here.
# This file knows nothing about HTTP, URLs or status codes.
# That means we can reuse it from an API, a script, a cron job or a test.

from typing import List

from app.core import database
from app.core.config import MAX_OPEN_TASKS
from app.models.task import Task


class TaskError(Exception):
    """Raised when a business rule is broken."""


def list_tasks() -> List[Task]:
    return list(database.tasks_table.values())


def create_task(title: str) -> Task:
    clean_title = title.strip()

    # Rule 1: no two tasks with the same title
    for task in database.tasks_table.values():
        if task.title.lower() == clean_title.lower():
            raise TaskError(f"A task called '{task.title}' already exists")

    # Rule 2: you can't have too many unfinished tasks at once
    open_tasks = [t for t in database.tasks_table.values() if not t.done]
    if len(open_tasks) >= MAX_OPEN_TASKS:
        raise TaskError(f"Finish a task first. Max {MAX_OPEN_TASKS} open tasks allowed")

    task = Task(id=database.next_id(), title=clean_title)
    database.tasks_table[task.id] = task
    return task


def complete_task(task_id: int) -> Task:
    task = database.tasks_table.get(task_id)
    if task is None:
        raise TaskError(f"Task {task_id} not found")
    task.done = True
    return task
