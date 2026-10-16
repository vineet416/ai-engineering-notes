from app.core.database import get_engine, make_engine
from app.main import app


def test_live_returns_200(client):
    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json() == {"status": "alive"}


def test_live_stays_200_when_database_is_gone(client, tmp_path):
    # Liveness must not depend on the database. If it did, Kubernetes would
    # restart every pod during a DB outage, and restarting fixes nothing.
    app.dependency_overrides[get_engine] = lambda: make_engine(str(tmp_path / "missing.db"))
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 503
