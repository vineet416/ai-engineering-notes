# schemas: what comes IN from the user and what goes OUT to the user.
# Pydantic checks the incoming data for us before our code even runs.

from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """What the user must send to create a task."""
    title: str = Field(min_length=3, max_length=100)


class TaskOut(BaseModel):
    """What we send back. We choose exactly which fields the user sees."""
    id: int
    title: str
    done: bool
    created_at: datetime
