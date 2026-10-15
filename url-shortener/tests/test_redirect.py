# GET /{code}
from app.core.cache import link_cache


def test_redirect_is_302_to_long_url(client, shorten):
    data = shorten("https://example.com/blog/post-1")
    res = client.get("/" + data["code"])
    assert res.status_code == 302
    assert res.headers["location"] == "https://example.com/blog/post-1"


def test_unknown_code_is_404(client):
    res = client.get("/nope123")
    assert res.status_code == 404


def test_health_and_docs_not_swallowed_by_code_route(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/docs").status_code == 200


def test_second_redirect_comes_from_cache(client, shorten):
    code = shorten("https://example.com/cached")["code"]
    client.get("/" + code)  # miss, goes to DB, fills cache
    client.get("/" + code)  # hit
    client.get("/" + code)  # hit
    assert link_cache.misses == 1
    assert link_cache.hits == 2


def test_cache_drops_least_recently_used():
    from app.core.cache import LRUCache
    cache = LRUCache(max_size=2)
    cache.set("a", (1, "https://a.com"))
    cache.set("b", (2, "https://b.com"))
    cache.get("a")                       # a is now most recent
    cache.set("c", (3, "https://c.com"))  # b gets dropped
    assert cache.get("b") is None
    assert cache.get("a") == (1, "https://a.com")
