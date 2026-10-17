from app.services.rate_limiter import DAY, HOUR, RateLimiter
from tests.conftest import FakeRunner


def test_unit_per_visitor_and_window():
    t = [0.0]
    rl = RateLimiter(2, 0, clock=lambda: t[0])
    assert rl.acquire("a")[0] and rl.acquire("a")[0]
    ok, retry, why = rl.acquire("a")
    assert not ok and why == "visitor" and 0 < retry <= HOUR
    assert rl.acquire("b")[0]            # other visitors unaffected
    t[0] = HOUR + 1
    assert rl.acquire("a")[0]            # window slid


def test_unit_global_daily_cap():
    t = [0.0]
    rl = RateLimiter(0, 2, clock=lambda: t[0])
    assert rl.acquire("a")[0] and rl.acquire("b")[0]
    ok, _, why = rl.acquire("c")
    assert not ok and why == "daily"
    t[0] = DAY + 1
    assert rl.acquire("c")[0]


def test_api_429_after_limit_but_cache_hits_still_free(make_client):
    r = FakeRunner()
    c = make_client(runner=r, rate_limit_per_hour=2)
    assert c.post("/api/kurals/1/explain").status_code == 200
    assert c.post("/api/kurals/2/explain").status_code == 200
    blocked = c.post("/api/kurals/3/explain")
    assert blocked.status_code == 429 and "Retry-After" in blocked.headers
    calls = len(r.calls)
    assert c.post("/api/kurals/1/explain").json()["cached"] is True   # cached: not limited
    assert c.post("/api/kurals/3/explain").status_code == 429
    assert len(r.calls) == calls                                       # blocked requests never reach the model
    assert c.get("/api/kurals/3").status_code == 200                   # browsing unaffected


def test_duplicate_concurrent_requests_spend_one_token(make_client):
    import threading
    c = make_client(runner=FakeRunner(), rate_limit_per_hour=1)
    out = []
    ts = [threading.Thread(target=lambda: out.append(c.post("/api/kurals/6/explain").status_code)) for _ in range(3)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert out == [200, 200, 200]


def test_proxy_header_only_trusted_when_enabled(make_client):
    c = make_client(runner=FakeRunner(), rate_limit_per_hour=1, trust_proxy=False)
    assert c.post("/api/kurals/1/explain", headers={"X-Real-IP": "1.1.1.1"}).status_code == 200
    assert c.post("/api/kurals/2/explain", headers={"X-Real-IP": "2.2.2.2"}).status_code == 429  # spoofing ignored
    c2 = make_client(runner=FakeRunner(), rate_limit_per_hour=1, trust_proxy=True)
    assert c2.post("/api/kurals/11/explain", headers={"X-Real-IP": "1.1.1.1"}).status_code == 200
    assert c2.post("/api/kurals/12/explain", headers={"X-Real-IP": "2.2.2.2"}).status_code == 200  # separate visitors
    assert c2.post("/api/kurals/13/explain", headers={"X-Real-IP": "1.1.1.1"}).status_code == 429
