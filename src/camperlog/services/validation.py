"""Checks shared by several services. Messages are German (shown to the user)."""

from camperlog.services.errors import ValidationError


def check_coordinate_ranges(lat: float | None, lon: float | None) -> None:
    """Latitude and longitude must be within their ranges, if given."""
    if lat is not None and not -90 <= lat <= 90:
        raise ValidationError("Die Breite muss zwischen -90 und 90 liegen.")
    if lon is not None and not -180 <= lon <= 180:
        raise ValidationError("Die Länge muss zwischen -180 und 180 liegen.")
