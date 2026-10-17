import asyncio

import pytest

from app.agents.base import AgentError
from app.agents.workflow import ReviewFailed, generate_reviewed
from app.models.schemas import Review
from tests.conftest import FakeRunner


def test_explain_generates_then_caches(make_client):
    r = FakeRunner()
    c = make_client(runner=r)
    a = c.post("/api/kurals/1/explain")
    assert a.status_code == 200
    j = a.json()
    assert j["review_status"] == "reviewed" and j["cached"] is False
    assert j["word_meanings"] and j["story"]["story"] and j["life_lesson"] and j["explanation"]
    assert r.calls == ["explanation_agent", "story_agent", "review_agent"]
    b = c.post("/api/kurals/1/explain").json()
    assert b["cached"] is True and len(r.calls) == 3  # no new model calls
    u = c.get("/api/usage").json()
    assert u["openai_requests"] == 3 and u["cache_hits"] == 1 and u["cache_misses"] == 1
    assert u["input_tokens"] == 300 and u["estimated_cost_usd"] is None


def test_config_change_invalidates_cache(make_client):
    r = FakeRunner()
    c = make_client(runner=r)
    c.post("/api/kurals/2/explain")
    c.app.state.settings = c.app.state.settings.model_copy(update={"openai_model": "other-model"})
    c.post("/api/kurals/2/explain")
    assert len(r.calls) == 6


def test_limited_correction_then_success(make_client):
    r = FakeRunner(reviews=[Review(approved=False, issues=["story drifts"], correction_target="story"), Review(approved=True)])
    c = make_client(runner=r)
    assert c.post("/api/kurals/3/explain").status_code == 200
    assert r.calls.count("review_agent") == 2
    assert any("story drifts" in t for t in r.tasks[-2:])


def test_correction_limit_and_not_cached(make_client):
    bad = Review(approved=False, issues=["contradiction"], correction_target="both")
    r = FakeRunner(reviews=[bad] * 5)
    c = make_client(runner=r)
    resp = c.post("/api/kurals/4/explain")
    assert resp.status_code == 502
    assert r.calls.count("review_agent") == 2  # initial + 1 correction, then stop
    assert "Traceback" not in resp.text
    assert c.app.state.cache.get(4, c.app.state.settings.openai_model, c.app.state.settings.cache_config_version) is None
    assert c.get("/api/usage").json()["generation_failures"] == 0


@pytest.mark.parametrize("agent", ["explanation_agent", "story_agent", "review_agent"])
def test_agent_failure_returns_502_not_cached(make_client, agent):
    c = make_client(runner=FakeRunner(fail_on=agent))
    resp = c.post("/api/kurals/5/explain")
    assert resp.status_code == 502 and "Boom" not in resp.text
    s = c.app.state
    assert s.cache.get(5, s.settings.openai_model, s.settings.cache_config_version) is None
    u = c.get("/api/usage").json()
    assert u["review_failures"] + u["generation_failures"] == 1


def test_non_tamil_output_is_not_accepted(settings):
    from app.services.dataset_service import DatasetService
    from app.models.schemas import Explanation, Story, WordMeaning

    class EnglishRunner(FakeRunner):
        async def __call__(self, name, system, task, output_model, max_tokens):
            out, u = await super().__call__(name, system, task, output_model, max_tokens)
            if output_model is Explanation:
                out.explanation = "This is English only."
            return out, u

    from app.config import DATA_DIR
    k = DatasetService(DATA_DIR / "thirukkural.json", DATA_DIR / "chapters.json").get(1)
    with pytest.raises(ReviewFailed):
        asyncio.run(generate_reviewed(EnglishRunner(), k, "m", 1))


def test_concurrent_requests_generate_once(make_client):
    import threading
    r = FakeRunner()
    c = make_client(runner=r)
    out = []
    ts = [threading.Thread(target=lambda: out.append(c.post("/api/kurals/6/explain").status_code)) for _ in range(4)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert out == [200] * 4
    assert r.calls.count("explanation_agent") == 1


def test_prompts_contain_only_selected_kural(make_client):
    r = FakeRunner()
    c = make_client(runner=r)
    c.post("/api/kurals/1/explain")
    assert all("குறள் எண்: 1\n" in t for t in r.tasks)
    assert not any("குறள் எண்: 2\n" in t for t in r.tasks)


def test_word_not_in_kural_triggers_correction(make_client):
    from app.models.schemas import Explanation

    class AlteredWordRunner(FakeRunner):
        n = 0
        async def __call__(self, name, system, task, output_model, max_tokens):
            out, u = await super().__call__(name, system, task, output_model, max_tokens)
            if output_model is Explanation and self.calls.count("explanation_agent") == 1:
                out.word_meanings[0].word = "அகரமே"  # not in the verse
            return out, u

    r = AlteredWordRunner()
    c = make_client(runner=r)
    assert c.post("/api/kurals/1/explain").status_code == 200
    assert r.calls.count("explanation_agent") == 2  # corrected once


def test_local_failure_skips_review_call_and_story_reused(make_client):
    """Altered word -> corrected without spending a review on the bad draft."""
    from app.models.schemas import Explanation

    class Bad(FakeRunner):
        async def __call__(self, name, system, task, output_model, max_tokens):
            out, u = await super().__call__(name, system, task, output_model, max_tokens)
            if output_model is Explanation and self.calls.count("explanation_agent") == 1:
                out.word_meanings[0].word = "அகரமே"
            return out, u

    r = Bad()
    c = make_client(runner=r)
    assert c.post("/api/kurals/1/explain").status_code == 200
    assert r.calls.count("review_agent") == 1  # reviewed once, on the corrected draft only


def test_story_only_correction_keeps_explanation(make_client):
    from app.models.schemas import Review
    r = FakeRunner(reviews=[Review(approved=False, issues=["story drifts"], correction_target="story"), Review(approved=True)])
    c = make_client(runner=r)
    assert c.post("/api/kurals/3/explain").status_code == 200
    assert r.calls.count("explanation_agent") == 1 and r.calls.count("story_agent") == 2
