# Shared test setup. Same trick as my testing build:
# every route gets an in-memory SQLite database instead of links.db.
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.cache import link_cache
from app.core.database import Base, get_db, get_session_factory
from app.main import app

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine, autoflush=False)
Base.metadata.create_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestSession()
    yield session
    session.close()
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    link_cache.clear()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    # the click logger opens its own session, so point it at the test DB too
    app.dependency_overrides[get_session_factory] = lambda: TestSession
    # follow_redirects=False so we can check the 302 itself
    yield TestClient(app, follow_redirects=False)
    app.dependency_overrides.clear()


@pytest.fixture
def shorten(client):
    def _shorten(url, alias=None):
        body = {"url": url}
        if alias:
            body["alias"] = alias
        res = client.post("/shorten", json=body)
        assert res.status_code == 201, res.text
        return res.json()
    return _shorten
