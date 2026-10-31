# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
pre-commit install

# Test
pytest -v                          # all tests
pytest tests/test_cli.py -v        # single file
pytest tests/integration/ -v       # integration tests only

# Lint / format
make lint                          # black --check + flake8 + mypy
make format                        # black src/ tests/
make check                         # lint + test combined

# Run
camperlog --help                   # CLI
CAMPERLOG_PASSWORD=test CAMPERLOG_SECRET_KEY=dev make serve   # local dev server (SQLite, auto-reload)
DATABASE_URL=<postgres-url> CAMPERLOG_PASSWORD=<pw> CAMPERLOG_SECRET_KEY=<key> make serve-prod   # production-style server
```

## Environment variables

- `DATABASE_URL` — SQLAlchemy connection string. Omit for local SQLite (`data/camperlog.db`). For PostgreSQL: `postgresql://user:password@host:port/dbname`.
- `CAMPERLOG_PASSWORD` — login password for the web app. **Required for the web server**; it refuses to start without it. Compared with `secrets.compare_digest`.
- `CAMPERLOG_SECRET_KEY` — signs the session cookie. **Required for the web server.** Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- `RAILWAY_ENVIRONMENT` — set by Railway automatically; its presence turns on the `Secure` flag of the session cookie (`https_only`). Not set locally.

The check lives in `camperlog/config.py` (`require_web_config()`) and runs in `camperlog serve` and in `web/app.py` (Railway starts `uvicorn camperlog.web.app:app` directly). Other CLI commands (`trip`, `fuel`) need neither variable.

## Architecture

The project has two entry points that share the same database layer:

- **CLI** (`src/camperlog/cli.py`) — Click command group with `trip` and `fuel` subgroups plus a `serve` command. Calls database functions directly and uses `rich` for terminal output.
- **Web app** (`src/camperlog/web/`) — FastAPI app, split into:
  - `app.py` — `create_app()` (lifespan with `init_db`, `SessionMiddleware`, routers, `GET /health`). `app` is built lazily on first access (module `__getattr__`), so importing the module needs no env vars; uvicorn target is `camperlog.web.app:app`.
  - `auth.py` — `GET/POST /login`, `POST /logout`, and the shared dependency `require_login`: pages redirect to `/login` (303), `/api/*` answers 401.
  - `pages.py` — private HTML pages (dashboard at `GET /`).
  - `api.py` — `APIRouter` for `/api/trips` and `/api/fuel` (GET/POST).
  - `templating.py` — shared `Jinja2Templates` instance.
  - Public routes: `/health`, `/login`. Everything else needs a login.

**Layer stack (top → bottom):**
1. `cli.py` / `web/app.py` (+ `auth.py`, `pages.py`, `api.py`) — entry points
2. `web/schemas.py` — Pydantic models for request validation and response serialization (separate from domain models)
3. `models.py` — plain `@dataclass` types `Trip` and `FuelEntry` (pure data, no ORM coupling)
4. `database.py` — SQLAlchemy 2.x ORM with `TripRow` / `FuelEntryRow` mapped classes; each CRUD function creates its own engine instance

**Database:** reads `DATABASE_URL` env var; falls back to `data/camperlog.db` (SQLite). Schema is auto-created via `Base.metadata.create_all(engine)` in `init_db()`, called on CLI startup and FastAPI lifespan.

**Templates** (`web/templates/`): `base.html` holds the shared layout and all CSS (mobile-first, responsive, no CSS framework, no build step; tables turn into cards on phones via `data-label`). `login.html` and `dashboard.html` extend it. The dashboard is a server-rendered Jinja2 page with inline JS that POSTs to the REST API via `fetch()` and reloads. Chart.js (CDN) renders fuel cost history.

**`src/camperlog/commands/`** is an empty placeholder package — no logic lives there yet. Don't add new commands there without first establishing a pattern; current CLI commands all live directly in `cli.py`.

**Tests:** `tests/conftest.py` monkeypatches `DATABASE_URL` to a temporary SQLite file so all tests are isolated. Integration tests use FastAPI's `TestClient` (via `httpx`); `tests/integration/conftest.py` sets the web env vars via monkeypatch, builds the app with `create_app()` and offers `anon_client` (not logged in) and `api_client` (logged in).

**Deployment:** Railway via `railway.toml` (nixpacks builder, `/health` healthcheck). Production uses PostgreSQL; local dev uses SQLite.
