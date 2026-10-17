"""Loads the read-only Kural dataset.

The source file is a JSON array of 1,330 verse strings (two lines each, joined by
"\\n"). It has no explicit numbers or chapter fields, so the Kural number is the
1-based array position and chapter/section follow the traditional structure
(10 Kurals per chapter; chapter ranges from data/chapters.json).
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.models.schemas import Chapter, Kural, Section

TAMIL_RE = re.compile(r"[஀-௿]")
TOTAL_KURALS = 1330
TOTAL_CHAPTERS = 133


@dataclass
class ValidationReport:
    ok: bool
    total: int
    unique: int
    problems: list[str] = field(default_factory=list)


class DatasetService:
    def __init__(self, dataset_path: Path, chapters_path: Path):
        with open(dataset_path, encoding="utf-8") as f:
            raw = json.load(f)
        with open(chapters_path, encoding="utf-8") as f:
            meta = json.load(f)
        self._raw: list = raw if isinstance(raw, list) else []
        self.sections = [Section(**s) for s in meta["sections"]]
        names: list[str] = meta["chapters"]
        self.report = self._validate(raw, names)

        self.chapters: list[Chapter] = []
        for i, name in enumerate(names, start=1):
            sec = next(s for s in self.sections if s.first_chapter <= i <= s.last_chapter)
            self.chapters.append(Chapter(
                number=i, name=name, section_number=sec.number, section_name=sec.name,
                first_kural=(i - 1) * 10 + 1, last_kural=i * 10))

        self.kurals: list[Kural] = []
        for idx, text in enumerate(self._raw, start=1):
            if not isinstance(text, str) or idx > TOTAL_KURALS:
                continue
            ch = self.chapters[(idx - 1) // 10]
            lines = text.split("\n")
            self.kurals.append(Kural(
                number=idx, text=text, line1=lines[0], line2="\n".join(lines[1:]),
                section_number=ch.section_number, section_name=ch.section_name,
                chapter_number=ch.number, chapter_name=ch.name))

    @staticmethod
    def _validate(raw, names) -> ValidationReport:
        problems: list[str] = []
        if not isinstance(raw, list):
            return ValidationReport(False, 0, 0, ["dataset root is not a list"])
        if len(raw) != TOTAL_KURALS:
            problems.append(f"expected {TOTAL_KURALS} records, found {len(raw)}")
        if len(names) != TOTAL_CHAPTERS:
            problems.append(f"expected {TOTAL_CHAPTERS} chapter names, found {len(names)}")
        seen: dict[str, int] = {}
        for i, t in enumerate(raw, start=1):
            if not isinstance(t, str) or not t.strip():
                problems.append(f"kural {i}: empty or non-string record")
                continue
            if not TAMIL_RE.search(t):
                problems.append(f"kural {i}: no Tamil characters")
            if t.count("\n") != 1:
                problems.append(f"kural {i}: expected 2 lines, got {t.count(chr(10)) + 1}")
            if t in seen:
                problems.append(f"kural {i}: duplicate of kural {seen[t]}")
            seen.setdefault(t, i)
        return ValidationReport(not problems, len(raw), len(seen), problems)

    def get(self, number: int) -> Kural | None:
        return self.kurals[number - 1] if 1 <= number <= len(self.kurals) else None

    def page(self, page: int, page_size: int, chapter: int | None = None,
             section: int | None = None) -> tuple[list[Kural], int]:
        items = self.kurals
        if chapter is not None:
            items = [k for k in items if k.chapter_number == chapter]
        if section is not None:
            items = [k for k in items if k.section_number == section]
        start = (page - 1) * page_size
        return items[start:start + page_size], len(items)

    def chapter_kurals(self, number: int) -> list[Kural]:
        return [k for k in self.kurals if k.chapter_number == number]
