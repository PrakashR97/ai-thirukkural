"""Result cache + usage log.

Uses PostgreSQL when DATABASE_URL is set, otherwise falls back to a local SQLite
file. SQL is written once with `?` placeholders (always parameterized) and
translated to `%s` for Postgres.
"""
import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS kural_cache (
    kural_number INTEGER NOT NULL,
    model TEXT NOT NULL,
    config_version TEXT NOT NULL,
    result_json TEXT NOT NULL,
    review_status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (kural_number, model, config_version)
);
CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    kural_number INTEGER,
    request_type TEXT NOT NULL,
    model TEXT,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_status TEXT,
    success INTEGER NOT NULL DEFAULT 1,
    error TEXT
);
"""

POSTGRES_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS kural_cache (
        kural_number INTEGER NOT NULL,
        model TEXT NOT NULL,
        config_version TEXT NOT NULL,
        result_json JSONB NOT NULL,
        review_status TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (kural_number, model, config_version)
    )""",
    """CREATE TABLE IF NOT EXISTS usage_logs (
        id BIGSERIAL PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        kural_number INTEGER,
        request_type TEXT NOT NULL,
        model TEXT,
        input_tokens INTEGER NOT NULL DEFAULT 0,
        output_tokens INTEGER NOT NULL DEFAULT 0,
        cache_status TEXT,
        success INTEGER NOT NULL DEFAULT 1,
        error TEXT
    )""",
]

UPSERT = (
    "INSERT INTO kural_cache (kural_number, model, config_version, result_json, review_status) "
    "VALUES (?,?,?,?,?) ON CONFLICT (kural_number, model, config_version) "
    "DO UPDATE SET result_json=excluded.result_json, review_status=excluded.review_status"
)


class CacheService:
    def __init__(self, sqlite_path: Path, database_url: str = ""):
        self.postgres = bool(database_url)
        self._lock = threading.Lock()
        if self.postgres:
            from psycopg_pool import ConnectionPool
            self._pool = ConnectionPool(database_url, min_size=1, max_size=5, open=True, timeout=10)
            with self._conn() as c:
                for stmt in POSTGRES_SCHEMA:
                    c.execute(stmt)
        else:
            self.db_path = str(sqlite_path)
            with self._conn() as c:
                c.executescript(SQLITE_SCHEMA)

    @contextmanager
    def _conn(self):
        if self.postgres:
            with self._pool.connection() as conn:  # commits on success, rolls back on error
                yield conn
        else:
            conn = sqlite3.connect(self.db_path, timeout=10)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                yield conn
                conn.commit()
            finally:
                conn.close()

    def _run(self, conn, sql: str, params: tuple = ()):
        return conn.execute(sql.replace("?", "%s") if self.postgres else sql, params)

    def close(self) -> None:
        if self.postgres:
            self._pool.close()

    def get(self, number: int, model: str, version: str) -> dict | None:
        with self._conn() as c:
            row = self._run(
                c, "SELECT result_json FROM kural_cache WHERE kural_number=? AND model=? AND config_version=?",
                (number, model, version)).fetchone()
        if not row:
            return None
        return row[0] if isinstance(row[0], dict) else json.loads(row[0])

    def put(self, number: int, model: str, version: str, result: dict, status: str) -> None:
        with self._lock, self._conn() as c:
            self._run(c, UPSERT, (number, model, version, json.dumps(result, ensure_ascii=False), status))

    def delete(self, number: int, model: str, version: str) -> None:
        with self._lock, self._conn() as c:
            self._run(c, "DELETE FROM kural_cache WHERE kural_number=? AND model=? AND config_version=?",
                      (number, model, version))

    def log(self, request_type: str, *, kural_number: int | None = None, model: str | None = None,
            input_tokens: int = 0, output_tokens: int = 0, cache_status: str | None = None,
            success: bool = True, error: str | None = None) -> None:
        with self._lock, self._conn() as c:
            self._run(
                c, "INSERT INTO usage_logs (kural_number, request_type, model, input_tokens, output_tokens, "
                "cache_status, success, error) VALUES (?,?,?,?,?,?,?,?)",
                (kural_number, request_type, model, input_tokens, output_tokens, cache_status,
                 int(success), (error or "")[:300] or None))

    def usage_summary(self) -> dict:
        with self._conn() as c:
            r = self._run(
                c, "SELECT COUNT(CASE WHEN request_type IN ('explanation','story','review') THEN 1 END), "
                "COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0), "
                "COUNT(CASE WHEN cache_status='hit' THEN 1 END), COUNT(CASE WHEN cache_status='miss' THEN 1 END), "
                "COUNT(CASE WHEN request_type='generation_failure' THEN 1 END), "
                "COUNT(CASE WHEN request_type='review_failure' THEN 1 END) FROM usage_logs").fetchone()
        return {"openai_requests": int(r[0]), "input_tokens": int(r[1]), "output_tokens": int(r[2]),
                "cache_hits": int(r[3]), "cache_misses": int(r[4]),
                "generation_failures": int(r[5]), "review_failures": int(r[6])}
