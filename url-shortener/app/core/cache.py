# A tiny in-memory LRU cache: code -> (link id, long URL).
# In production this would be Redis, shared by every server.
# Short links never change after they're created, so there's nothing to invalidate.
from collections import OrderedDict
from typing import Optional, Tuple

from app.core.config import CACHE_SIZE


class LRUCache:
    def __init__(self, max_size: int):
        self.max_size = max_size
        self._data: "OrderedDict[str, Tuple[int, str]]" = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Tuple[int, str]]:
        if key in self._data:
            self._data.move_to_end(key)  # mark as recently used
            self.hits += 1
            return self._data[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Tuple[int, str]) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self.max_size:
            self._data.popitem(last=False)  # drop the least recently used

    def clear(self) -> None:
        self._data.clear()
        self.hits = 0
        self.misses = 0

    def __len__(self) -> int:
        return len(self._data)


link_cache = LRUCache(CACHE_SIZE)
