# Clicks are logged in a background task, then read back from /stats.
from datetime import date


def test_every_click_is_counted(client, shorten):
    code = shorten("https://example.com/launch")["code"]
    for _ in range(5):
        client.get("/" + code)
    stats = client.get(f"/stats/{code}").json()
    assert stats["total_clicks"] == 5


def test_cached_clicks_still_counted(client, shorten):
    # the cache skips the DB lookup, but the click still has to be logged
    code = shorten("https://example.com/cache-check")["code"]
    client.get("/" + code)
    client.get("/" + code)
    assert client.get(f"/stats/{code}").json()["total_clicks"] == 2


def test_clicks_by_day(client, shorten):
    code = shorten("https://example.com/today")["code"]
    client.get("/" + code)
    client.get("/" + code)
    by_day = client.get(f"/stats/{code}").json()["clicks_by_day"]
    assert sum(by_day.values()) == 2
    assert len(by_day) == 1
    # stored in UTC, so near midnight the date can differ from local time
    assert list(by_day)[0][:4] == str(date.today().year)


def test_top_referrers(client, shorten):
    code = shorten("https://example.com/post")["code"]
    client.get("/" + code, headers={"referer": "https://www.linkedin.com/"})
    client.get("/" + code, headers={"referer": "https://www.linkedin.com/"})
    client.get("/" + code, headers={"referer": "https://x.com/"})
    client.get("/" + code)  # no referer = typed in or opened from an app
    top = client.get(f"/stats/{code}").json()["top_referrers"]
    assert top[0] == {"referrer": "https://www.linkedin.com/", "clicks": 2}
    assert {"referrer": "direct", "clicks": 1} in top


def test_new_link_has_zero_clicks(client, shorten):
    code = shorten("https://example.com/fresh")["code"]
    stats = client.get(f"/stats/{code}").json()
    assert stats["total_clicks"] == 0
    assert stats["clicks_by_day"] == {}


def test_stats_for_unknown_code_is_404(client):
    assert client.get("/stats/nope123").status_code == 404


def test_clicks_only_counted_for_their_own_link(client, shorten):
    a = shorten("https://example.com/a")["code"]
    b = shorten("https://example.com/b")["code"]
    client.get("/" + a)
    client.get("/" + a)
    client.get("/" + b)
    assert client.get(f"/stats/{a}").json()["total_clicks"] == 2
    assert client.get(f"/stats/{b}").json()["total_clicks"] == 1
