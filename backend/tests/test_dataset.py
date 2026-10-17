import hashlib

from app.config import DATA_DIR
from app.services.dataset_service import DatasetService


def _ds():
    return DatasetService(DATA_DIR / "thirukkural.json", DATA_DIR / "chapters.json")


def test_validation_report_clean():
    r = _ds().report
    assert r.ok, r.problems
    assert r.total == r.unique == 1330


def test_numbers_cover_1_to_1330():
    assert [k.number for k in _ds().kurals] == list(range(1, 1331))


def test_text_matches_source_exactly(raw_dataset):
    ds = _ds()
    assert all(k.text == raw_dataset[k.number - 1] for k in ds.kurals)
    assert ds.get(1).line1 == "அகர முதல எழுத்தெல்லாம் ஆதி"


def test_structure():
    ds = _ds()
    assert len(ds.chapters) == 133 and len(ds.sections) == 3
    assert all(len(ds.chapter_kurals(c.number)) == 10 for c in ds.chapters)
    assert ds.get(380).section_number == 1 and ds.get(381).section_number == 2
    assert ds.get(1080).section_number == 2 and ds.get(1081).section_number == 3
    assert ds.get(1330).chapter_number == 133


def test_source_file_not_modified_by_loading(raw_dataset):
    before = hashlib.sha256((DATA_DIR / "thirukkural.json").read_bytes()).hexdigest()
    _ds()
    assert hashlib.sha256((DATA_DIR / "thirukkural.json").read_bytes()).hexdigest() == before


def test_validator_detects_problems(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('["அ\\nஆ", "அ\\nஆ", "english only", ""]', encoding="utf-8")
    r = DatasetService(bad, DATA_DIR / "chapters.json").report
    assert not r.ok
    text = " ".join(r.problems)
    assert "duplicate" in text and "no Tamil" in text and "empty" in text and "expected 1330" in text
