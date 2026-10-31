# CamperLog

Persönliches Tool zum Protokollieren von Camper-/Van-Reisen, Tankvorgängen und besuchten Orten.

## Language

**Trip**:
Eine komplette Reise über einen Zeitraum (Start- bis Enddatum), bestehend aus einer geordneten Liste von Stopps.
_Avoid_: Fahrt (wenn eine einzelne Etappe gemeint ist, siehe Stopp)

**Stopp**:
Eine Station innerhalb eines Trips mit eigenem Datum. Kann optional auf einen Stellplatz verweisen und übernimmt dann dessen Ort; ein freistehender Stopp ohne Stellplatz-Referenz ist erlaubt (z.B. spontane Übernachtung ohne Eintrag) und hat einen optionalen eigenen Ortsnamen und optionale Koordinaten.
_Avoid_: Station, Zwischenstopp

**Stellplatz**:
Ein eigenständiger, von einem konkreten Trip unabhängiger Ort mit Name, Koordinaten, Status (besucht/vorgemerkt), Freitext-Notizen, ein paar festen Flags (z.B. Spielplatz vorhanden, Haustiere erlaubt) und optionalem externen Link (z.B. Park4Night). Kann null, einem oder mehreren Stopps zugeordnet werden. Der Status wird manuell gesetzt, wird aber automatisch „besucht“, sobald ein vergangener Stopp auf den Stellplatz verweist.
_Avoid_: Campingplatz (Stellplatz ist der kanonische Begriff für beide)

**Ausgabe**:
Ein Geldbetrag mit Datum und Kategorie. Es gibt vorgegebene Kategorien (z.B. Sprit, Stellplatzgebühr, Fähre/Maut, Reparatur/Wartung, Lebensmittel, Freizeit, Sonstiges), weitere kann der Nutzer selbst anlegen und umbenennen; Sprit ist fest und weder umbenennbar noch löschbar. Eine Ausgabe gehört optional zu einem Trip; liegt ihr Datum im Zeitraum eines Trips, wird diese Zuordnung vorgeschlagen, ist aber änderbar (z.B. vorab gebuchte Fähre gehört dazu, eine während der Reise abgebuchte Versicherung nicht). Ein Tankvorgang ist eine Ausgabe der Kategorie Sprit mit zusätzlich Litern, Preis pro Liter und Kilometerstand; daraus wird der Verbrauch berechnet.
_Avoid_: Kosten (als Objekt), Expense, FuelEntry (als eigenständiger Begriff)

**Tankvorgang**:
Eine Ausgabe der Kategorie Sprit (siehe Ausgabe).
_Avoid_: Tankeintrag, Fuel

**Share-Link**:
Ein Link, über den ein einzelner Trip oder Stellplatz für Dritte nur lesbar sichtbar ist. Ausgaben sind darüber nie sichtbar. Der Nutzer kann einen Share-Link jederzeit deaktivieren; er läuft nicht von selbst ab.
_Avoid_: Freigabe, Teilen (wenn Zugriff für weitere Nutzer gemeint ist; CamperLog hat genau einen Nutzer)
