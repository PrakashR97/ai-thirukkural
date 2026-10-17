def test_health(make_client):
    j = make_client().get("/api/health").json()
    assert j["status"] == "ok" and j["kurals"] == 1330


def test_list_and_pagination(make_client):
    c = make_client()
    j = c.get("/api/kurals?page=1&page_size=100").json()
    assert j["total"] == 1330 and len(j["items"]) == 100
    seen = set()
    for p in range(1, 15):
        seen |= {k["number"] for k in c.get(f"/api/kurals?page={p}&page_size=100").json()["items"]}
    assert seen == set(range(1, 1331))


def test_detail_and_invalid(make_client):
    c = make_client()
    assert c.get("/api/kurals/1").json()["chapter_name"] == "கடவுள் வாழ்த்து"
    for bad in (0, 1331, -1):
        assert c.get(f"/api/kurals/{bad}").status_code == 404
    assert c.get("/api/kurals/abc").status_code == 422
    assert c.post("/api/kurals/9999/explain").status_code == 404


def test_sections_chapters(make_client):
    c = make_client()
    assert len(c.get("/api/sections").json()) == 3
    assert len(c.get("/api/chapters").json()) == 133
    assert len(c.get("/api/chapters?section=3").json()) == 25
    ks = c.get("/api/chapters/2/kurals").json()
    assert [k["number"] for k in ks] == list(range(11, 21))
    assert c.get("/api/chapters/134/kurals").status_code == 404


def test_search(make_client):
    c = make_client()
    assert [k["number"] for k in c.get("/api/search?q=7").json()] == [7]
    assert c.get("/api/search?q=5000").json() == []
    r = c.get("/api/search?q=அகர").json()
    assert r and r[0]["number"] == 1
    assert c.get("/api/search?q=").status_code == 422


def test_browsing_never_calls_ai(make_client):
    from tests.conftest import FakeRunner
    r = FakeRunner()
    c = make_client(runner=r)
    c.get("/api/kurals"); c.get("/api/kurals/5"); c.get("/api/search?q=அறம்"); c.get("/api/chapters")
    assert r.calls == []


def test_missing_config_browsing_ok_explain_503(make_client):
    c = make_client(openai_api_key="")
    assert c.get("/api/kurals/1").status_code == 200
    assert c.post("/api/kurals/1/explain").status_code == 503
