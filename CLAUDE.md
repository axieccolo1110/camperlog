# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language

English is the leading language of this repository (it is public): code, comments, docstrings, identifiers, test names, commit messages, PR and issue text, and documentation are written in English. German stays only where users see it: the web UI, CLI output and `--help` texts, and error messages. Domain terms are named in English (e.g. campsite, stop, expense, category); the glossary in `CONTEXT.md` maps them to the German terms.

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
camperlog db upgrade               # apply pending schema migrations (same as `alembic upgrade head`)
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

- **CLI** (`src/camperlog/cli.py`) — only the Click root group (it checks the schema version) and the registration of the command groups. Each group lives in its own module in `src/camperlog/commands/`: `trip.py`, `fuel.py`, `db.py` (`camperlog db upgrade`) and `serve.py`; shared helpers are in `commands/common.py`. Commands open one session per invocation with `session_scope()`, call services and use `rich` for terminal output. To add a command group: new module in `commands/` exposing a Click group, register it in `cli.py`.
- **Web app** (`src/camperlog/web/`) — FastAPI app, split into:
  - `app.py` — `create_app()` (lifespan checks the schema version, `SessionMiddleware`, routers, `GET /health`). `app` is built lazily on first access (module `__getattr__`), so importing the module needs no env vars; uvicorn target is `camperlog.web.app:app`.
  - `auth.py` — `GET/POST /login`, `POST /logout`, and the shared dependency `require_login`: pages redirect to `/login` (303), `/api/*` answers 401.
  - `pages.py` — private HTML pages (dashboard at `GET /`, campsite list and form at `GET /campsites`, trip detail at `GET /trips/{id}` with the stop form, the trip edit form and delete buttons that ask via `confirm()`).
  - `api.py` — `APIRouter` for `/api/trips` (list, create, detail with stops, `PUT`/`DELETE /api/trips/{id}`, `POST /api/trips/{id}/stops`), `/api/stops/{id}` (`PUT`/`DELETE`), `/api/campsites` (GET/POST) and `/api/fuel` (GET/POST). Updates replace all fields (PUT); deletes answer 204.
  - `templating.py` — shared `Jinja2Templates` instance.
  - Public routes: `/health`, `/login`. Everything else needs a login.

**Layer stack (top → bottom):**
1. `cli.py` + `commands/` / `web/app.py` (+ `auth.py`, `pages.py`, `api.py`) — entry points. They never import `sqlalchemy` or `camperlog.models` (enforced by `tests/test_layers.py`).
2. `web/schemas.py` — Pydantic models for request validation and response serialization; read from domain objects via `from_attributes`
3. `services/` — business rules and all queries: `campsites.py` (campsites: add, list, get; links must be http(s) because they are rendered as `href`), `validation.py` (checks shared by services), `trips.py` (trips and stops: add, update, delete; a new trip period must include all stops), `expenses.py` (for now only refuelings). Business rule violations raise `ValidationError` (web: 422), missing objects `NotFoundError` (web: 404, CLI: error message); both live in `services/errors.py` and carry the German user message. Read queries use `populate_existing` so a session that inserted stops by `trip_id` does not keep a stale collection. Functions take a `Session` and commit themselves (one function = one transaction). Sessions are short-lived: one per request on the web (`Depends(get_session)`), one per command in the CLI (`session_scope()`).
4. `models.py` — domain classes `Campsite` (own place with required coordinates; manual status `visited`/`bookmarked`, stored in English), `Trip`, `Stop` (a trip owns its ordered stops, `Trip.stops`, cascade delete) and `FuelEntry`, each at once a dataclass and the ORM mapping (`MappedAsDataclass`, ADR 0004)
5. `labels.py` — German UI texts for stored English values (e.g. status `visited` → "besucht"), used by the CLI and as a Jinja global. `db.py` — infrastructure: one engine per process and database URL, sessions, schema version check, `upgrade_to_head()`

**Database:** `db.py` reads the `DATABASE_URL` env var and falls back to `data/camperlog.db` (SQLite). The schema is managed by **Alembic** (`alembic.ini`, `migrations/`); nothing creates tables implicitly. Run `camperlog db upgrade` (or `alembic upgrade head`) after pulling schema changes. `make serve` and the Railway start command do this before the server starts. CLI commands (except `db` and `serve`), `camperlog serve` and the web app's lifespan abort with a hint to `camperlog db upgrade` if the database is not at the newest revision. Migrations take their URL from `camperlog.db`, with batch mode enabled for SQLite. Tests create their temporary database with `upgrade_to_head()` (see `tests/conftest.py`). A database that was created by the former `create_all` is adopted once with `alembic stamp 0001_baseline` and then migrated. Data migrations (e.g. `0002`: old trips → trip with period + two stops) have a test that fills an old-schema database and checks the result (`tests/test_migration_trip_period.py`). SQLite migrations run with foreign keys switched off (batch mode rebuilds tables and would otherwise cascade-delete child rows); the app turns them on for every SQLite connection.

**Templates** (`web/templates/`): `base.html` holds the shared layout and all CSS (mobile-first, responsive, no CSS framework, no build step; tables turn into cards on phones via `data-label`). `login.html` and `dashboard.html` extend it. The dashboard is a server-rendered Jinja2 page with inline JS that POSTs to the REST API via `fetch()` and reloads. Chart.js (CDN) renders fuel cost history.

**Tests:** `tests/conftest.py` monkeypatches `DATABASE_URL` to a temporary SQLite file so all tests are isolated; its `session` fixture gives services tests (`tests/services/`) a session on that database. Dates in domain objects are `datetime.date`; the API and CLI convert from and to `YYYY-MM-DD` strings. Integration tests use FastAPI's `TestClient` (via `httpx`); `tests/integration/conftest.py` sets the web env vars via monkeypatch, builds the app with `create_app()` and offers `anon_client` (not logged in) and `api_client` (logged in).

**Deployment:** Railway via `railway.toml` (nixpacks builder, `/health` healthcheck). Production uses PostgreSQL; local dev uses SQLite.
