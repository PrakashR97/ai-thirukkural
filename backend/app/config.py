from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Bump when prompts or generation config change: invalidates cached results.
PROMPT_VERSION = "v3"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = "gpt-4o-mini"
    serper_api_key: str = Field(default="", repr=False)
    price_input_per_1m: float | None = None
    price_output_per_1m: float | None = None
    cors_origins: str = "http://localhost:5173"
    database_url: str = Field(default="", repr=False)  # PostgreSQL URL; empty = SQLite fallback
    db_path: Path = BASE_DIR / "cache.db"
    dataset_path: Path = DATA_DIR / "thirukkural.json"
    chapters_path: Path = DATA_DIR / "chapters.json"
    request_timeout: float = 60.0
    # Limits on NEW (paid) generations only; cached results are always free. 0 disables a limit.
    rate_limit_per_hour: int = 10
    daily_generation_cap: int = 300
    # Trust X-Real-IP from the nginx proxy to identify visitors. Enable only behind a trusted proxy.
    trust_proxy: bool = False
    max_correction_attempts: int = 1

    @field_validator("price_input_per_1m", "price_output_per_1m", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        return None if v is None or str(v).strip() == "" else v

    @property
    def cache_config_version(self) -> str:
        return f"{PROMPT_VERSION}|{self.openai_model}|corr{self.max_correction_attempts}"

    @property
    def ai_configured(self) -> bool:
        return bool(self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
