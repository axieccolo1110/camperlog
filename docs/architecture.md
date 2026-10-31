# CamperLog architecture (target state)

As of 2026-10-31 · Describes the target state after the milestones from the [PRD](prd-realignment.md). The current state is described in [CLAUDE.md](../CLAUDE.md). Terms: see [CONTEXT.md](../CONTEXT.md).

## Overview

```
   Browser (private)       Browser (share link)        Terminal
        │                          │                       │
        ▼                          ▼                       ▼
 ┌──────────────────────────────────────────┐   ┌───────────────────┐
 │ web/   FastAPI                           │   │ cli.py + commands/│
 │  pages (Jinja) · api (JSON) · share      │   │  Click groups     │
 │  auth (session cookie) · schemas (Pyd.)  │   │  rich output      │
 └────────────────────┬─────────────────────┘   └─────────┬─────────┘
                      │                                   │
                      ▼                                   ▼
 ┌────────────────────────────────────────────────────────────────────┐
 │ services/   trips · campsites · expenses · sharing                 │
 │             business rules, transaction boundaries                 │
 └───────────────────────────────┬────────────────────────────────────┘
                                 ▼
 ┌────────────────────────────────────────────────────────────────────┐
 │ models.py   domain classes = ORM mapping (MappedAsDataclass)       │
 │ db.py       one engine per process, session factory                │
 │ migrations/ Alembic                                                │
 └───────────────────────────────┬────────────────────────────────────┘
                                 ▼
                 SQLite (local, tests) / PostgreSQL (Railway)
```

**Rule:** CLI and web access data exclusively through `services/`, never directly through sessions or ORM queries. Every business rule exists exactly once.

## Package structure

```
src/camperlog/
  models.py            domain classes (Trip, Stop, Campsite, Expense, Category, ShareLink)
  db.py                engine singleton, session factory, DATABASE_URL handling
  config.py            required environment variables for the web server
  consumption.py       consumption calculation (stays, works on fuel expenses)
  services/
    trips.py           trips, stops, migration helpers
    campsites.py       campsites, effective status
    expenses.py        expenses, categories, trip suggestion, trip total
    sharing.py         create/deactivate share links, public views
    geocoding.py       look up coordinates for a place name (Nominatim, M3)
  cli.py               Click root, registers the groups from commands/
  commands/            one module per Click group: trip.py, campsite.py, expense.py, fuel.py
  web/
    app.py             FastAPI app, middleware, router registration
    auth.py            login/logout, "logged in" dependency
    api.py             JSON routes /api/*
    pages.py           private HTML pages
    share.py           public route /s/{token}
    schemas.py         Pydantic models (only at the web boundary)
    templating.py      shared Jinja2Templates instance
    templates/         base.html + one page per area, share/*.html
migrations/            Alembic environment and revisions
```

`database.py` is split into `db.py` (infrastructure) and `services/` (queries and rules).

## Domain model and persistence

Domain classes are also the ORM mapping ([ADR 0004](adr/0004-domain-classes-are-orm-dataclasses.md)). Pydantic schemas exist only in `web/schemas.py`.

| Table | Important fields | Relations |
|---|---|---|
| `trips` | start_date, end_date, distance_km (optional) | 1:n stops, 1:n expenses |
| `stops` | trip_id, position, date, campsite_id (optional), place_name (optional), lat/lon (optional) | n:1 trip, n:1 campsite |
| `campsites` | name, lat, lon, status (manual: visited/bookmarked), notes, playground, pets_allowed, external_url | 1:n stops |
| `categories` | name, protected | 1:n expenses |
| `expenses` | date, amount, category_id, trip_id (optional), note, liters/price_per_liter/odometer (fuel only) | n:1 category, n:1 trip |
| `share_links` | token, target_type (trip/campsite), target_id, active, created_at | – |

Decisions:

- **Order of stops:** sorted by `date`, for the same date by `position` (order of entry within the day). Manual reordering is not planned for now. The date of a stop must lie within the period of its trip; `services/trips.py` checks this.
- **Deleting:** a trip takes its stops with it. The service rejects deleting a campsite that stops reference.
- **Location of a stop:** with a campsite reference, the campsite's location applies. Coordinates of the stop itself are then ignored.
- **Effective status of a campsite** is computed on read: "visited" if the manual status is "visited" **or** a stop with a date ≤ today references it. If the status were set on save, a stop planned in the future would wrongly stay "bookmarked" after its date.
- **Refueling:** one row in `expenses` with the fuel fields filled. `services/expenses.py` enforces: category Fuel exactly when liters, price per liter and odometer reading are set. The amount of a fuel expense is computed from liters × price.
- **Category Fuel** is created by a migration, with `protected = true`. The service rejects renaming and deleting protected categories. Other categories can only be deleted if no expense uses them.
- **Trip suggestion:** for a date the service returns the matching trip (date between start and end). Only what the user confirms is stored.
- **Engine:** one per process, created lazily in `db.py`. Sessions are short-lived: one per request on the web, one per command in the CLI.

## Migrations

Schema changes go through **Alembic**. `Base.metadata.create_all` is dropped.

- The first revision reproduces today's schema (`trips`, `fuel_entries`). Existing production databases are set to it with `alembic stamp`.
- Data conversions are revisions of their own: old trips → trip + two free-standing stops (M2), `fuel_entries` → `expenses` of the category Fuel (M4).
- Execution: `alembic upgrade head` before the server starts (Railway start command, `make serve`). The CLI does not migrate by itself. It checks the schema version and aborts with a hint to `camperlog db upgrade` if the schema is outdated. Otherwise a local call with `DATABASE_URL` pointing at production could rebuild the schema before the deployment.
- SQLite needs Alembic's batch mode for column changes (`render_as_batch=True`).
- Every data revision gets a test that fills a database in the old schema with sample data, migrates it and checks the result.

## Web

Server-rendered Jinja pages with a shared `base.html`, no SPA ([ADR 0005](adr/0005-server-rendered-pages-instead-of-spa.md)). Forms send their data to the JSON API via `fetch()`, as they do today.

| Route | Access | Purpose |
|---|---|---|
| `GET/POST /login`, `POST /logout` | public | login form |
| `GET /health` | public | Railway health check |
| `GET /s/{token}` | public | share view (trip or campsite) |
| `GET /`, `/trips…`, `/campsites…`, `/map`, `/expenses…` | logged in | private pages |
| `/api/*` | logged in | JSON API for forms and the map |

- **Login:** one password from `CAMPERLOG_PASSWORD`, compared with `secrets.compare_digest`. On success a signed session cookie via Starlette `SessionMiddleware` (secret from `CAMPERLOG_SECRET_KEY`, `https_only` in production). Private routes depend on a shared FastAPI dependency: pages redirect to `/login`, the API answers 401.
- **Map:** Leaflet with OpenStreetMap tiles via CDN (like Chart.js), data as GeoJSON from `/api/map`. Two views: retrospective (visited campsites, free-standing stops with coordinates, straight lines per trip can be toggled on) and bookmark list. Coordinates are entered by clicking on the map or by hand.
- **Coordinate lookup:** `GET /api/geocode?q=…` (login required) asks OpenStreetMap Nominatim from the server ([ADR 0006](adr/0006-coordinate-lookup-via-nominatim-on-the-server.md)) and returns up to five matches (name, region, country, lat, lon). The stop form calls it when the place field is left and no coordinates are entered. The server sends an identifying `User-Agent`, makes at most one request per second and caches results. Failures and timeouts are answered with an empty result, so the form never blocks. Tests replace the service with a fake.
- **Share links:** the token comes from `secrets.token_urlsafe(16)`. `services/sharing.py` provides separate, reduced data objects for the share view **without amount fields**. The share template therefore gets no costs at all. Deactivated or unknown tokens return 404, with no difference between the two cases.

## CLI

`cli.py` contains only the root group and registers the groups from `commands/`. The CLI keeps working directly against the database from `DATABASE_URL`, not through the web API, and needs no login. `fuel add` stays as a shorthand and calls the same service as `expense add --category Fuel`.

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | no (local) / yes (Railway) | database; without it SQLite at `data/camperlog.db` |
| `CAMPERLOG_PASSWORD` | yes for the web | login password |
| `CAMPERLOG_SECRET_KEY` | yes for the web | signature of the session cookies |

Without the password or the secret key the web server does not start, so no instance accidentally goes online unprotected.

New dependencies: `alembic`, `itsdangerous` (for `SessionMiddleware`), `python-multipart` (login form), `httpx` (server-side coordinate lookup; today dev-only, becomes a production dependency in M3).

## Tests

- Services are tested directly against SQLite (as today via `conftest.py` with a temporary database). The tests of the business rules live here.
- Web integration tests with `TestClient` additionally check: private routes without a login → 401 or redirect, the share view contains no amounts.
- Migration tests: see above.

## Implementation along the milestones

| Milestone | Architecture work |
|---|---|
| M1 Login | split `web/` (`app.py`, `auth.py`, `pages.py`, `api.py`), `base.html`, start-up check of the environment variables |
| M2 Trip with stops | `db.py` + `services/`, switch to `MappedAsDataclass`, Alembic baseline + migration of the trips, introduce `commands/` |
| M3 Campsite + map | `services/campsites.py`, `services/geocoding.py`, Leaflet, `/api/map`, `/api/geocode` |
| M4 Expenses | `services/expenses.py`, categories, migration of the fuel entries, switch `consumption.py` to fuel expenses |
| M5 Share links | `services/sharing.py`, `web/share.py`, share templates |

CLAUDE.md is adjusted to the then-current state in every milestone.
