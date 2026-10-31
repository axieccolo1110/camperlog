"""Configuration from environment variables.

The web server only starts if the password and the secret key are set, so no
instance accidentally goes online unprotected.
"""

import os

REQUIRED_WEB_VARS = ("CAMPERLOG_PASSWORD", "CAMPERLOG_SECRET_KEY")


class ConfigError(RuntimeError):
    """The configuration is incomplete."""


def missing_web_vars() -> list[str]:
    """Names of the required web server variables that are missing or empty."""
    return [name for name in REQUIRED_WEB_VARS if not os.environ.get(name, "").strip()]


def require_web_config() -> None:
    """Raise ConfigError with a clear (German) message if a variable is missing."""
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
