"""German texts for values that are stored in English (what users see)."""

STATUS_LABELS = {"visited": "besucht", "bookmarked": "vorgemerkt"}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)
