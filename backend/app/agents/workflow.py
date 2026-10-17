"""Controlled generation workflow: explain -> story -> review (+ bounded correction)."""
import re
import unicodedata
from typing import Awaitable, Callable

from app.agents.base import AgentError, Runner, Usage
from app.agents.explanation_agent import run_explanation_agent
from app.agents.review_agent import run_review_agent
from app.agents.story_agent import run_story_agent
from app.models.schemas import ExplainResult, Explanation, Kural, Review, Story
from app.services.rag_service import RagService

TAMIL_RE = re.compile(r"[஀-௿]")

# (request_type, usage) callback so the caller can log each model call
UsageSink = Callable[[str, Usage, bool], None]


class ReviewFailed(Exception):
    """Review did not complete or did not approve within the correction limit."""


def _is_tamil(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and sum(1 for c in letters if TAMIL_RE.match(c)) / len(letters) > 0.6


def _local_issues(k: Kural, exp: Explanation, story: Story) -> tuple[list[str], str]:
    """Free deterministic checks. Returns (issues, correction_target)."""
    issues: list[str] = []
    exp_bad = story_bad = False
    if not exp.word_meanings:
        issues.append("word_meanings is empty")
        exp_bad = True
    verse = unicodedata.normalize("NFC", k.text)
    for w in exp.word_meanings:
        word = unicodedata.normalize("NFC", w.word).strip(" .,;:!?'\"‘’“”")
        if not word or word not in verse:
            issues.append(f"word '{w.word}' does not appear exactly in the Kural; quote words exactly as written in the Kural")
            exp_bad = True
    if not _is_tamil(exp.explanation) or not _is_tamil(exp.life_lesson):
        issues.append("explanation and life lesson must be in Tamil")
        exp_bad = True
    if not _is_tamil(story.story):
        issues.append("story must be in Tamil")
        story_bad = True
    target = "both" if exp_bad and story_bad else "explanation" if exp_bad else "story" if story_bad else "none"
    return issues, target


async def generate_reviewed(run: Runner, k: Kural, model: str, max_corrections: int,
                            sink: UsageSink | None = None) -> ExplainResult:
    sink = sink or (lambda *_: None)
    ctx = RagService.context(k)

    async def call(kind: str, coro):
        try:
            out, usage = await coro
        except AgentError:
            sink("review_failure" if kind == "review" else "generation_failure", Usage(), False)
            raise
        sink(kind, usage, True)
        return out

    exp = await call("explanation", run_explanation_agent(run, ctx))
    story = await call("story", run_story_agent(run, ctx, exp))

    attempt = 0
    while True:
        local, target = _local_issues(k, exp, story)
        issues = list(local)
        review: Review | None = None
        if not local:  # only pay for a review once the free checks pass
            try:
                review = await call("review", run_review_agent(run, ctx, exp, story))
            except AgentError as e:
                raise ReviewFailed(str(e)) from None
            if review.approved:
                return ExplainResult(
                    kural_number=k.number, word_meanings=exp.word_meanings, explanation=exp.explanation,
                    story=story, life_lesson=exp.life_lesson, review_status="reviewed",
                    review_notes=review.suggestions, model=model)
            issues = list(review.issues)
            target = review.correction_target if review.correction_target in ("explanation", "story", "both") else "both"
        if attempt >= max_corrections:
            raise ReviewFailed("review did not approve within the correction limit")
        attempt += 1
        # Regenerate only what is flawed; a new explanation changes the story's input, so the story follows it.
        if target in ("explanation", "both"):
            exp = await call("explanation", run_explanation_agent(run, ctx, issues))
            story = await call("story", run_story_agent(run, ctx, exp, issues))
        else:
            story = await call("story", run_story_agent(run, ctx, exp, issues))
