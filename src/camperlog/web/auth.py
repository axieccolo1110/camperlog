"""Login, Logout und die Abhängigkeit "eingeloggt".

Das Passwort steht in ``CAMPERLOG_PASSWORD``. Nach erfolgreichem Login merkt sich
ein signiertes Session-Cookie (Starlette ``SessionMiddleware``), dass man drin ist.
"""

import os
import secrets

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from camperlog.web.templating import templates

SESSION_KEY = "logged_in"

router = APIRouter()


def check_password(candidate: str) -> bool:
    """Vergleicht in konstanter Zeit mit ``CAMPERLOG_PASSWORD``.

    Ist kein Passwort konfiguriert, ist niemals ein Login möglich.
    """
    expected = os.environ.get("CAMPERLOG_PASSWORD", "")
    if not expected:
        return False
    return secrets.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))


def is_logged_in(request: Request) -> bool:
    return request.session.get(SESSION_KEY) is True


def require_login(request: Request) -> None:
    """Gemeinsame Abhängigkeit für alle privaten Routen.

    Die API (``/api/*``) antwortet mit 401, Seiten leiten auf ``/login`` um.
    """
    if is_logged_in(request):
        return
    if request.url.path.startswith("/api/"):
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    raise HTTPException(status_code=303, headers={"Location": "/login"})


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request) -> Response:
    if is_logged_in(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, password: str = Form("")) -> Response:
    if not check_password(password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Falsches Passwort."},
            status_code=401,
        )
    request.session.clear()
    request.session[SESSION_KEY] = True
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request) -> Response:
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
