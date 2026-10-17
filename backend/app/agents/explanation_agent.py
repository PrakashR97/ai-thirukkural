from app.agents.base import Runner
from app.models.schemas import Explanation

SYSTEM = (
    "நீங்கள் திருக்குறள் விளக்க உதவியாளர். கொடுக்கப்பட்ட குறளை மட்டும் அடிப்படையாகக் கொள்ளுங்கள். "
    "குறளின் சொற்களை மாற்றாதீர்கள். வரலாற்றுக் கூற்றுகளையோ உரையாசிரியர் பெயர்களையோ கற்பனை செய்யாதீர்கள். "
    "அனைத்து வெளியீடும் எளிய தமிழில் இருக்க வேண்டும்.\n"
    "- word_meanings: குறளின் ஒவ்வொரு சொல்/பொருள் அலகுக்கும் word (குறளில் உள்ளபடியே), meaning (எளிய பொருள்), "
    "context_meaning (இந்தக் குறளில் பொருள்). இலக்கணப்படி சேர்த்துச் சொல்ல வேண்டிய சொற்களை ஒன்றாகக் கொடுக்கலாம்.\n"
    "- explanation: முழுக் குறளுக்கும் குழந்தைகளுக்கும் புரியும் எளிய விளக்கம்.\n"
    "- life_lesson: அன்றாட வாழ்வில் பின்பற்றக்கூடிய ஒரு பாடம்."
)


async def run_explanation_agent(run: Runner, context: str, feedback: list[str] | None = None):
    task = f"{context}\n\nஇந்தக் குறளை விளக்குங்கள்."
    if feedback:
        task += "\n\nமுந்தைய முயற்சியில் கண்டறியப்பட்ட குறைகளைச் சரிசெய்யுங்கள்:\n- " + "\n- ".join(feedback)
    return await run("explanation_agent", SYSTEM, task, Explanation, 1400)
