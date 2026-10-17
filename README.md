# AI திருக்குறள்

React + TypeScript (Vite) frontend, FastAPI backend, AutoGen agents (Explanation, Story, Review) using `gpt-4o-mini`,
exact-lookup RAG over the local 1,330-Kural dataset, SQLite caching.

## Dataset
`backend/data/thirukkural.json` is the supplied file (read-only, never modified): a JSON array of 1,330 two-line verses.
It has no number/chapter fields, so **Kural number = 1-based array position**; chapters/sections follow the traditional
10-per-chapter structure with chapter names from `backend/data/chapters.json` (reference metadata kept separate from the verses).
The file contains no commentary or word meanings; those are AI-generated and labelled as such in the UI.

## Setup
```bash
# Backend (Python 3.12)
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then put your real OPENAI_API_KEY in .env

# Frontend
cd ../frontend
npm install
cp .env.example .env        # VITE_API_BASE_URL (backend URL; contains no secrets)
```

## Run
```bash
# terminal 1
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
# terminal 2
cd frontend && npm run dev          # http://localhost:5173
```
Without `OPENAI_API_KEY` the app still starts and browsing/search work; `POST /api/kurals/{n}/explain` returns 503 for uncached Kurals.

## Tests
```bash
cd backend && .venv/bin/python -m pytest        # dataset, API, agent workflow, cache (mocked model; no API credits)
cd frontend && npm test && npm run build        # UI tests + typecheck/build
```

## Docker (frontend + backend + PostgreSQL)
```bash
cp .env.example .env                 # set POSTGRES_PASSWORD (and HTTP_PORT if 80 is taken)
cp backend/.env.example backend/.env # set OPENAI_API_KEY etc. (DATABASE_URL is set by compose)
docker compose up -d --build         # site on http://localhost:${HTTP_PORT:-80}
docker compose logs -f backend
docker compose down                  # keep data; add -v to also delete the database volume
```
nginx serves the React build and proxies `/api` to the backend, so the browser only talks to one origin.
Secrets are read from `.env` files at runtime and are never baked into images or committed.

## Deploy on a Hostinger VPS
Needs a **VPS** plan (shared/web hosting cannot run Docker). On the server (Ubuntu): install Docker, clone this repo,
create the two `.env` files as above, run `docker compose up -d --build`, and point your domain's A record at the VPS IP.
Add HTTPS (e.g. Caddy or certbot) in front before sharing the site publicly.

## How AI usage is controlled
- Browsing/searching never calls OpenAI. Opening a Kural calls `POST /api/kurals/{n}/explain`.
- Flow: exact lookup -> Explanation Agent -> Story Agent -> Review Agent (max 1 correction round) -> store in SQLite.
- Only results approved by the Review Agent are cached; failures are not cached and return a 502.
- Cache key: Kural number + model + (`PROMPT_VERSION` in `app/config.py` + model + correction limit). Bump `PROMPT_VERSION` after editing prompts.
- Concurrent requests for the same Kural share one generation (per-Kural lock, then cache hit).
- `GET /api/usage` reports request count, tokens, cache hits/misses, failures, and estimated cost
  (only if `PRICE_INPUT_PER_1M` / `PRICE_OUTPUT_PER_1M` are set).
- Rate limits apply only to NEW paid generations (cached Kurals are free and unlimited): `RATE_LIMIT_PER_HOUR` per visitor (default 10)
  and `DAILY_GENERATION_CAP` for the whole site (default 30); `0` disables a limit. Over the limit returns HTTP 429 with a Tamil message.
  Visitors are identified by IP (via nginx's `X-Real-IP`, trusted only when `TRUST_PROXY=true`, which compose sets). In-memory, single worker.
- The Review Agent is an AI consistency check, not verification against authoritative commentary.

## Limitations
- Rate limiting is per IP and in memory (resets on restart; shared IPs share a quota). There is no login.
- SerperDev web research is **not implemented** (nothing in the current feature set needs it; `SERPER_API_KEY` is unused).
- No UI button to force regeneration (the API supports `?regenerate=true`).
- Real OpenAI calls have not been exercised by the automated tests (mocked on purpose); verify output quality manually with your key.
