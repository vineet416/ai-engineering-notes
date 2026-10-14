# Shared test setup. pytest picks this file up on its own.
#
# 1. One in-memory SQLite database for the whole test run (tables created once).
# 2. Every route that asks for get_db gets a session on THAT database instead
#    of tasks.db, through app.dependency_overrides.
# 3. After each test, every row is wiped, so the next test starts clean.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import API_KEY
from app.core.database import Base, get_db
from app.main import app

# "sqlite://" with no file name = a database that only lives in RAM.
# StaticPool = reuse one connection. Without it, each new connection
# would get its own empty in-memory DB and you'd see "no such table".
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
    # wipe every table so tests can't see each other's data
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    # plain TestClient(app), not "with TestClient(app)": the "with" form runs
    # startup, which would create the real tasks.db file
    test_client = TestClient(app)
    test_client.headers["X-API-Key"] = API_KEY
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client(db):
    """Same app, but no API key header."""
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def add_task(client):
    def _add(title):
        res = client.post("/tasks", json={"title": title})
        assert res.status_code == 201, res.text
        return res.json()
    return _add
