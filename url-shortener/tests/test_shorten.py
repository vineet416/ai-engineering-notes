# POST /shorten


def test_shorten_returns_code_and_short_url(shorten):
    data = shorten("https://fastapi.tiangolo.com/tutorial/")
    assert len(data["code"]) == 6
    assert data["short_url"].endswith("/" + data["code"])
    assert data["long_url"] == "https://fastapi.tiangolo.com/tutorial/"


def test_two_links_get_different_codes(shorten):
    a = shorten("https://example.com/a")
    b = shorten("https://example.com/b")
    assert a["code"] != b["code"]


def test_codes_follow_the_counter(shorten):
    a = shorten("https://example.com/a")
    b = shorten("https://example.com/b")
    # next id = next code
    from app.services.codes import decode
    assert decode(b["code"]) == decode(a["code"]) + 1


def test_custom_alias(shorten):
    data = shorten("https://www.linkedin.com/in/vineet416/", alias="vineet")
    assert data["code"] == "vineet"


def test_alias_taken_is_409(client, shorten):
    shorten("https://example.com/one", alias="launch")
    res = client.post("/shorten", json={"url": "https://example.com/two", "alias": "launch"})
    assert res.status_code == 409
    assert "already taken" in res.json()["detail"]


def test_reserved_alias_is_409(client):
    res = client.post("/shorten", json={"url": "https://example.com", "alias": "docs"})
    assert res.status_code == 409
    assert "reserved" in res.json()["detail"]


def test_not_a_url_is_422(client):
    res = client.post("/shorten", json={"url": "hello"})
    assert res.status_code == 422


def test_javascript_url_is_422(client):
    res = client.post("/shorten", json={"url": "javascript:alert(1)"})
    assert res.status_code == 422


def test_alias_with_bad_characters_is_422(client):
    res = client.post("/shorten", json={"url": "https://example.com", "alias": "my link!"})
    assert res.status_code == 422
