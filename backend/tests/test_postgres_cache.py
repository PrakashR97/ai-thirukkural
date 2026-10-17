"""Runs the same cache contract against PostgreSQL (skipped if the test DB is unreachable)."""
import os

import pytest

from app.services.cache_service import CacheService

URL = os.environ.get("TEST_DATABASE_URL", "postgresql://localhost:5432/thirukkural_test")


@pytest.fixture
def pg():
    try:
        c = CacheService("unused.db", URL)
    except Exception:
        pytest.skip("PostgreSQL test database not available")
    with c._conn() as conn:
        conn.execute("TRUNCATE kural_cache, usage_logs")
    yield c
    c.close()


def test_roundtrip_unicode_and_upsert(pg):
    data = {"explanation": "தமிழ்", "n": 1}
    assert pg.get(1, "m", "v") is None
    pg.put(1, "m", "v", data, "reviewed")
    assert pg.get(1, "m", "v") == data
    pg.put(1, "m", "v", {"explanation": "மாற்றம்"}, "reviewed")  # upsert, no duplicate-key error
    assert pg.get(1, "m", "v") == {"explanation": "மாற்றம்"}
    assert pg.get(1, "m", "other") is None  # different config version -> miss
    pg.delete(1, "m", "v")
    assert pg.get(1, "m", "v") is None


def test_usage_summary(pg):
    pg.log("explanation", kural_number=1, input_tokens=10, output_tokens=5)
    pg.log("cache", kural_number=1, cache_status="hit")
    pg.log("cache", kural_number=1, cache_status="miss")
    s = pg.usage_summary()
    assert s["openai_requests"] == 1 and s["input_tokens"] == 10 and s["cache_hits"] == 1 and s["cache_misses"] == 1


def test_api_uses_postgres_cache_and_avoids_second_generation(settings):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from tests.conftest import FakeRunner
    try:
        CacheService("unused.db", URL).close()
    except Exception:
        pytest.skip("PostgreSQL test database not available")
    r = FakeRunner()
    with TestClient(create_app(settings.model_copy(update={"database_url": URL}), runner=r)) as c:
        c.app.state.cache.delete(9, settings.openai_model, settings.cache_config_version)
        assert c.post("/api/kurals/9/explain").json()["cached"] is False
        assert c.post("/api/kurals/9/explain").json()["cached"] is True
        assert len(r.calls) == 3
        c.app.state.cache.delete(9, settings.openai_model, settings.cache_config_version)
