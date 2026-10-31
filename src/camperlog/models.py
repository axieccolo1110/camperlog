from dataclasses import dataclass


@dataclass
class Trip:
    """Data class for a trip."""

    id: int
    origin: str
    destination: str
    km: int
    date: str  # Format: YYYY-MM-DD


@dataclass
class FuelEntry:
    """Data class for a fuel entry."""

    id: int
    date: str  # Format: YYYY-MM-DD
    liters: float
    price_per_liter: float
    odometer: int
    total_cost: float
