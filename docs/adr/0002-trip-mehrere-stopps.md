# Trip wird zum Container mit mehreren Stopps statt einer Einzel-Fahrt

Bisher war `Trip` eine einzelne Fahrt (origin, destination, km, ein Datum). Da mehrwöchige Reisen mit mehreren besuchten Orten vollständig protokollierbar sein sollen (Kernanforderung der Neuausrichtung), wird `Trip` zu einem Container über einen Zeitraum (Start-/Enddatum) mit einer geordneten Liste von Stopps. Jeder Stopp hat ein eigenes Datum und verweist optional auf einen Stellplatz; freistehende Stopps ohne Stellplatz-Referenz bleiben erlaubt, damit nicht jede Übernachtung katalogisiert werden muss.

## Considered Options

- `Trip` unverändert lassen, Stellplätze nur lose zuordnen (kein Zwischenstopp-Konzept) — verworfen, deckt keine Trip-Gesamtkosten über mehrere besuchte Orte ab, was die zentrale Anforderung war.
