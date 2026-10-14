# Business rules. No HTTP in here.
# The session is passed in, so whoever calls this decides which database it talks to.
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import MAX_OPEN_TASKS
from app.models.task import Task


class TaskError(Exception):
    """A rule was broken. The router turns this into a 400."""


class TaskNotFound(Exception):
    """No task with that id. The router turns this into a 404."""


def list_tasks(db: Session, done: Optional[bool] = None) -> List[Task]:
    query = select(Task).order_by(Task.id)
    if done is not None:
        query = query.where(Task.done == done)
    return list(db.scalars(query))


def get_task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise TaskNotFound(f"Task {task_id} not found")
    return task


def _check_title_free(db: Session, title: str, ignore_id: Optional[int] = None) -> None:
    query = select(Task).where(func.lower(Task.title) == title.lower())
    if ignore_id is not None:
        query = query.where(Task.id != ignore_id)
    if db.scalar(query) is not None:
        raise TaskError(f"A task called '{title}' already exists")


def create_task(db: Session, title: str) -> Task:
    title = title.strip()
    _check_title_free(db, title)

    open_count = db.scalar(select(func.count(Task.id)).where(Task.done.is_(False)))
    if open_count >= MAX_OPEN_TASKS:
        raise TaskError(f"You already have {MAX_OPEN_TASKS} open tasks. Finish one first")

    task = Task(title=title)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_id: int, title: Optional[str], done: Optional[bool]) -> Task:
    task = get_task(db, task_id)
    if title is not None:
        title = title.strip()
        _check_title_free(db, title, ignore_id=task_id)
        task.title = title
    if done is not None:
        task.done = done
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int) -> None:
    db.delete(get_task(db, task_id))
    db.commit()
