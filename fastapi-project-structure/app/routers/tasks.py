# routers: only the HTTP part. Receive the request, call the service, send the response.
# No business rules here. If you see an "if" about the business in a router, move it.

from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas.task import TaskCreate, TaskOut
from app.services import task_service
from app.services.task_service import TaskError

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=List[TaskOut])
def get_tasks():
    return task_service.list_tasks()


@router.post("/", response_model=TaskOut, status_code=201)
def add_task(payload: TaskCreate):
    try:
        return task_service.create_task(payload.title)
    except TaskError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.patch("/{task_id}/done", response_model=TaskOut)
def finish_task(task_id: int):
    try:
        return task_service.complete_task(task_id)
    except TaskError as err:
        raise HTTPException(status_code=404, detail=str(err))
