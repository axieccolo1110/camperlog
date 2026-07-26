# CamperLog 🚐

Ein modernes **Command-Line Interface (CLI)** zum Verwalten und Dokumentieren von Camper-Van-Reisen. Erfassen Sie Ihre Trips, Tankfüllungen und berechnen Sie automatisch den Treibstoffverbrauch.

**Version:** 0.1.0  
**Python:** >=3.11  
**Status:** In aktiver Entwicklung

---

## 🎯 Features

### Reiseverwaltung (Trip-Tracking)
- ✅ Neue Reisen erfassen (von → zu, Kilometer, Datum)
- ✅ Übersicht aller Reisen in formatierter Tabelle
- ✅ Chronologische Sortierung (neueste zuerst)

### Tankfüllungen (Fuel-Logging)
- ✅ Tankvorgänge mit Kosten dokumentieren
- ✅ Automatische Verbrauchsberechnung (L/100km)
- ✅ Kosten pro Liter und Gesamtausgaben tracken
- ✅ Kilometerstand-Differenzen erfassen

### Datenmanagement
- 💾 SQLite-Datenbank (persistent, lokal)
- 🔒 Validierung aller Eingaben (Datumsformat, Zahlenwerte)
- 📊 Rich-formatierte Tabellen mit Farben

---

## 📦 Installation

### Voraussetzungen
- Python 3.11 oder höher
- pip oder pip3
- Optional: virtualenv / conda

### Setup (mit venv)

```bash
# 1. Repository klonen
git clone <repo-url>
cd camperlog

# 2. Virtuelles Environment erstellen
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# oder für Windows:
# .venv\Scripts\activate

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. Entwickler-Tools (optional)
pip install -r requirements-dev.txt
```

### Installation aus Quelle
```bash
pip install -e .
```

Danach ist `camperlog` als globales Kommando verfügbar:
```bash
camperlog --help
```

---

## 🚀 Verwendung

### Trips verwalten

#### Eine neue Reise erfassen
```bash
camperlog trip add --from München --to Berlin --km 600 --date 2026-07-26
```

Output:
```
✓ Reise gespeichert: München → Berlin (600 km)
```

#### Alle Reisen anzeigen
```bash
camperlog trip list
```

Output:
```
📍 Alle Reisen
┏━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━┓
┃ Datum      ┃ Von    ┃ Nach   ┃ km ┃
┡━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━┩
│ 2026-07-26 │ München│ Berlin │600 │
└────────────┴────────┴────────┴────┘
```

### Tankfüllungen verwalten

#### Tankvorgang erfassen
```bash
camperlog fuel add --liters 50.5 --price-per-liter 1.85 --odometer 45000 --date 2026-07-26
```

Output:
```
✓ Tankfüllung gespeichert: 50.5L @ 1.85€/L = 93.43€
```

#### Alle Tankfüllungen mit Verbrauch anzeigen
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

## 📋 Datenbank-Schema

### Tabelle: `trips`
```sql
CREATE TABLE trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    km INTEGER NOT NULL,
    date TEXT NOT NULL
)
```

### Tabelle: `fuel_entries`
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

**Speicherort:** `data/camperlog.db` (relative zum Projekt-Root)

---

## 🛠️ Entwicklung

### Projektstruktur
```
camperlog/
├── src/camperlog/
│   ├── __init__.py
│   ├── cli.py              # Click-CLI-Befehle
│   ├── database.py         # SQLite-Operationen
│   ├── models.py           # Datenklassen (Trip, FuelEntry)
│   └── commands/
├── tests/
│   ├── test_cli.py         # CLI-Tests
│   └── test_database.py    # Datenbankfunktions-Tests
├── data/                   # Datenbank-Verzeichnis
├── docs/                   # Dokumentation
├── pyproject.toml          # Projektmetadaten & Tool-Config
├── requirements.txt        # Produktive Dependencies
├── requirements-dev.txt    # Entwickler-Dependencies
├── Makefile               # Häufige Befehle
└── README.md              # Diese Datei
```

### Dependencies

**Production:**
- `click>=8.1.0` – CLI-Framework
- `rich>=13.0.0` – Farbige, formatierte Terminal-Ausgabe

**Development:**
- `pytest>=7.0` – Testing Framework
- `pytest-cov>=4.0` – Code Coverage
- `black>=23.0` – Code Formatter
- `flake8>=6.0` – Linter
- `mypy>=1.0` – Type Checker

### Häufige Entwicklungs-Befehle

```bash
# Tests ausführen (mit Coverage)
python -m pytest tests/ -v

# Linting prüfen
python -m flake8 src/

# Type-Checking
python -m mypy src/ --ignore-missing-imports

# Code formatieren
black src/ tests/

# Alle Checks (linting + type-check + tests)
make check  # Falls Makefile konfiguriert
```

### Neuen Feature entwickeln

1. **Feature-Branch erstellen:**
   ```bash
   git checkout -b feat/feature-name
   ```

2. **Code schreiben + Tests:**
   ```bash
   # Neue Funktion in database.py oder cli.py
   # Tests in tests/
   ```

3. **Quality Checks:**
   ```bash
   python -m flake8 src/
   python -m mypy src/
   python -m pytest tests/ -v
   black src/ tests/
   ```

4. **Commit + Push:**
   ```bash
   git add .
   git commit -m "feat: Kurzbeschreibung"
   git push origin feat/feature-name
   ```

---

## 🧪 Tests

Das Projekt nutzt **pytest** mit **Coverage-Reporting**.

### Tests ausführen

```bash
# Alle Tests mit Verbose-Output
python -m pytest tests/ -v

# Mit Coverage-Report
python -m pytest tests/ --cov=src/camperlog

# Nur einen Test-File
python -m pytest tests/test_cli.py -v
```

### Coverage-Ziel
- Mindestens **80%** Code-Coverage angestrebt
- Alle neuen Features müssen Tests haben

### Test-Struktur
```
tests/
├── test_cli.py          # CLI-Befehle testen
│   ├── test_trip_add_valid
│   ├── test_trip_add_invalid_date
│   ├── test_trip_list_empty
│   └── test_trip_list_with_data
│
└── test_database.py     # Datenbankfunktionen testen
    ├── test_add_trip
    ├── test_get_all_trips
    └── test_empty_trips_list
```

---

## 📝 Code-Stil & Quality

Das Projekt befolgt strikte Code-Standards:

### Black (Formatter)
- Line-Length: 88 Zeichen
- Python 3.11+ target

```bash
black src/ tests/
```

### Flake8 (Linter)
Prüft auf:
- Syntax-Fehler
- Unused Imports
- Naming Conventions
- Komplexität

```bash
flake8 src/
```

### Mypy (Type Checker)
Strict type annotations:
```bash
mypy src/ --ignore-missing-imports
```

---

## 📊 Roadmap

- [ ] **v0.2.0** – Wartungs-Logging
  - Speichern von Wartungsarbeiten (Ölwechsel, Inspektion, etc.)
  - Filter und Statistiken

- [ ] **v0.3.0** – Erweiterte Berichte
  - Excel/CSV-Export
  - Monats-/Jahres-Statistiken
  - Treibstoffverbrauch-Trends

- [ ] **v0.4.0** – Web-Dashboard (optional)
  - REST-API
  - Web UI mit Grafiken

---

## 🤝 Contributing

Contributions sind **willkommen**! 

1. Fork das Repo
2. Feature-Branch erstellen (`git checkout -b feat/AmazingFeature`)
3. Commit (`git commit -m 'feat: Add AmazingFeature'`)
4. Push (`git push origin feat/AmazingFeature`)
5. Pull Request öffnen

**Bitte beachten:**
- ✅ Alle Tests müssen passen
- ✅ Code muss formattiert sein (black)
- ✅ Keine flake8 Warnungen
- ✅ Type-Checking muss passen (mypy)

---

## 📄 Lizenz

Dieses Projekt ist lizenziert unter der **MIT License** – siehe [LICENSE](LICENSE) für Details.

---

## 👤 Autoren

- **Alexander Eckert** – alexander.eckert@mailbox.org

---

## 📞 Support

Probleme oder Fragen?

- 📧 Email: alexander.eckert@mailbox.org
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/camperlog/issues)

---

## 🙏 Danksagungen

Gebaut mit:
- [Click](https://click.palletsprojects.com/) – CLI-Framework
- [Rich](https://rich.readthedocs.io/) – Terminal-Rendering
- [pytest](https://pytest.org/) – Testing Framework

---

**Happy Camping! 🏕️🚐**
