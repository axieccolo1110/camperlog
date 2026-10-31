# Architektur CamperLog (Zielbild)

Stand: 2026-10-31 · Beschreibt den Zielzustand nach den Meilensteinen aus dem [PRD](prd-neuausrichtung.md). Den heutigen Stand beschreibt [CLAUDE.md](../CLAUDE.md). Begriffe siehe [CONTEXT.md](../CONTEXT.md).

## Überblick

```
   Browser (privat)        Browser (Share-Link)        Terminal
        │                          │                       │
        ▼                          ▼                       ▼
 ┌──────────────────────────────────────────┐   ┌───────────────────┐
 │ web/   FastAPI                           │   │ cli.py + commands/│
 │  pages (Jinja) · api (JSON) · share      │   │  Click-Gruppen    │
 │  auth (Session-Cookie)  · schemas (Pyd.) │   │  rich-Ausgabe     │
 └────────────────────┬─────────────────────┘   └─────────┬─────────┘
                      │                                   │
                      ▼                                   ▼
 ┌────────────────────────────────────────────────────────────────────┐
 │ services/   trips · stellplaetze · ausgaben · sharing              │
 │             Fachregeln, Transaktionsgrenzen                        │
 └───────────────────────────────┬────────────────────────────────────┘
                                 ▼
 ┌────────────────────────────────────────────────────────────────────┐
 │ models.py   Domänenklassen = ORM-Mapping (MappedAsDataclass)       │
 │ db.py       eine Engine pro Prozess, Session-Factory               │
 │ migrations/ Alembic                                                │
 └───────────────────────────────┬────────────────────────────────────┘
                                 ▼
                 SQLite (lokal, Tests) / PostgreSQL (Railway)
```

**Regel:** CLI und Web greifen ausschließlich über `services/` auf Daten zu, nie direkt auf Sessions oder ORM-Abfragen. Jede Fachregel gibt es genau einmal.

## Paketstruktur

```
src/camperlog/
  models.py            Domänenklassen (Trip, Stopp, Stellplatz, Ausgabe, Kategorie, ShareLink)
  db.py                Engine-Singleton, Session-Factory, DATABASE_URL-Auswertung
  consumption.py       Verbrauchsberechnung (bleibt, arbeitet auf Sprit-Ausgaben)
  services/
    trips.py           Trips, Stopps, Migration-Hilfen
    stellplaetze.py    Stellplätze, effektiver Status
    ausgaben.py        Ausgaben, Kategorien, Trip-Vorschlag, Trip-Summe
    sharing.py         Share-Links erzeugen/deaktivieren, öffentliche Ansichten
  cli.py               Click-Root, registriert die Gruppen aus commands/
  commands/            ein Modul pro Click-Gruppe: trip.py, stellplatz.py, ausgabe.py, fuel.py
  web/
    app.py             FastAPI-App, Middleware, Router-Registrierung
    auth.py            Login/Logout, Abhängigkeit "eingeloggt"
    api.py             JSON-Routen /api/*
    pages.py           private HTML-Seiten
    share.py           öffentliche Route /s/{token}
    schemas.py         Pydantic-Modelle (nur an der Web-Grenze)
    templates/         base.html + eine Seite pro Bereich, share/*.html
migrations/            Alembic-Umgebung und Revisionen
```

`database.py` wird in `db.py` (Infrastruktur) und `services/` (Abfragen und Regeln) aufgeteilt.

## Domänenmodell und Persistenz

Domänenklassen sind zugleich das ORM-Mapping ([ADR 0004](adr/0004-domaenenklassen-sind-orm-dataclasses.md)). Pydantic-Schemas gibt es nur in `web/schemas.py`.

| Tabelle | Wichtige Felder | Beziehungen |
|---|---|---|
| `trips` | start_datum, end_datum, distanz_km (optional) | 1:n Stopps, 1:n Ausgaben |
| `stopps` | trip_id, position, datum, stellplatz_id (optional), ortsname (optional), lat/lon (optional) | n:1 Trip, n:1 Stellplatz |
| `stellplaetze` | name, lat, lon, status (manuell: besucht/vorgemerkt), notizen, spielplatz, haustiere_erlaubt, externer_link | 1:n Stopps |
| `kategorien` | name, geschuetzt | 1:n Ausgaben |
| `ausgaben` | datum, betrag, kategorie_id, trip_id (optional), notiz, liter/preis_pro_liter/kilometerstand (nur bei Sprit) | n:1 Kategorie, n:1 Trip |
| `share_links` | token, ziel_typ (trip/stellplatz), ziel_id, aktiv, erstellt_am | – |

Festlegungen:

- **Reihenfolge der Stopps:** sortiert nach `datum`, bei gleichem Datum nach `position` (Erfassungsreihenfolge innerhalb des Tages). Manuelles Umsortieren ist vorerst nicht vorgesehen. Das Datum eines Stopps muss im Zeitraum seines Trips liegen, das prüft `services/trips.py`.
- **Löschen:** Ein Trip nimmt seine Stopps mit. Einen Stellplatz mit verweisenden Stopps lehnt der Service ab.
- **Ort eines Stopps:** Mit Stellplatz-Referenz gilt der Ort des Stellplatzes. Eigene Koordinaten am Stopp werden dann ignoriert.
- **Effektiver Status eines Stellplatzes** wird beim Lesen berechnet: „besucht“, wenn der manuelle Status „besucht“ ist **oder** ein Stopp mit Datum ≤ heute auf ihn verweist. Würde man den Status beim Speichern setzen, bliebe ein in der Zukunft geplanter Stopp nach seinem Datum fälschlich „vorgemerkt“.
- **Tankvorgang:** eine Zeile in `ausgaben` mit gefüllten Sprit-Feldern. `services/ausgaben.py` erzwingt: Kategorie Sprit genau dann, wenn Liter, Preis pro Liter und Kilometerstand gesetzt sind. Der Betrag einer Sprit-Ausgabe wird aus Liter × Preis berechnet.
- **Kategorie Sprit** wird per Migration angelegt, mit `geschuetzt = true`. Der Service lehnt Umbenennen und Löschen geschützter Kategorien ab. Löschen anderer Kategorien geht nur, wenn keine Ausgabe sie nutzt.
- **Trip-Vorschlag:** Der Service liefert für ein Datum den passenden Trip (Datum zwischen Start und Ende). Gespeichert wird nur, was der Nutzer bestätigt.
- **Engine:** eine pro Prozess, lazy erzeugt in `db.py`. Sessions sind kurzlebig: im Web eine pro Request, in der CLI eine pro Befehl.

## Migrationen

Schema-Änderungen laufen über **Alembic**. `Base.metadata.create_all` entfällt.

- Die erste Revision bildet das heutige Schema ab (`trips`, `fuel_entries`). Bestehende Produktionsdatenbanken werden darauf mit `alembic stamp` gesetzt.
- Datenumbauten sind eigene Revisionen: alte Trips → Trip + zwei freistehende Stopps (M2), `fuel_entries` → `ausgaben` der Kategorie Sprit (M4).
- Ausführung: `alembic upgrade head` vor dem Serverstart (Railway-Startbefehl, `make serve`). Die CLI migriert nicht selbst. Sie prüft den Schema-Stand und bricht bei veraltetem Schema mit dem Hinweis auf `camperlog db upgrade` ab. Sonst könnte ein lokaler Aufruf mit `DATABASE_URL` auf Produktion das Schema vor dem Deployment umbauen.
- SQLite braucht für Spaltenänderungen den Batch-Modus von Alembic (`render_as_batch=True`).
- Jede Daten-Revision bekommt einen Test, der eine Datenbank im alten Schema mit Beispieldaten füllt, migriert und das Ergebnis prüft.

## Web

Server-gerenderte Jinja-Seiten mit gemeinsamem `base.html`, keine SPA ([ADR 0005](adr/0005-server-gerenderte-seiten-statt-spa.md)). Formulare schicken ihre Daten wie heute per `fetch()` an die JSON-API.

| Route | Zugriff | Zweck |
|---|---|---|
| `GET/POST /login`, `POST /logout` | öffentlich | Login-Formular |
| `GET /health` | öffentlich | Railway-Healthcheck |
| `GET /s/{token}` | öffentlich | Share-Ansicht (Trip oder Stellplatz) |
| `GET /`, `/trips…`, `/stellplaetze…`, `/karte`, `/ausgaben…` | eingeloggt | private Seiten |
| `/api/*` | eingeloggt | JSON-API für Formulare und Karte |

- **Login:** ein Passwort aus `CAMPERLOG_PASSWORD`, Vergleich mit `secrets.compare_digest`. Nach Erfolg ein signiertes Session-Cookie über Starlette `SessionMiddleware` (Secret aus `CAMPERLOG_SECRET_KEY`, `https_only` in Produktion). Private Routen hängen an einer gemeinsamen FastAPI-Abhängigkeit: Seiten leiten auf `/login` um, die API antwortet mit 401.
- **Karte:** Leaflet mit OpenStreetMap-Kacheln per CDN (wie Chart.js), Daten als GeoJSON aus `/api/karte`. Zwei Ansichten: Rückschau (besuchte Stellplätze, freistehende Stopps mit Koordinaten, Luftlinien pro Trip zuschaltbar) und Vormerkliste. Koordinaten gibt man per Klick auf die Karte oder von Hand ein.
- **Share-Links:** Das Token stammt aus `secrets.token_urlsafe(16)`. `services/sharing.py` liefert für die Share-Ansicht eigene, reduzierte Datenobjekte **ohne Betragsfelder**. Das Share-Template bekommt also gar keine Kosten. Deaktivierte oder unbekannte Tokens geben 404 zurück, ohne Unterschied zwischen beiden Fällen.

## CLI

`cli.py` enthält nur noch die Root-Gruppe und registriert die Gruppen aus `commands/`. Die CLI arbeitet weiter direkt gegen die Datenbank aus `DATABASE_URL`, nicht über die Web-API, und braucht keinen Login. `fuel add` bleibt als Kurzform und ruft denselben Service auf wie `ausgabe add --kategorie Sprit`.

## Konfiguration

| Variable | Pflicht | Zweck |
|---|---|---|
| `DATABASE_URL` | nein (lokal) / ja (Railway) | Datenbank; ohne Angabe SQLite unter `data/camperlog.db` |
| `CAMPERLOG_PASSWORD` | ja für das Web | Login-Passwort |
| `CAMPERLOG_SECRET_KEY` | ja für das Web | Signatur der Session-Cookies |

Ohne Passwort oder Secret startet der Webserver nicht. So geht keine Instanz versehentlich ohne Schutz online.

Neue Abhängigkeiten: `alembic`, `itsdangerous` (für `SessionMiddleware`), `python-multipart` (Login-Formular).

## Tests

- Services werden direkt gegen SQLite getestet (wie heute über `conftest.py` mit temporärer Datenbank). Hier liegen die Tests der Fachregeln.
- Web-Integrationstests mit `TestClient` prüfen zusätzlich: private Routen ohne Login → 401 bzw. Umleitung, Share-Ansicht enthält keine Beträge.
- Migrationstests siehe oben.

## Umsetzung entlang der Meilensteine

| Meilenstein | Architekturarbeit |
|---|---|
| M1 Login | `web/` aufteilen (`app.py`, `auth.py`, `pages.py`, `api.py`), `base.html`, Startprüfung der Umgebungsvariablen |
| M2 Trip mit Stopps | `db.py` + `services/`, Umstieg auf `MappedAsDataclass`, Alembic-Basis + Migration der Trips, `commands/` einführen |
| M3 Stellplatz + Karte | `services/stellplaetze.py`, Leaflet, `/api/karte` |
| M4 Ausgaben | `services/ausgaben.py`, Kategorien, Migration der Tankeinträge, `consumption.py` auf Sprit-Ausgaben umstellen |
| M5 Share-Links | `services/sharing.py`, `web/share.py`, Share-Templates |

CLAUDE.md wird in jedem Meilenstein an den dann tatsächlichen Stand angepasst.
