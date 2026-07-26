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
make serve                         # local dev server (SQLite, auto-reload)
DATABASE_URL=<postgres-url> make serve-prod   # production-style server
```

## Environment variables

- `DATABASE_URL` — SQLAlchemy connection string. Omit for local SQLite (`data/camperlog.db`). For PostgreSQL: `postgresql://user:password@host:port/dbname`.

## Architecture

The project has two entry points that share the same database layer:

- **CLI** (`src/camperlog/cli.py`) — Click command group with `trip` and `fuel` subgroups plus a `serve` command. Calls database functions directly and uses `rich` for terminal output.
- **Web API** (`src/camperlog/web/api.py`) — FastAPI app with REST routes (`GET/POST /api/trips`, `GET/POST /api/fuel`, `GET /health`) and a server-rendered dashboard at `GET /`.

**Layer stack (top → bottom):**
1. `cli.py` / `web/api.py` — entry points
2. `web/schemas.py` — Pydantic models for request validation and response serialization (separate from domain models)
3. `models.py` — plain `@dataclass` types `Trip` and `FuelEntry` (pure data, no ORM coupling)
4. `database.py` — SQLAlchemy 2.x ORM with `TripRow` / `FuelEntryRow` mapped classes; each CRUD function creates its own engine instance

**Database:** reads `DATABASE_URL` env var; falls back to `data/camperlog.db` (SQLite). Schema is auto-created via `Base.metadata.create_all(engine)` in `init_db()`, called on CLI startup and FastAPI lifespan.

**Dashboard template** (`web/templates/dashboard.html`) is a server-rendered Jinja2 page with inline JS that POSTs to the REST API via `fetch()` and reloads. Chart.js (CDN) renders fuel cost history.

**`src/camperlog/commands/`** is an empty placeholder package — no logic lives there yet. Don't add new commands there without first establishing a pattern; current CLI commands all live directly in `cli.py`.

**Tests:** `tests/conftest.py` monkeypatches `DATABASE_URL` to a temporary SQLite file so all tests are isolated. Integration tests use FastAPI's `TestClient` (via `httpx`).

**Deployment:** Railway via `railway.toml` (nixpacks builder, `/health` healthcheck). Production uses PostgreSQL; local dev uses SQLite.
