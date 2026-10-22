import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.main import app, get_redis


@pytest.fixture(autouse=True)
def no_real_llm(monkeypatch):
    # Tests never call the real LLM, even if your .env has a key.
    from app import config
    monkeypatch.setattr(config, "USE_LLM", False)
    monkeypatch.setattr(config, "JOB_SECONDS", 0.0)


@pytest.fixture
def r():
    # In-memory Redis, so tests need no server and start clean every time.
    return fakeredis.FakeRedis()


@pytest.fixture
def client(r):
    app.dependency_overrides[get_redis] = lambda: r
    yield TestClient(app)
    app.dependency_overrides.clear()
