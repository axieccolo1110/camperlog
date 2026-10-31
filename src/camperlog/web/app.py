"""FastAPI-App: Lifespan, Session-Middleware, Router und Healthcheck."""

import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

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
    # Ohne CAMPERLOG_SECRET_KEY gilt ein zufälliger Schlüssel pro Prozess: Logins
    # überleben keinen Neustart, aber niemand kann Cookies fälschen. (Der
    # Webserver-Start ohne Schlüssel wird in F1.2 ganz verhindert.)
    secret_key = os.environ.get("CAMPERLOG_SECRET_KEY") or secrets.token_urlsafe(32)

    app = FastAPI(title="CamperLog API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
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


app = create_app()
