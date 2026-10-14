# Pydantic: what the client may send, and what we send back.
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)


class TaskUpdate(BaseModel):
    # Both optional, so the client can change just one of them
    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    done: Optional[bool] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    done: bool
    created_at: datetime
