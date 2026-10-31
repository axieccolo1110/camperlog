# Tankvorgang wird eine Ausgabe der Kategorie Sprit statt eines eigenen Objekts

Mit der Neuausrichtung soll ein Trip seine Gesamtkosten zeigen („was hat diese Reise wirklich gekostet“), und dazu kommen neben Sprit weitere Kategorien wie Stellplatzgebühr, Reparatur und Lebensmittel. Statt `FuelEntry` neben einer neuen Ausgabe weiterzuführen, wird ein Tankvorgang eine Ausgabe der Kategorie Sprit mit den Zusatzdaten Liter, Preis pro Liter und Kilometerstand. Damit gibt es genau eine Summenlogik; der Verbrauch (L/100km) wird weiterhin aus den Ausgaben der Kategorie Sprit berechnet. Bestehende Tankeinträge werden in Ausgaben überführt.

## Considered Options

- `FuelEntry` und Ausgabe getrennt lassen — verworfen, weil jede Kostensumme (Trip, Zeitraum) zwei Quellen addieren müsste und die Logik dafür an mehreren Stellen doppelt entstünde.
