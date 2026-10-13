# core: a tiny fake database (just a Python dict in memory).
# In a real project this file would open a connection to Postgres, MySQL, etc.

from typing import Dict

from app.models.task import Task

tasks_table: Dict[int, Task] = {}
_next_id = 1


def next_id() -> int:
    global _next_id
    value = _next_id
    _next_id += 1
    return value


def reset() -> None:
    """Empty the fake database (used by tests)."""
    global _next_id
    tasks_table.clear()
    _next_id = 1
