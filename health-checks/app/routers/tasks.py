# A tiny real feature, so the app actually needs its database.
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.task import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)


class TaskOut(BaseModel):
    id: int
    title: str


@router.post("", response_model=TaskOut, status_code=201)
def create_task(body: TaskIn, db: Session = Depends(get_db)):
    task = Task(title=body.title)
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut(id=task.id, title=task.title)


@router.get("", response_model=List[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return [TaskOut(id=t.id, title=t.title) for t in db.query(Task).all()]
