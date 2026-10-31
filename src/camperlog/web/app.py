"""FastAPI app: lifespan, session middleware, routers and health check."""

import os
from contextlib import asynccontextmanager
from functools import cache

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from camperlog.config import ConfigError, require_web_config
from camperlog.db import require_current_schema
from camperlog.web import api, auth, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    require_current_schema()
    yield


def use_https_only_cookie() -> bool:
    """Send the session cookie over HTTPS only?

    Railway sets ``RAILWAY_ENVIRONMENT`` automatically in every deployment, and
    the site is always served over HTTPS there. Locally (``http://127.0.0.1``) a
    Secure cookie would be useless because the browser does not send it back.
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
        # Railway starts uvicorn directly. SystemExit with a string prints only the
        # message instead of a traceback and ends the process with exit code 1.
        raise SystemExit(f"Fehler: {e}") from None


def __getattr__(name: str) -> FastAPI:
    # ``app`` is built on first access (uvicorn ``camperlog.web.app:app``), so
    # importing the module, e.g. in tests, needs no environment variables.
    if name == "app":
        return _build_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
