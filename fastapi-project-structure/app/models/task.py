# models: how a task is STORED in the database.
# This is the shape of a row in the table, including fields the user never sends.

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    created_at: datetime = field(default_factory=datetime.now)
