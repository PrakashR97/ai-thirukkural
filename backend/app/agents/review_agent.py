from app.agents.base import Runner
from app.models.schemas import Explanation, Review, Story

SYSTEM = (
    "You are a reviewer of Tamil Thirukkural content for children. You get the original Kural, word meanings, "
    "an explanation, a lesson and a story. Approve (approved=true) unless there is a BLOCKING defect. "
    "Blocking defects are only: (1) the meaning contradicts or clearly misreads the Kural; (2) the Kural wording "
    "is altered or major words are left unexplained; (3) invented citations, commentator names or unsupported "
    "historical claims; (4) the story's moral is unrelated to or contradicts the Kural; (5) user-facing text is not Tamil. "
    "Do NOT reject for style, depth, simplicity, missing nuance, or a different valid interpretation; put such "
    "points in 'suggestions' instead. You have no authoritative commentary, so never claim scholarly verification. "
    "If not approved, list only the blocking problems in 'issues' and set correction_target to "
    "'explanation', 'story' or 'both'."
)


async def run_review_agent(run: Runner, context: str, exp: Explanation, story: Story):
    wm = "\n".join(f"- {w.word}: {w.meaning} | {w.context_meaning}" for w in exp.word_meanings)
    task = (f"{context}\n\nசொற்பொருள்:\n{wm}\n\nவிளக்கம்: {exp.explanation}\n\nவாழ்க்கைப் பாடம்: {exp.life_lesson}\n\n"
            f"கதை ({story.title}): {story.story}\nதொடர்பு: {story.connection}")
    return await run("review_agent", SYSTEM, task, Review, 500)
