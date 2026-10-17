import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from app.agents.base import AgentError, Usage
from app.config import DATA_DIR, Settings
from app.main import create_app
from app.models.schemas import Explanation, Review, Story, WordMeaning


class FakeRunner:
    """Stands in for the OpenAI-backed runner. Records calls; scripted reviews."""

    def __init__(self, reviews=None, fail_on=None):
        self.calls: list[str] = []
        self.tasks: list[str] = []
        self.reviews = list(reviews) if reviews is not None else None
        self.fail_on = fail_on

    async def __call__(self, name, system, task, output_model, max_tokens):
        self.calls.append(name)
        self.tasks.append(task)
        if self.fail_on == name:
            raise AgentError(f"{name} failed: Boom")
        u = Usage(100, 50)
        if output_model is Explanation:
            first = task.split("குறள்:\n", 1)[1].split()[0]
            return Explanation(word_meanings=[WordMeaning(word=first, meaning="அ என்னும் எழுத்து", context_meaning="முதல் எழுத்து")],
                               explanation="எழுத்துக்கள் அகரத்தில் தொடங்குவது போல உலகம் கடவுளிடமிருந்து தொடங்குகிறது.",
                               life_lesson="எப்போதும் அடிப்படையை மதிக்க வேண்டும்."), u
        if output_model is Story:
            return Story(title="முதல் படி", story="ஒரு சிறுவன் எழுத்துக்களைக் கற்றுக்கொண்டான்.", connection="முதல் எழுத்து போல அடிப்படை முக்கியம்."), u
        if output_model is Review:
            r = self.reviews.pop(0) if self.reviews else Review(approved=True)
            return r, u
        raise AssertionError(output_model)


@pytest.fixture
def settings(tmp_path):
    return Settings(openai_api_key="test-key", db_path=tmp_path / "t.db", _env_file=None)


@pytest.fixture
def make_client(settings):
    clients = []

    def _make(runner=None, **overrides):
        s = settings.model_copy(update=overrides)
        c = TestClient(create_app(s, runner=runner or FakeRunner()))
        c.__enter__()
        clients.append(c)
        return c

    yield _make
    for c in clients:
        c.__exit__(None, None, None)


@pytest.fixture(scope="session")
def raw_dataset():
    return json.load(open(DATA_DIR / "thirukkural.json", encoding="utf-8"))
