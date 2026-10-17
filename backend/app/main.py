import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.base import make_runner
from app.api.routes import router
from app.config import Settings, get_settings
from app.services.cache_service import CacheService
from app.services.dataset_service import DatasetService
from app.services.rate_limiter import RateLimiter
from app.services.search_service import SearchService

log = logging.getLogger("thirukkural")


def create_app(settings: Settings | None = None, runner=None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ds = DatasetService(settings.dataset_path, settings.chapters_path)
        if not ds.report.ok:
            raise RuntimeError("Dataset validation failed: " + "; ".join(ds.report.problems[:5]))
        app.state.settings = settings
        app.state.ds = ds
        app.state.search = SearchService(ds)
        app.state.cache = CacheService(settings.db_path, settings.database_url)
        app.state.runner = runner or make_runner(settings)
        app.state.locks = {}
        app.state.limiter = RateLimiter(settings.rate_limit_per_hour, settings.daily_generation_cap)
        if not settings.ai_configured:
            log.warning("OPENAI_API_KEY is not set: browsing works, AI generation is disabled.")
        yield
        close = getattr(app.state.runner, "aclose", None)
        if close:
            await close()
        app.state.cache.close()

    app = FastAPI(title="AI Thirukkural", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                       allow_methods=["GET", "POST"], allow_headers=["*"])
    app.include_router(router)
    return app


app = create_app()
