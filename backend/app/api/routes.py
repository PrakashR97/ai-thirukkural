import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query, Request

from app.agents.base import AgentError, Usage
from app.agents.workflow import ReviewFailed, generate_reviewed
from app.models.schemas import Chapter, ExplainResult, Kural, KuralPage, Section

log = logging.getLogger("thirukkural")
router = APIRouter(prefix="/api")


def _state(request: Request):
    return request.app.state


def _kural_or_404(request: Request, number: int) -> Kural:
    k = _state(request).ds.get(number)
    if not k:
        raise HTTPException(404, f"Kural {number} not found (valid range 1-1330)")
    return k


@router.get("/health")
def health(request: Request):
    s = _state(request)
    return {"status": "ok", "kurals": len(s.ds.kurals), "dataset_valid": s.ds.report.ok,
            "ai_configured": s.settings.ai_configured}


@router.get("/kurals", response_model=KuralPage)
def list_kurals(request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                chapter: int | None = Query(None, ge=1, le=133), section: int | None = Query(None, ge=1, le=3)):
    items, total = _state(request).ds.page(page, page_size, chapter, section)
    return KuralPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/kurals/{number}", response_model=Kural)
def get_kural(request: Request, number: int):
    return _kural_or_404(request, number)


@router.get("/sections", response_model=list[Section])
def sections(request: Request):
    return _state(request).ds.sections


@router.get("/chapters", response_model=list[Chapter])
def chapters(request: Request, section: int | None = Query(None, ge=1, le=3)):
    cs = _state(request).ds.chapters
    return [c for c in cs if section is None or c.section_number == section]


@router.get("/chapters/{number}/kurals", response_model=list[Kural])
def chapter_kurals(request: Request, number: int):
    if not 1 <= number <= 133:
        raise HTTPException(404, "Chapter not found (valid range 1-133)")
    return _state(request).ds.chapter_kurals(number)


@router.get("/search", response_model=list[Kural])
def search(request: Request, q: str = Query(..., min_length=1, max_length=100)):
    return _state(request).search.search(q)


@router.get("/usage")
def usage(request: Request):
    s = _state(request)
    summary = s.cache.usage_summary()
    p_in, p_out = s.settings.price_input_per_1m, s.settings.price_output_per_1m
    summary["estimated_cost_usd"] = (
        round(summary["input_tokens"] * p_in / 1e6 + summary["output_tokens"] * p_out / 1e6, 6)
        if p_in is not None and p_out is not None else None)
    return summary


@router.post("/kurals/{number}/explain", response_model=ExplainResult)
async def explain(request: Request, number: int, regenerate: bool = False):
    s = _state(request)
    k = _kural_or_404(request, number)
    cfg, model = s.settings.cache_config_version, s.settings.openai_model

    if not regenerate:
        hit = s.cache.get(number, model, cfg)
        if hit:
            s.cache.log("cache", kural_number=number, model=model, cache_status="hit")
            return ExplainResult(**{**hit, "cached": True})
    if not s.settings.ai_configured:
        raise HTTPException(503, "AI generation is not configured on the server (missing OPENAI_API_KEY)")

    lock = s.locks.setdefault(number, asyncio.Lock())
    async with lock:  # concurrent requests for the same Kural wait, then hit the cache
        if not regenerate:
            hit = s.cache.get(number, model, cfg)
            if hit:
                s.cache.log("cache", kural_number=number, model=model, cache_status="hit")
                return ExplainResult(**{**hit, "cached": True})
        s.cache.log("cache", kural_number=number, model=model, cache_status="miss")

        def sink(kind: str, u: Usage, ok: bool):
            s.cache.log(kind, kural_number=number, model=model, input_tokens=u.input_tokens,
                        output_tokens=u.output_tokens, success=ok)

        try:
            result = await generate_reviewed(s.runner, k, model, s.settings.max_correction_attempts, sink)
        except ReviewFailed as e:
            log.warning("review failed for kural %s: %s", number, e)
            raise HTTPException(502, "விளக்கத்தை மதிப்பாய்வு செய்ய முடியவில்லை. Review did not complete; please retry.")
        except AgentError as e:
            log.warning("generation failed for kural %s: %s", number, e)
            raise HTTPException(502, "Generation failed; please retry.")
        s.cache.put(number, model, cfg, result.model_dump(), result.review_status)
        return result
