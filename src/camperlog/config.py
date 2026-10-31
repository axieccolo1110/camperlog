"""Konfiguration aus Umgebungsvariablen.

Der Webserver startet nur, wenn Passwort und Secret gesetzt sind. So geht keine
Instanz versehentlich ohne Schutz online.
"""

import os

REQUIRED_WEB_VARS = ("CAMPERLOG_PASSWORD", "CAMPERLOG_SECRET_KEY")


class ConfigError(RuntimeError):
    """Die Konfiguration ist unvollständig."""


def missing_web_vars() -> list[str]:
    """Namen der Pflichtvariablen für den Webserver, die fehlen oder leer sind."""
    return [name for name in REQUIRED_WEB_VARS if not os.environ.get(name, "").strip()]


def require_web_config() -> None:
    """Bricht mit klarer Meldung ab, wenn für den Webserver etwas fehlt."""
    missing = missing_web_vars()
    if missing:
        raise ConfigError(
            f"Der Webserver startet nicht: {' und '.join(missing)} "
            f"{'ist' if len(missing) == 1 else 'sind'} nicht gesetzt. "
            "Beide Variablen sind Pflicht, damit keine Instanz ungeschützt online "
            "geht. Beispiel: CAMPERLOG_PASSWORD=<passwort> "
            "CAMPERLOG_SECRET_KEY=\"$(python -c 'import secrets; "
            "print(secrets.token_urlsafe(32))')\""
        )
