"""
auth.py
Login con usuario y contraseña (colección `users` de Mongo, ver db.py; las
cuentas se crean con el script users.py, sin correo ni servicios externos).
La sesión guarda solo el nombre de usuario en una cookie firmada
(SessionMiddleware de Starlette, agregado en server.py); en cada request se
vuelve a leer la cuenta, así borrarla o quitarle el admin corta al instante.

Sin MONGODB_URI (ej. corriendo local para probar) no hay cuentas: el gate
queda abierto como un admin "local".
"""

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

import db

LOCAL_USER = {"username": "local", "is_admin": True}


def login(request: Request, username, password):
    """True y abre la sesión si las credenciales son correctas."""
    user = db.verify_user(username, password)
    if user is None:
        return False
    request.session.clear()
    request.session["user"] = user["username"]
    return True


def current_user(request: Request):
    """{"username", "is_admin"} del usuario logueado, o None."""
    if not db.is_configured():
        return LOCAL_USER
    username = request.session.get("user")
    if not username:
        return None
    user = db.get_user(username)
    if user is None:
        return None
    return {"username": user["username"], "is_admin": bool(user.get("is_admin"))}


def require_login_api(request: Request):
    """Para rutas de API/SSE: Depends() que devuelve el usuario logueado o
    corta con 401 si no hay sesión."""
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user


def redirect_to_login():
    return RedirectResponse("/login", status_code=303)
