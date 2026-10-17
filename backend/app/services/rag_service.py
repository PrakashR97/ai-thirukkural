"""Lightweight RAG: exact retrieval by Kural number from the local dataset.

No embeddings and no vector store - the selected Kural plus its chapter/section
metadata is the only context given to the agents.
"""
from app.models.schemas import Kural
from app.services.dataset_service import DatasetService


class RagService:
    def __init__(self, ds: DatasetService):
        self.ds = ds

    def retrieve(self, number: int) -> Kural | None:
        return self.ds.get(number)

    @staticmethod
    def context(k: Kural) -> str:
        return (
            f"குறள் எண்: {k.number}\n"
            f"பால்: {k.section_name}\n"
            f"அதிகாரம் {k.chapter_number}: {k.chapter_name}\n"
            f"குறள்:\n{k.text}"
        )
