# HTTP layer. Every route gets its session from Depends(get_db).
# Reading is public. Writing needs the API key (require_api_key).
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_api_key
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services import task_service
from app.services.task_service import TaskError, TaskNotFound

router = APIRouter(prefix="/tasks", tags=["Tasks"])
write_access = [Depends(require_api_key)]


def _http_error(err: Exception) -> HTTPException:
    if isinstance(err, TaskNotFound):
        return HTTPException(status_code=404, detail=str(err))
    return HTTPException(status_code=400, detail=str(err))


@router.get("", response_model=List[TaskOut])
def list_tasks(done: Optional[bool] = None, db: Session = Depends(get_db)):
    return task_service.list_tasks(db, done)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    try:
        return task_service.get_task(db, task_id)
    except TaskNotFound as err:
        raise _http_error(err)


@router.post("", response_model=TaskOut, status_code=201, dependencies=write_access)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    try:
        return task_service.create_task(db, payload.title)
    except TaskError as err:
        raise _http_error(err)


@router.patch("/{task_id}", response_model=TaskOut, dependencies=write_access)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    try:
        return task_service.update_task(db, task_id, payload.title, payload.done)
    except (TaskError, TaskNotFound) as err:
        raise _http_error(err)


@router.delete("/{task_id}", status_code=204, dependencies=write_access)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    try:
        task_service.delete_task(db, task_id)
    except TaskNotFound as err:
        raise _http_error(err)
