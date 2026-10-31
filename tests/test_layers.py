"""CLI and web must reach the database only through services/."""

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "camperlog"
ENTRY_POINTS = [SRC / "cli.py", *SRC.glob("commands/*.py"), *SRC.glob("web/*.py")]
FORBIDDEN = re.compile(r"^\s*(from|import)\s+(sqlalchemy|camperlog\.models)\b", re.M)


def test_entry_points_do_not_touch_the_orm_directly():
    offenders = [
        str(path.relative_to(SRC))
        for path in ENTRY_POINTS
        if FORBIDDEN.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
