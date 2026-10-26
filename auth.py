"""
auth.py
Login súper simple: una sola contraseña compartida (APP_PASSWORD env var),
sin cuentas individuales. Quien la tenga, entra. La sesión se guarda en una
cookie firmada (SessionMiddleware de Starlette, agregado en server.py).

Si APP_PASSWORD no está seteada (ej. corriendo local para probar), el gate
queda abierto — no hace falta inventar una contraseña solo para desarrollar.
"""

import os

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse


def check_password(password):
    expected = os.environ.get("APP_PASSWORD")
    if not expected:
        return True
    return password == expected


def is_logged_in(request: Request) -> bool:
    if not os.environ.get("APP_PASSWORD"):
        return True
    return bool(request.session.get("authenticated"))


def require_login_page(request: Request):
    """Para rutas de página completa: si no hay sesión, redirige a /login
    en vez de tirar un error — se usa a mano en cada route (ver server.py),
    no como Depends(), porque FastAPI no deja que un Depends devuelva una
    respuesta distinta sin más ceremonia que simplemente chequear inline."""
    return is_logged_in(request)


def require_login_api(request: Request):
    """Para rutas de API/SSE: Depends() que corta con 401 si no hay sesión."""
    if not is_logged_in(request):
        raise HTTPException(status_code=401, detail="No autenticado")


def redirect_to_login():
    return RedirectResponse("/login", status_code=303)
