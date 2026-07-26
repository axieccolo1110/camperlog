from dataclasses import dataclass


@dataclass
class Trip:
    """Datenklasse für eine Reise."""

    id: int
    origin: str
    destination: str
    km: int
    date: str  # Format: YYYY-MM-DD


@dataclass
class FuelEntry:
    """Datenklasse für einen Tankvorgang."""

    id: int
    date: str  # Format: YYYY-MM-DD
    liters: float
    price_per_liter: float
    odometer: int
    total_cost: float
