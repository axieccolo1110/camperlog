# CamperLog 🚐

A modern **command-line interface (CLI)** and web dashboard for managing and documenting camper van journeys. Record your trips and refuelings and calculate the fuel consumption automatically.

**Version:** 0.1.0  
**Python:** >=3.11  
**Status:** under active development

The user interface (web pages, CLI output and `--help` texts) is currently in German. Code, comments and documentation are in English.

---

## 🎯 Features

### Trip management (trip tracking)
- ✅ Record trips with a start and an end date and an optional distance
- ✅ Overview of all trips (period, number of stops, distance) in a formatted table
- ✅ Chronological sorting (newest first)
- ✅ Add stops to a trip (date within the trip, optional place name and coordinates)
- ✅ Edit and delete trips and stops (CLI and web, deleting asks for confirmation)
- ✅ Type a place name for a stop and the coordinates are looked up (OpenStreetMap Nominatim, asked from the server; one match is filled in, several are offered, a failed lookup never blocks the form)

### Refuelings (fuel logging)
- ✅ Document refuelings with costs
- ✅ Automatic consumption calculation (L/100km)
- ✅ Track price per liter and total expenses
- ✅ Record odometer differences

### Web dashboard
- 🔐 Login with a password, all pages and the API (`/api/*`) are protected
- 📱 Responsive: phone, tablet and desktop
- 📈 Record trips and refuelings, fuel costs as a chart

### Campsites
- ✅ Collect campsites independently of trips: name, coordinates, status (visited/bookmarked), notes, playground, pets allowed, external link (e.g. Park4Night)
- ✅ List and form in the web (`/campsites`) and in the CLI
- ✅ Map (`/map`) with your bookmarked campsites as pins; click a pin for name, notes, flags and the external link (Leaflet and OpenStreetMap tiles from a CDN, so the map needs an internet connection)

### Data management
- 💾 SQLite database (persistent, local)
- 🔒 Validation of all inputs (date format, numeric values)
- 📊 Rich-formatted tables with colors

---

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- pip or pip3
- Optional: virtualenv / conda

### Setup (with venv)

```bash
# 1. Clone the repository
git clone <repo-url>
cd camperlog

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or on Windows:
# .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Developer tools (optional)
pip install -r requirements-dev.txt
```

### Installation from source
```bash
pip install -e .
```

### Create the database
The schema is managed with Alembic. Create or update the local database (SQLite in `data/camperlog.db`, or the one in `DATABASE_URL`) once after installing and after every update that changes the schema:

```bash
camperlog db upgrade
```

CLI commands abort with a hint to this command if the schema is outdated. `make serve` runs the migrations for you.

Afterwards `camperlog` is available as a global command:
```bash
camperlog --help
```

---

## 🚀 Usage

### Managing trips

#### Record a new trip
```bash
camperlog trip add --start 2026-07-26 --end 2026-08-16 --km 2500
```

`--km` (the distance) is optional. The end must not lie before the start.

Output:
```
✓ Reise gespeichert: 2026-07-26 – 2026-08-16 (2500 km)
```

#### Add stops to a trip
```bash
camperlog trip stop add 1 --date 2026-07-28 --place Verona --lat 45.438 --lon 10.992
camperlog trip stop add 1 --date 2026-07-29     # a free-standing stop without a place
camperlog trip stop add 1 --date 2026-07-30 --campsite 2   # a stop at campsite no. 2
```

The date must lie within the period of the trip (both ends included). Coordinates are given as a pair or not at all. A stop at a campsite takes over its name and coordinates, so `--campsite` cannot be combined with `--place`, `--lat` or `--lon` (`trip stop edit … --campsite` replaces an own place, `--clear-campsite` frees the stop again). The status of a campsite is computed: it is shown as *besucht* if it is marked so or a stop dated today or earlier references it; a stop planned for the future changes nothing. A new stop goes to the end of its day. Show a trip with its stops:
```bash
camperlog trip show 1
```

#### Edit and delete
```bash
camperlog trip edit 1 --end 2026-08-20          # also --start, --km, --clear-km
camperlog trip stop edit 3 --place Rimini        # also --date, --lat/--lon, --clear-coordinates
camperlog trip stop delete 3                     # asks first, --yes skips the question
camperlog trip delete 1                          # deletes the trip with its stops
```

The number of a stop (`3` above) is shown by `camperlog trip show`. A new period of a trip must include all its stops, and the date of an edited stop must stay within the trip. In the web, the trip page (click a trip on the dashboard) offers the same with buttons and a confirmation dialog.

#### Show all trips
```bash
camperlog trip list
```

Output:
```
📍 Alle Reisen
┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━┓
┃ Von        ┃ Bis        ┃ Stopps ┃   km ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━┩
│ 2026-07-26 │ 2026-08-16 │      0 │ 2500 │
└────────────┴────────────┴────────┴──────┘
```

### Managing campsites

```bash
camperlog campsite add --name "Wiese am See" --lat 46.668 --lon 11.159 \
    --status vorgemerkt --playground --pets --url https://park4night.com/place/1
camperlog campsite list
```

Name and coordinates are required. `--status` is `vorgemerkt` (default) or `besucht`. Only `http(s)` links are accepted. In the web, campsites are under *Stellplätze* in the navigation.

### Managing refuelings

#### Record a refueling
```bash
camperlog fuel add --liters 50.5 --price-per-liter 1.85 --odometer 45000 --date 2026-07-26
```

Output:
```
✓ Tankfüllung gespeichert: 50.5L @ 1.85€/L = 93.43€
```

#### Show all refuelings with consumption
```bash
camperlog fuel list
```

Output:
```
⛽ Tankfüllungen
┏━━━━━━━━━━━━┳━━━━┳━━━━━┳━━━━━┳━━━━━━┳━━━━━━━┓
┃ Datum      ┃ Ltr┃ €/L ┃Kosten┃km-Std┃L/100km┃
┡━━━━━━━━━━━━╇━━━━╇━━━━━╇━━━━━╇━━━━━━╇━━━━━━━┩
│ 2026-07-26 │50.5│1.850│93.43€│45000 │  -    │
└────────────┴────┴─────┴──────┴──────┴───────┘
```

---

## 🌐 Web server

The web server needs two environment variables and **does not start without them**, so that no instance accidentally goes online unprotected:

| Variable | Required | Purpose |
|---|---|---|
| `CAMPERLOG_PASSWORD` | yes (web) | login password |
| `CAMPERLOG_SECRET_KEY` | yes (web) | signature of the session cookies |
| `DATABASE_URL` | no locally, yes on Railway | database; without it SQLite at `data/camperlog.db` |

Start locally:

```bash
CAMPERLOG_PASSWORD=test CAMPERLOG_SECRET_KEY=dev make serve
```

Then open `http://127.0.0.1:8000`. A secret key can be generated with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

On Railway, set both variables under *Variables*. The start command runs `alembic upgrade head` before the server starts. A production database that was created before Alembic was introduced must be adopted **once** by hand, without data loss: run `alembic stamp 0001_baseline` against it (with `DATABASE_URL` set), then deploy. The CLI commands (`camperlog trip …`, `camperlog fuel …`) do not need them.

---

## 📋 Database schema

### Table: `trips`
```sql
CREATE TABLE trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    distance_km INTEGER            -- optional, entered by hand
)
```

### Table: `stops`
```sql
CREATE TABLE stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,     -- order of entry; stops sort by date, then position
    date DATE NOT NULL,
    place_name TEXT,               -- own place, only without a campsite
    lat FLOAT,
    lon FLOAT,
    campsite_id INTEGER REFERENCES campsites(id)   -- takes over the campsite's place
)
```

Trips created before the realignment (one drive with origin, destination, km and date) are migrated automatically: each becomes a trip with start = end = the old date, the old km as distance and two stops (place names = old origin and destination).

### Table: `campsites`
```sql
CREATE TABLE campsites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'bookmarked',   -- 'visited' or 'bookmarked'
    notes VARCHAR,
    playground BOOLEAN NOT NULL DEFAULT false,
    pets_allowed BOOLEAN NOT NULL DEFAULT false,
    external_url VARCHAR
)
```

### Table: `fuel_entries`
```sql
CREATE TABLE fuel_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    liters REAL NOT NULL,
    price_per_liter REAL NOT NULL,
    odometer INTEGER NOT NULL,
    total_cost REAL NOT NULL
)
```

**Location:** `data/camperlog.db` (relative to the project root). The tables are created by the Alembic revisions in `migrations/versions/`.

---

## 🛠️ Development

### Project structure
```
camperlog/
├── src/camperlog/
│   ├── __init__.py
│   ├── cli.py              # Click CLI commands
│   ├── config.py           # required variables for the web server
│   ├── db.py               # engine, sessions, schema check, migrations entry point
│   ├── models.py           # domain classes = ORM mapping (Trip, FuelEntry)
│   ├── services/           # business rules and queries (trips, expenses)
│   ├── commands/           # one module per CLI group (trip, fuel, db, serve)
│   └── web/
│       ├── app.py          # FastAPI app, session middleware, /health
│       ├── auth.py         # login/logout, "logged in" dependency
│       ├── pages.py        # HTML pages (dashboard)
│       ├── api.py          # JSON API /api/*
│       ├── schemas.py      # Pydantic models
│       └── templates/      # base.html, login.html, dashboard.html
├── migrations/             # Alembic environment and revisions
├── alembic.ini             # Alembic configuration
├── tests/
│   ├── test_cli.py         # CLI tests
│   ├── test_config.py      # start-up check of the web server
│   ├── test_db.py          # engine, migrations, schema check
│   ├── services/           # service tests
│   └── integration/        # web tests (login, API, dashboard)
├── data/                   # database directory
├── docs/                   # documentation
├── pyproject.toml          # project metadata & tool config
├── requirements.txt        # production dependencies
├── requirements-dev.txt    # developer dependencies
├── Makefile                # common commands
└── README.md               # this file
```

### Dependencies

**Production:**
- `click>=8.1.0` – CLI framework
- `rich>=13.0.0` – colored, formatted terminal output
- `fastapi`, `uvicorn`, `jinja2` – web server and dashboard
- `itsdangerous` – signature of the session cookies
- `python-multipart` – login form
- `httpx` – coordinate lookup for place names
- `alembic` – database migrations

**Development:**
- `pytest>=7.0` – testing framework
- `pytest-cov>=4.0` – code coverage
- `black>=23.0` – code formatter
- `flake8>=6.0` – linter
- `mypy>=1.0` – type checker

### Common development commands

```bash
# Run tests (with coverage)
python -m pytest tests/ -v

# Check linting
python -m flake8 src/

# Type checking
python -m mypy src/ --ignore-missing-imports

# Format code
black src/ tests/

# All checks (linting + type check + tests)
make check  # if the Makefile is configured
```

### Developing a new feature

1. **Create a feature branch:**
   ```bash
   git checkout -b feat/feature-name
   ```

2. **Write code + tests:**
   ```bash
   # New function in services/ and a command in commands/
   # Tests in tests/
   ```

3. **Quality checks:**
   ```bash
   python -m flake8 src/
   python -m mypy src/
   python -m pytest tests/ -v
   black src/ tests/
   ```

4. **Commit + push:**
   ```bash
   git add .
   git commit -m "feat: short description"
   git push origin feat/feature-name
   ```

---

## 🧪 Tests

The project uses **pytest** with **coverage reporting**.

### Running tests

```bash
# All tests with verbose output
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ --cov=src/camperlog

# A single test file
python -m pytest tests/test_cli.py -v
```

### Coverage goal
- At least **80%** code coverage is aimed for
- All new features must have tests

### Test structure
```
tests/
├── test_cli.py          # test the CLI commands
│   ├── test_trip_add_valid
│   ├── test_trip_add_invalid_date
│   ├── test_trip_list_empty
│   └── test_trip_list_with_data
│
└── services/            # test the services
    ├── test_trips.py
    └── test_expenses.py
```

---

## 📝 Code style & quality

The project follows strict code standards:

### Black (formatter)
- Line length: 88 characters
- Python 3.11+ target

```bash
black src/ tests/
```

### Flake8 (linter)
Checks for:
- syntax errors
- unused imports
- naming conventions
- complexity

```bash
flake8 src/
```

### Mypy (type checker)
Strict type annotations:
```bash
mypy src/ --ignore-missing-imports
```

---

## 📊 Roadmap

- [ ] **v0.2.0** – Maintenance logging
  - Store maintenance work (oil change, inspection, etc.)
  - Filters and statistics

- [ ] **v0.3.0** – Extended reports
  - Excel/CSV export
  - Monthly/yearly statistics
  - Fuel consumption trends

- [ ] **v0.4.0** – Web dashboard (optional)
  - REST API
  - Web UI with charts

The current product direction (trips with stops, campsites and a map, expenses, share links) is described in [docs/prd-realignment.md](docs/prd-realignment.md).

---

## 🤝 Contributing

Contributions are **welcome**!

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/AmazingFeature`)
3. Commit (`git commit -m 'feat: Add AmazingFeature'`)
4. Push (`git push origin feat/AmazingFeature`)
5. Open a pull request

**Please note:**
- ✅ All tests must pass
- ✅ Code must be formatted (black)
- ✅ No flake8 warnings
- ✅ Type checking must pass (mypy)

---

## 📄 License

This project is licensed under the **MIT License** – see [LICENSE](LICENSE) for details.

---

## 👤 Authors

- **Alexander Eckert** – alexander.eckert@mailbox.org

---

## 📞 Support

Problems or questions?

- 📧 Email: alexander.eckert@mailbox.org
- 🐛 Issues: [GitHub Issues](https://github.com/axieccolo1110/camperlog/issues)

---

## 🙏 Acknowledgements

Built with:
- [Click](https://click.palletsprojects.com/) – CLI framework
- [Rich](https://rich.readthedocs.io/) – terminal rendering
- [pytest](https://pytest.org/) – testing framework

---

**Happy camping! 🏕️🚐**
