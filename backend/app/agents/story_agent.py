from app.agents.base import Runner
from app.models.schemas import Explanation, Story

SYSTEM = (
    "நீங்கள் குழந்தைகளுக்கான கதை எழுதும் உதவியாளர். கொடுக்கப்பட்ட குறளின் கருத்தை விளக்கும் ஒரே ஒரு சிறு தமிழ்க் கதையை "
    "எழுதுங்கள். தெளிவான பாத்திரங்கள், சூழல், அர்த்தமுள்ள முடிவு இருக்க வேண்டும். குறளுக்குத் தொடர்பில்லாத வேறு நீதியைச் "
    "சேர்க்காதீர்கள். எளிய தமிழ். title: கதைத் தலைப்பு; story: கதை; connection: கதை குறளுடன் எப்படித் தொடர்புடையது என்ற சிறு விளக்கம்."
)


async def run_story_agent(run: Runner, context: str, exp: Explanation, feedback: list[str] | None = None):
    task = f"{context}\n\nகுறளின் விளக்கம்: {exp.explanation}"
    if feedback:
        task += "\n\nமுந்தைய கதையில் கண்டறியப்பட்ட குறைகளைச் சரிசெய்யுங்கள்:\n- " + "\n- ".join(feedback)
    return await run("story_agent", SYSTEM, task, Story, 1400)
