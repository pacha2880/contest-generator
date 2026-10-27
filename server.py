"""
server.py
Backend web de PachaContests (FastAPI). Pieza nueva y separada — no la usan
ni la consola (`py main.py ...`) ni `gui.py`, que siguen leyendo config.json
exactamente igual que antes. Este server llama a las mismas funciones core
(`app.generate_recommendations`, `atcoder.find_recommended_abc`,
`gym.find_untouched_gyms` + `gym.select_recommendations`) pero con
parámetros que vienen del formulario web, no de config.json.

Cada corrida se ejecuta en un hilo aparte (igual que gui.py) y transmite
el progreso al navegador vía Server-Sent Events en vez de
window.write_event_value — mismo patrón de fondo (cola + callback), distinto
transporte.

Correr local:
    py -m uvicorn server:app --reload
Variables de entorno (todas opcionales para desarrollo local, ver .env):
    APP_PASSWORD   contraseña compartida; sin ella el login queda abierto
    SECRET_KEY     firma de la cookie de sesión; sin ella usa un valor fijo
                   de desarrollo (cambiarla es obligatorio en producción)
    MONGODB_URI    sin ella, "usuarios recordados" y "listas guardadas"
                   quedan vacíos pero el resto del server funciona igual

En local estas variables se leen de un archivo .env (vía python-dotenv) si
existe. En Render se setean directo como env vars del servicio, así que ahí
no hace falta ningún .env.
"""

import json
import os
import queue
import threading
import uuid
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import app as cf_app
import atcoder
import auth
import db
import gym
from cancel import StoppedByUser

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-change-in-production")

# No automation around this yet (no CHANGELOG.md, no CI check) — bump by hand
# alongside a meaningful batch of changes to the web UI/backend.
APP_VERSION = "0.4.0"

app = FastAPI(title="PachaContests")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals["app_version"] = APP_VERSION


# ---------------------------------------------------------------------------
# Run manager: one background thread + progress queue per run, keyed by a
# random run_id the browser polls via SSE. In-memory only (RUNS dict) — fine
# for a single Uvicorn worker, which is what this project needs; would need
# a shared store (ej. Redis) if this ever ran with multiple worker processes.
# ---------------------------------------------------------------------------

class RunState:
    def __init__(self):
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.status = "running"  # running | ok | stopped | error
        self.error = None
        self.result = None


RUNS = {}
RUNS_LOCK = threading.Lock()


def _new_run():
    run_id = uuid.uuid4().hex
    state = RunState()
    with RUNS_LOCK:
        RUNS[run_id] = state
    return run_id, state


def _finish(state, status, error=None, result=None):
    state.status = status
    state.error = error
    state.result = result
    state.queue.put(None)  # sentinel: tells the SSE stream to close


def _run_codeforces(state, payload):
    on_progress = state.queue.put
    try:
        db.remember_last_config("codeforces", payload)
        users = payload.get("users", [])
        users_vjudge = payload.get("users_vjudge", [])
        mode = payload.get("mode", "difficulties")
        result_lines, newly_recommended, items = cf_app.generate_recommendations(
            users, mode,
            difficulties=payload.get("difficulties"),
            letters=payload.get("letters"),
            round_type=payload.get("round_type", "div2"),
            users_vjudge=users_vjudge,
            on_progress=on_progress,
            should_stop=state.stop_event.is_set,
        )
        db.remember_users("codeforces", users)
        db.remember_users("vjudge", users_vjudge)
        list_id = db.save_list("codeforces", payload.get("title") or "Sin título", payload, result_lines, items)
        _finish(state, "ok", result={"items": items, "list_id": list_id})
    except StoppedByUser:
        _finish(state, "stopped")
    except Exception as e:
        _finish(state, "error", error=str(e))


def _run_atcoder(state, payload):
    on_progress = state.queue.put
    try:
        db.remember_last_config("atcoder", payload)
        users_atcoder = payload.get("users_atcoder", [])
        users_vjudge = payload.get("users_vjudge", [])
        count = int(payload.get("count", 5))
        lookback = int(payload.get("lookback", 50))
        problem_letters = payload.get("problems") or None
        recommended = atcoder.find_recommended_abc(
            users_atcoder, users_vjudge, count, lookback,
            on_progress=on_progress, problem_letters=problem_letters,
            should_stop=state.stop_event.is_set,
        )
        items = [
            {"id": c["id"], "title": c.get("title", c["id"]), "link": atcoder.build_link(c["id"])}
            for c in recommended
        ]
        db.remember_users("atcoder", users_atcoder)
        db.remember_users("vjudge", users_vjudge)
        list_id = db.save_list("atcoder", payload.get("title") or "Sin título", payload, [], items)
        _finish(state, "ok", result={"items": items, "list_id": list_id})
    except StoppedByUser:
        _finish(state, "stopped")
    except Exception as e:
        _finish(state, "error", error=str(e))


def _run_gym(state, payload):
    on_progress = state.queue.put
    try:
        db.remember_last_config("gym", payload)
        users = payload.get("users", [])
        users_vjudge = payload.get("users_vjudge", [])
        filters = payload.get("filters", {})
        count = int(payload.get("count", 10))
        require_editorial = bool(payload.get("require_editorial", False))
        untouched = gym.find_untouched_gyms(
            users, filters, users_vjudge=users_vjudge,
            on_progress=on_progress, should_stop=state.stop_event.is_set,
        )
        recommended, editorials = gym.select_recommendations(
            untouched, count, require_editorial,
            on_progress=on_progress, should_stop=state.stop_event.is_set,
        )
        items = []
        for contest in recommended:
            found = editorials.get(contest["id"])
            editorial = "yes" if found is True else "no" if found is False else "unknown"
            items.append({
                "id": contest["id"],
                "name": contest["name"],
                "difficulty": contest.get("difficulty", ""),
                "editorial": editorial,
                "link": f"https://codeforces.com/gym/{contest['id']}",
            })
        db.remember_users("codeforces", users)
        db.remember_users("vjudge", users_vjudge)
        list_id = db.save_list("gym", payload.get("title") or "Sin título", payload, [], items)
        _finish(state, "ok", result={"items": items, "list_id": list_id})
    except StoppedByUser:
        _finish(state, "stopped")
    except Exception as e:
        _finish(state, "error", error=str(e))


RUNNERS = {"codeforces": _run_codeforces, "atcoder": _run_atcoder, "gym": _run_gym}


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login")
def login_submit(request: Request, password: str = Form(...)):
    if auth.check_password(password):
        request.session["authenticated"] = True
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request, "login.html", {"error": "Contraseña incorrecta"}, status_code=401,
    )


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    if not auth.require_login_page(request):
        return auth.redirect_to_login()
    return templates.TemplateResponse(request, "index.html", {})


# ---------------------------------------------------------------------------
# API: correr un flujo + progreso en vivo
# ---------------------------------------------------------------------------

@app.post("/api/run/{flow}")
async def start_run(flow: str, request: Request, _=Depends(auth.require_login_api)):
    if flow not in RUNNERS:
        raise HTTPException(404, f"Flujo desconocido: {flow}")
    payload = await request.json()
    run_id, state = _new_run()
    threading.Thread(target=RUNNERS[flow], args=(state, payload), daemon=True).start()
    return {"run_id": run_id}


@app.get("/api/run/{run_id}/stream")
def stream_run(run_id: str, _=Depends(auth.require_login_api)):
    """Sync def a propósito: FastAPI corre las rutas sync en un threadpool,
    así que el `queue.get()` bloqueante de acá adentro no traba el event
    loop del resto del server mientras espera el próximo mensaje."""
    state = RUNS.get(run_id)
    if state is None:
        raise HTTPException(404, "Corrida no encontrada")

    def event_stream():
        while True:
            msg = state.queue.get()
            if msg is None:
                break
            yield f"data: {json.dumps(msg)}\n\n"
        done_payload = {"status": state.status, "error": state.error, "result": state.result}
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/run/{run_id}/stop")
def stop_run(run_id: str, _=Depends(auth.require_login_api)):
    state = RUNS.get(run_id)
    if state is None:
        raise HTTPException(404, "Corrida no encontrada")
    state.stop_event.set()
    return {"ok": True}


# ---------------------------------------------------------------------------
# API: usuarios recordados (autocompletado)
# ---------------------------------------------------------------------------

@app.get("/api/known-users")
def known_users(platform: str, _=Depends(auth.require_login_api)):
    return db.list_known_users(platform)


# ---------------------------------------------------------------------------
# API: listas guardadas (CRUD liviano)
# ---------------------------------------------------------------------------

class UpdateListBody(BaseModel):
    title: Optional[str] = None
    items: Optional[List[dict]] = None


@app.get("/api/lists")
def api_list_saved(flow: Optional[str] = None, _=Depends(auth.require_login_api)):
    return db.list_saved_lists(flow)


@app.get("/api/lists/{list_id}")
def api_get_saved(list_id: str, _=Depends(auth.require_login_api)):
    doc = db.get_saved_list(list_id)
    if doc is None:
        raise HTTPException(404, "No encontrada")
    return doc


@app.patch("/api/lists/{list_id}")
def api_update_saved(list_id: str, body: UpdateListBody, _=Depends(auth.require_login_api)):
    ok = db.update_saved_list(list_id, title=body.title, items=body.items)
    if not ok:
        raise HTTPException(404, "No encontrada")
    return {"ok": True}


@app.delete("/api/lists/{list_id}")
def api_delete_saved(list_id: str, _=Depends(auth.require_login_api)):
    ok = db.delete_saved_list(list_id)
    if not ok:
        raise HTTPException(404, "No encontrada")
    return {"ok": True}


@app.delete("/api/lists/{list_id}/items/{index}")
def api_delete_saved_item(list_id: str, index: int, _=Depends(auth.require_login_api)):
    """Saca un contest/problema puntual de una lista guardada (ej. "ya lo
    resolví"), sin borrar la lista entera."""
    ok = db.remove_item_from_list(list_id, index)
    if not ok:
        raise HTTPException(404, "No encontrada")
    return {"ok": True}


# ---------------------------------------------------------------------------
# API: configuraciones (último uso por flujo + configs con nombre guardadas)
# ---------------------------------------------------------------------------

class SaveConfigBody(BaseModel):
    name: str
    params: dict


@app.get("/api/configs/{flow}/last")
def api_get_last_config(flow: str, _=Depends(auth.require_login_api)):
    return {"params": db.get_last_config(flow)}


@app.get("/api/configs/{flow}")
def api_list_configs(flow: str, _=Depends(auth.require_login_api)):
    return db.list_named_configs(flow)


@app.post("/api/configs/{flow}")
def api_save_config(flow: str, body: SaveConfigBody, _=Depends(auth.require_login_api)):
    config_id = db.save_named_config(flow, body.name, body.params)
    return {"_id": config_id}


@app.get("/api/configs/{flow}/{config_id}")
def api_get_config(flow: str, config_id: str, _=Depends(auth.require_login_api)):
    doc = db.get_named_config(config_id)
    if doc is None:
        raise HTTPException(404, "No encontrada")
    return doc


@app.delete("/api/configs/{flow}/{config_id}")
def api_delete_config(flow: str, config_id: str, _=Depends(auth.require_login_api)):
    ok = db.delete_named_config(config_id)
    if not ok:
        raise HTTPException(404, "No encontrada")
    return {"ok": True}


@app.get("/api/health")
def health():
    return JSONResponse({"ok": True, "db": db.is_configured()})
