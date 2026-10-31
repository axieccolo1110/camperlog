"""FastAPI-App: Lifespan, Session-Middleware, Router und Healthcheck."""

import os
from contextlib import asynccontextmanager
from functools import cache

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from camperlog.config import ConfigError, require_web_config
from camperlog.database import init_db
from camperlog.web import api, auth, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def use_https_only_cookie() -> bool:
    """Session-Cookie nur über HTTPS schicken?

    Railway setzt ``RAILWAY_ENVIRONMENT`` automatisch in jedem Deployment, dort
    läuft die Seite immer über HTTPS. Lokal (``http://127.0.0.1``) wäre ein
    Secure-Cookie unbrauchbar, weil der Browser es nicht zurückschickt.
    """
    return bool(os.environ.get("RAILWAY_ENVIRONMENT"))


def create_app() -> FastAPI:
    require_web_config()

    app = FastAPI(title="CamperLog API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.environ["CAMPERLOG_SECRET_KEY"],
        https_only=use_https_only_cookie(),
        same_site="lax",
    )
    app.include_router(auth.router)
    app.include_router(pages.router)
    app.include_router(api.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


@cache
def _build_app() -> FastAPI:
    try:
        return create_app()
    except ConfigError as e:
        # Railway startet uvicorn direkt. SystemExit mit Text gibt nur die Meldung
        # aus statt eines Tracebacks und beendet den Prozess mit Fehlercode 1.
        raise SystemExit(f"Fehler: {e}") from None


def __getattr__(name: str) -> FastAPI:
    # ``app`` wird erst beim ersten Zugriff gebaut (uvicorn ``camperlog.web.app:app``).
    # Ein Import des Moduls, etwa in Tests, braucht deshalb keine Umgebungsvariablen.
    if name == "app":
        return _build_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
