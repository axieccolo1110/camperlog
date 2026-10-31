# Domänenklassen sind zugleich ORM-Mapping (MappedAsDataclass)

Bisher existierte jedes Objekt dreifach: als reine `@dataclass` in `models.py`, als ORM-Klasse (`TripRow`, `FuelEntryRow`) in `database.py` und als Pydantic-Schema an der Web-Grenze, mit handgeschriebener Umwandlung zwischen allen dreien. Mit der Neuausrichtung kommen Stopp, Stellplatz, Ausgabe, Kategorie und ShareLink hinzu. Wir nutzen deshalb `MappedAsDataclass` aus SQLAlchemy 2: Eine Klasse ist gleichzeitig Dataclass und ORM-Mapping. Pydantic bleibt nur an der Web-Grenze. Die frühere Trennung „reine Daten ohne ORM-Kopplung“ geben wir damit bewusst auf. Die Kopplung an SQLAlchemy beschränkt sich auf `models.py` und `services/`, die Einstiegspunkte sehen nur Services.

## Considered Options

- Dreifache Repräsentation beibehalten — verworfen, weil jede neue Spalte an drei Stellen plus zwei Umwandlungen gepflegt werden müsste.
- Pydantic-Modelle als Domänenklassen (z.B. SQLModel) — verworfen, weil das Validierungs- und Persistenz-Bibliothek zusätzlich koppelt und eine weitere Abhängigkeit bringt, ohne die Web-Grenze zu vereinfachen.
