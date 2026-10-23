import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.main import app, get_redis


@pytest.fixture
def r():
    # In-memory Redis (with Lua support), so tests need no server.
    return fakeredis.FakeRedis()


@pytest.fixture
def client(r):
    app.dependency_overrides[get_redis] = lambda: r
    yield TestClient(app)
    app.dependency_overrides.clear()
