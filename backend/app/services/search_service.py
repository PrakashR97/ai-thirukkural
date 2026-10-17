import re
import unicodedata

from app.models.schemas import Kural
from app.services.dataset_service import DatasetService


def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", s).lower()


class SearchService:
    def __init__(self, ds: DatasetService):
        self.ds = ds
        self._index = [(k, _norm(k.text.replace("\n", " "))) for k in ds.kurals]

    def search(self, q: str, limit: int = 50) -> list[Kural]:
        q = q.strip()
        if not q:
            return []
        if re.fullmatch(r"\d{1,4}", q):
            k = self.ds.get(int(q))
            return [k] if k else []
        terms = _norm(q).split()
        out = [k for k, t in self._index if all(w in t for w in terms)]
        return out[:limit]
