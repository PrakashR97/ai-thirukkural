from pydantic import BaseModel, Field


class Kural(BaseModel):
    number: int
    text: str
    line1: str
    line2: str
    section_number: int
    section_name: str
    chapter_number: int
    chapter_name: str


class Section(BaseModel):
    number: int
    name: str
    first_chapter: int
    last_chapter: int


class Chapter(BaseModel):
    number: int
    name: str
    section_number: int
    section_name: str
    first_kural: int
    last_kural: int


class KuralPage(BaseModel):
    items: list[Kural]
    total: int
    page: int
    page_size: int


# ---- AI output models (all user-facing text in Tamil) ----
class WordMeaning(BaseModel):
    word: str = Field(description="Original word/phrase exactly as it appears in the Kural")
    meaning: str = Field(description="Simple Tamil meaning")
    context_meaning: str = Field(description="Meaning in the context of this Kural, in Tamil")


class Explanation(BaseModel):
    word_meanings: list[WordMeaning]
    explanation: str = Field(description="Simple Tamil explanation of the whole Kural")
    life_lesson: str = Field(description="One practical life lesson in Tamil")


class Story(BaseModel):
    title: str
    story: str
    connection: str = Field(description="Short Tamil note on how the story connects to the Kural")


class Review(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list, description="Blocking problems only")
    suggestions: list[str] = Field(default_factory=list, description="Minor non-blocking notes")
    correction_target: str = Field(
        default="none", description="One of: none, explanation, story, both"
    )


class ExplainResult(BaseModel):
    kural_number: int
    word_meanings: list[WordMeaning]
    explanation: str
    story: Story
    life_lesson: str
    review_status: str  # "reviewed" (AI consistency review passed)
    review_notes: list[str] = Field(default_factory=list)
    model: str
    cached: bool = False
    disclaimer: str = (
        "இந்த விளக்கம், கதை மற்றும் சொற்பொருள்கள் செயற்கை நுண்ணறிவால் உருவாக்கப்பட்டவை; "
        "அதிகாரப்பூர்வ உரையுடன் சரிபார்க்கப்படவில்லை. மூல குறள் மட்டுமே தரவுத்தொகுப்பிலிருந்து எடுக்கப்பட்டது."
    )
