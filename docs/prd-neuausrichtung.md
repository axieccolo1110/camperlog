# PRD: Neuausrichtung CamperLog — privates Reise-Tagebuch mit Karte

Stand: 2026-10-31 · Begriffe siehe [CONTEXT.md](../CONTEXT.md) · Entscheidungen siehe [docs/adr/](adr/)

## Problem

CamperLog erfasst heute nur einzelne Fahrten (von/nach, km, Datum) und Tankvorgänge. Damit lässt sich weder eine mehrwöchige Reise mit mehreren Orten abbilden, noch beantworten, was eine Reise insgesamt gekostet hat. Orte, an denen man war oder die man sich für später merkt, haben gar keinen Platz. Nutzer pflegen deshalb parallel Tabellen, Notiz-Apps und Favoritenlisten in Park4Night.

Zusätzlich ist das Web-Dashboard samt API heute ohne Login öffentlich erreichbar.

## Ziel

CamperLog wird ein **privates Reise-Tagebuch**: komplette Reisen mit allen Stopps protokollieren, eigene Stellplätze (besucht und vorgemerkt) auf einer Karte sehen und am Ende wissen, was eine Reise wirklich gekostet hat.

## Positionierung und Nicht-Ziele

CamperLog ergänzt die Spezialisten-Apps, statt sie zu ersetzen ([ADR 0001](adr/0001-stellplatz-ergaenzt-crowd-datenbanken.md)). Man findet Orte weiter über Park4Night, iOverlander & Co. und trägt sie mit Link in CamperLog ein. Der Mehrwert, den keine dieser Apps bietet: eigene Orte, Reisen und Kosten an einem Ort, verknüpft miteinander.

Ausdrücklich **nicht** Teil dieser Neuausrichtung:

- Eigene Stellplatz-Suche, Crowd-Datenbank oder Bewertungen
- Routenplanung oder Navigation (die Karte zeigt nur Luftlinien zwischen Stopps)
- Mehrere Nutzer oder Accounts. CamperLog hat genau einen Nutzer.
- Vollwertiges Finanz- oder Wartungstool im Stil von Fuelio

## Zielgruppe

Grundlage sind zwei simulierte Personas plus die Vorstellungen des Produktinhabers:

- **Jörg**, 52, solo mit Hund im selbst ausgebauten Sprinter, 3–4 Langzeitreisen pro Jahr nach Südeuropa. Will eine ehrliche Kostensumme pro Reise, braucht keine Karte, möchte einzelne Dinge mit Bekannten teilen.
- **Sabine**, 41, Familie mit zwei Kindern, Wochenend- und Ferienreisen, plant Stellplätze Monate im Voraus. Für sie sind Karte und Vormerkliste der Kern („Spielplatz vorhanden“ ist ihr wichtigstes Feld), dazu die Kostensumme pro Urlaub.
- **Produktinhaber:** Karte mit eigenen Stellplätzen hat Priorität 1. Ausgaben und Wartung bleiben im Scope, aber mit niedrigerer Priorität.

Sabines Wunsch nach gemeinsamem Zugriff für mehrere Personen wird bewusst nicht umgesetzt (siehe Nicht-Ziele).

## Meilensteine

Die Reihenfolge folgt den Abhängigkeiten: Jeder Meilenstein baut auf dem vorherigen auf.

### M1 — Login für das Web

- Dashboard und alle `/api/*`-Routen sind nur nach Login erreichbar. Ausnahmen: `/health` und später die Share-Link-Seiten.
- Ein einziges Passwort, das per Umgebungsvariable gesetzt wird. Keine Accounts, keine Registrierung.
- Die CLI greift direkt auf die Datenbank zu und ist nicht betroffen.

**Fertig, wenn:** ein Aufruf des Dashboards oder der API ohne Login abgewiesen wird und `/health` weiter antwortet, sodass der Railway-Healthcheck grün bleibt.

### M2 — Trip mit Stopps

([ADR 0002](adr/0002-trip-mehrere-stopps.md))

- Ein **Trip** hat Start- und Enddatum, optional eine von Hand eingetragene Distanz in km und eine geordnete Liste von **Stopps**.
- Ein **Stopp** hat ein Datum und verweist entweder auf einen Stellplatz (und übernimmt dessen Ort) oder ist freistehend mit optionalem Ortsnamen und optionalen Koordinaten.
- **Migration:** Jeder bestehende Trip wird ein Trip mit Start- und Enddatum gleich dem alten Datum und zwei freistehenden Stopps (Ortsname = alter Start bzw. altes Ziel). Der alte km-Wert bleibt als Distanz erhalten.
- Das Datum eines Stopps muss im Zeitraum seines Trips liegen. Stopps werden nach Datum sortiert, bei gleichem Datum in der Reihenfolge der Erfassung.
- Trips und Stopps lassen sich bearbeiten und löschen. Ein geänderter Trip-Zeitraum muss alle vorhandenen Stopps einschließen. Wird ein Trip gelöscht, verschwinden auch seine Stopps.
- CLI: Trips anlegen und auflisten, Stopps zu einem Trip hinzufügen (`trip stopp …`).

**Fertig, wenn:** sich eine dreiwöchige Reise mit sechs Stopps (davon zwei freistehend) per Web und per CLI erfassen lässt und alle Alt-Trips ohne Datenverlust migriert sind.

### M3 — Stellplatz und Karte (Priorität 1)

- Ein **Stellplatz** ist unabhängig von Trips anlegbar und hat: Name, Koordinaten, Status (besucht/vorgemerkt), Freitext-Notizen, feste Flags (Spielplatz vorhanden, Haustiere erlaubt) und einen optionalen externen Link (z.B. Park4Night).
- Den Status setzt man von Hand. Sobald ein Stopp mit Datum in der Vergangenheit auf einen Stellplatz verweist, wird er automatisch „besucht“. Besuche aus der Zeit vor CamperLog lassen sich so ohne Trip eintragen.
- Ein Stellplatz kann von beliebig vielen Stopps referenziert werden, z.B. ein Lieblingsplatz auf mehreren Reisen.
- Stellplätze lassen sich bearbeiten und löschen. Ein Stellplatz, auf den ein Stopp verweist, lässt sich nicht löschen.
- **Karte** im Web-Dashboard mit zwei klar getrennten Ansichten:
  - **Rückschau:** besuchte Stellplätze und freistehende Stopps mit Koordinaten als Pins. Pro Trip lässt sich eine Luftlinie einblenden, die die Stopps der Reihe nach verbindet.
  - **Vormerkliste:** vorgemerkte Stellplätze.
- Die Karte gibt es nur im Web. Die CLI kann Stellplätze anlegen und auflisten (`stellplatz …`).

**Fertig, wenn:** man im Februar einen Platz vormerken kann, ihn im August als Stopp einem Trip zuordnet und er danach in der Rückschau statt in der Vormerkliste erscheint.

### M4 — Ausgaben und Trip-Summe

([ADR 0003](adr/0003-tankvorgang-ist-ausgabe.md))

- Eine **Ausgabe** hat Datum, Betrag, Kategorie, optional eine Notiz und optional einen Trip.
- **Kategorien:** vorgegeben sind Sprit, Stellplatzgebühr, Fähre/Maut, Reparatur/Wartung, Lebensmittel, Freizeit und Sonstiges. Eigene Kategorien kann man anlegen und umbenennen. Sprit lässt sich weder umbenennen noch löschen. Eine Kategorie lässt sich nur löschen, wenn keine Ausgabe sie mehr nutzt.
- **Tankvorgang** = Ausgabe der Kategorie Sprit mit Litern, Preis pro Liter und Kilometerstand. Der Verbrauch (L/100km) wird wie bisher daraus berechnet. Bestehende Tankeinträge werden migriert.
- **Zuordnung zu einem Trip:** Liegt das Datum im Zeitraum eines Trips, wird dieser Trip vorgeschlagen. Man kann ihn ändern oder entfernen (vorab gebuchte Fähre gehört dazu, die während der Reise abgebuchte Versicherung nicht).
- **Trip-Summe:** pro Trip die Gesamtkosten, aufgeschlüsselt nach Kategorie.
- CLI: `ausgabe …` zum Erfassen und Auflisten. `fuel add` bleibt als Kurzform für eine Sprit-Ausgabe erhalten.

**Fertig, wenn:** für einen Trip mit Sprit-, Stellplatz- und Fähren-Ausgaben die Gesamtsumme samt Aufschlüsselung angezeigt wird und die bisherigen Verbrauchswerte nach der Migration unverändert sind.

### M5 — Share-Links

- Der Nutzer kann für einen einzelnen **Trip** (Karte und Stopps) oder einen einzelnen **Stellplatz** einen Share-Link erzeugen.
- Über einen Share-Link sieht man die Inhalte nur zum Lesen und ohne Login. **Ausgaben und Kosten sind nie sichtbar.**
- Ein Share-Link lässt sich jederzeit deaktivieren und läuft nicht von selbst ab.

**Fertig, wenn:** ein geteilter Trip ohne Login aufrufbar ist, keine Beträge zeigt und nach dem Deaktivieren nicht mehr erreichbar ist.

### M6 — Wartung (Platzhalter)

Erinnerungen an Wartungen nach Kilometerstand oder Zeit (z.B. Ölwechsel) sind gewünscht, haben aber niedrige Priorität. Struktur und Umfang werden erst festgelegt, wenn der Meilenstein ansteht.

## Offene Punkte

Keine offenen Produktentscheidungen. Technische Detailfragen (z.B. Karten-Bibliothek und Kartenkacheln, Migrationsstrategie für PostgreSQL in Produktion) werden pro Meilenstein bei der Umsetzung geklärt.
