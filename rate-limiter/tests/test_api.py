import redis

from app import config
from app.main import app, get_redis


def test_11th_request_gets_429_with_retry_after(client):
    for _ in range(10):
        assert client.get("/api/quote", headers={"X-API-Key": "alice"}).status_code == 200
    res = client.get("/api/quote", headers={"X-API-Key": "alice"})
    assert res.status_code == 429
    assert int(res.headers["Retry-After"]) >= 1
    assert res.headers["X-RateLimit-Remaining"] == "0"


def test_other_api_key_is_not_blocked(client):
    for _ in range(11):
        client.get("/api/quote", headers={"X-API-Key": "alice"})
    assert client.get("/api/quote", headers={"X-API-Key": "bob"}).status_code == 200


class DeadRedis:
    """Looks like a Redis client, but every call fails."""

    def register_script(self, _):
        def run(**_):
            raise redis.ConnectionError("Redis is down")
        return run

    def pipeline(self):
        raise redis.ConnectionError("Redis is down")


def test_redis_down_fail_open_lets_requests_through(client, monkeypatch):
    monkeypatch.setattr(config, "FAIL_OPEN", True)
    app.dependency_overrides[get_redis] = lambda: DeadRedis()
    assert client.get("/api/quote").status_code == 200


def test_redis_down_fail_closed_returns_503(client, monkeypatch):
    monkeypatch.setattr(config, "FAIL_OPEN", False)
    app.dependency_overrides[get_redis] = lambda: DeadRedis()
    assert client.get("/api/quote").status_code == 503
