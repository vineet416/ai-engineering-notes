import asyncio
import os
import time

from app.core.database import create_db_file, get_engine, make_engine
from app.health.checks import Check, database_check, http_check
from app.main import app
from app.routers.health import get_checks


async def ok():
    return None


async def broken():
    raise ConnectionError("connection refused")


async def hangs():
    await asyncio.sleep(10)


def use_checks(*checks):
    app.dependency_overrides[get_checks] = lambda: list(checks)


def test_ready_200_when_database_is_up(client):
    # real database check against the temp app.db (outside API swapped out)
    engine = app.dependency_overrides[get_engine]()
    use_checks(Check("database", database_check(engine)))
    res = client.get("/health/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"]["status"] == "up"
    assert "latency_ms" in body["checks"]["database"]


def test_ready_503_when_database_file_disappears(client, db_path):
    # The real demo: rename app.db while the app is running.
    engine = app.dependency_overrides[get_engine]()
    use_checks(Check("database", database_check(engine)))
    assert client.get("/health/ready").status_code == 200

    os.rename(db_path, str(db_path) + ".bak")
    res = client.get("/health/ready")
    assert res.status_code == 503
    db = res.json()["checks"]["database"]
    assert db["status"] == "down"
    assert "unable to open database file" in db["error"]

    os.rename(str(db_path) + ".bak", db_path)
    assert client.get("/health/ready").status_code == 200


def test_ready_503_when_table_is_missing(client, tmp_path):
    # An empty database file is not a healthy database.
    empty = tmp_path / "empty.db"
    create_db_file(str(empty))
    use_checks(Check("database", database_check(make_engine(str(empty)))))
    res = client.get("/health/ready")
    assert res.status_code == 503
    assert "no such table" in res.json()["checks"]["database"]["error"]


def test_critical_failure_gives_503(client):
    use_checks(Check("database", broken), Check("external_api", ok, critical=False))
    res = client.get("/health/ready")
    assert res.status_code == 503
    assert res.json()["status"] == "not_ready"
    assert res.json()["checks"]["database"]["error"] == "connection refused"


def test_non_critical_failure_is_degraded_not_503(client):
    # The outside API being down shouldn't pull every instance out of traffic.
    use_checks(Check("database", ok), Check("external_api", broken, critical=False))
    res = client.get("/health/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "degraded"
    assert res.json()["checks"]["external_api"]["status"] == "down"


def test_hanging_dependency_times_out(client, monkeypatch):
    monkeypatch.setattr("app.routers.health.CHECK_TIMEOUT_SECONDS", 0.3)
    use_checks(Check("database", hangs))
    start = time.perf_counter()
    res = client.get("/health/ready")
    elapsed = time.perf_counter() - start
    assert res.status_code == 503
    assert res.json()["checks"]["database"]["error"] == "timed out after 0.3s"
    assert elapsed < 2  # didn't wait the full 10 seconds


def test_checks_run_at_the_same_time(client, monkeypatch):
    # three checks that each take 0.3s should finish in ~0.3s, not ~0.9s
    async def slow():
        await asyncio.sleep(0.3)

    use_checks(Check("a", slow), Check("b", slow), Check("c", slow))
    start = time.perf_counter()
    res = client.get("/health/ready")
    assert res.status_code == 200
    assert time.perf_counter() - start < 0.8


def test_real_http_check_reports_unreachable_api(client):
    # port 9 on localhost has nothing listening, so the connection is refused
    use_checks(Check("external_api", http_check("http://127.0.0.1:9", 1.0), critical=False))
    res = client.get("/health/ready")
    assert res.status_code == 200
    assert res.json()["checks"]["external_api"]["status"] == "down"
