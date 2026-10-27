"""
db.py
Capa de persistencia para el backend web (server.py). `app.py` también la
importa (desde 2026-10-27) para la cache de vjudge (ver vjudge_cache más
abajo) — el resto de la consola/gui.py sigue con config.json/solved.txt tal
cual, sin tocar Mongo para nada más.

Colecciones en MongoDB:
- known_users: handles vistos en corridas anteriores, para autocompletar.
- saved_lists: corridas guardadas con título editable (lo que generate_*
  produjo), para poder volver a verlas/editarlas después.
- last_configs: los parámetros de la última corrida de cada flujo (uno por
  flujo), para precargar el formulario la próxima vez que se abre la página.
- saved_configs: configuraciones con nombre, guardadas a mano, para volver
  a cargarlas sin tipear todo de nuevo.
- vjudge_cache: último resultado exitoso de `app.fetch_vjudge_rows` por
  (handle, oj_id) — vjudge.net está bloqueado desde Render (ver CONTEXT.md,
  2026-10-27) pero funciona perfecto en local, así que esto deja que una
  corrida en Render use el último dato que sí se consiguió corriendo local,
  en vez de no tener nada.

Si no hay MONGODB_URI configurada (ej. corriendo local sin Mongo todavía),
todas las funciones degradan a no-ops / listas vacías en vez de romper el
resto del server — así se puede probar generación+SSE+login sin Mongo.
"""

import os
from datetime import datetime, timezone

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

_client = None
_db = None


def _get_db():
    global _client, _db
    if _db is not None:
        return _db
    uri = os.environ.get("MONGODB_URI")
    if not uri or MongoClient is None:
        return None
    _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # get_default_database() exige que la URI traiga el nombre de la base
    # (.../nombre_db?...), pero el connection string que da Atlas por default
    # no lo incluye. Con default= no hace falta tocar la URI.
    _db = _client.get_default_database(default="problemshunter")
    return _db


def is_configured():
    return _get_db() is not None


# --- known_users: autocompletado de handles -------------------------------

def remember_users(platform, handles):
    """platform: "codeforces" | "atcoder" | "vjudge". No-op si no hay Mongo."""
    db = _get_db()
    if db is None or not handles:
        return
    now = datetime.now(timezone.utc)
    for handle in handles:
        db.known_users.update_one(
            {"platform": platform, "handle": handle},
            {"$set": {"last_used": now}, "$setOnInsert": {"platform": platform, "handle": handle}},
            upsert=True,
        )


def list_known_users(platform):
    db = _get_db()
    if db is None:
        return []
    cursor = db.known_users.find({"platform": platform}, {"_id": 0, "handle": 1}).sort("last_used", -1)
    return [doc["handle"] for doc in cursor]


# --- saved_lists: corridas guardadas, con título editable -----------------

def _dedupe_title(mongo_db, flow, title):
    """Si el título ya existe en ese flujo, le agrega " (1)", " (2)", etc."""
    existing = {doc["title"] for doc in mongo_db.saved_lists.find({"flow": flow}, {"title": 1, "_id": 0})}
    if title not in existing:
        return title
    i = 1
    while f"{title} ({i})" in existing:
        i += 1
    return f"{title} ({i})"


def save_list(flow, title, params, result_lines, items):
    """items: la lista estructurada de resultados (problems/contests/gyms)
    que ya arma cada flujo, para poder mostrarla de nuevo sin volver a
    generarla. Devuelve el id como string, o None si no hay Mongo (la
    corrida igual funcionó — guardar es best-effort, no bloqueante)."""
    db = _get_db()
    if db is None:
        return None
    now = datetime.now(timezone.utc)
    doc = {
        "flow": flow,
        "title": _dedupe_title(db, flow, title),
        "params": params,
        "result_lines": result_lines,
        "items": items,
        "created_at": now,
        "updated_at": now,
    }
    result = db.saved_lists.insert_one(doc)
    return str(result.inserted_id)


def list_saved_lists(flow=None):
    db = _get_db()
    if db is None:
        return []
    query = {"flow": flow} if flow else {}
    cursor = db.saved_lists.find(
        query, {"result_lines": 0, "items": 0, "params": 0},
    ).sort("created_at", -1)
    out = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        out.append(doc)
    return out


def get_saved_list(list_id):
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return None
    doc = db.saved_lists.find_one({"_id": ObjectId(list_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def update_saved_list(list_id, *, title=None, items=None):
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return False
    updates = {"updated_at": datetime.now(timezone.utc)}
    if title is not None:
        updates["title"] = title
    if items is not None:
        updates["items"] = items
    result = db.saved_lists.update_one({"_id": ObjectId(list_id)}, {"$set": updates})
    return result.matched_count > 0


def delete_saved_list(list_id):
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return False
    result = db.saved_lists.delete_one({"_id": ObjectId(list_id)})
    return result.deleted_count > 0


def remove_item_from_list(list_id, index):
    """Saca el item en esa posición (ej. "ya lo resolví") y reacomoda el
    resto. False si la lista o el índice no existen."""
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return False
    doc = db.saved_lists.find_one({"_id": ObjectId(list_id)}, {"items": 1})
    if doc is None:
        return False
    items = doc.get("items") or []
    if index < 0 or index >= len(items):
        return False
    items.pop(index)
    db.saved_lists.update_one(
        {"_id": ObjectId(list_id)},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}},
    )
    return True


# --- last_configs: parámetros de la última corrida de cada flujo ----------

def remember_last_config(flow, params):
    db = _get_db()
    if db is None:
        return
    db.last_configs.update_one(
        {"flow": flow},
        {"$set": {"params": params, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


def get_last_config(flow):
    db = _get_db()
    if db is None:
        return None
    doc = db.last_configs.find_one({"flow": flow}, {"_id": 0, "params": 1})
    return doc["params"] if doc else None


# --- saved_configs: configuraciones con nombre, guardadas a mano -----------

def save_named_config(flow, name, params):
    """Guarda (o sobreescribe si ya existe ese nombre en el flujo)."""
    db = _get_db()
    if db is None:
        return None
    now = datetime.now(timezone.utc)
    db.saved_configs.update_one(
        {"flow": flow, "name": name},
        {
            "$set": {"params": params, "updated_at": now},
            "$setOnInsert": {"flow": flow, "name": name, "created_at": now},
        },
        upsert=True,
    )
    doc = db.saved_configs.find_one({"flow": flow, "name": name}, {"_id": 1})
    return str(doc["_id"]) if doc else None


def list_named_configs(flow):
    db = _get_db()
    if db is None:
        return []
    cursor = db.saved_configs.find({"flow": flow}, {"params": 0}).sort("name", 1)
    out = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        out.append(doc)
    return out


def get_named_config(config_id):
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return None
    doc = db.saved_configs.find_one({"_id": ObjectId(config_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def delete_named_config(config_id):
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return False
    result = db.saved_configs.delete_one({"_id": ObjectId(config_id)})
    return result.deleted_count > 0


# --- vjudge_cache: último fetch en vivo exitoso de vjudge, por (handle, oj) -

def save_vjudge_cache(handle, oj_id, rows):
    db = _get_db()
    if db is None:
        return
    db.vjudge_cache.update_one(
        {"handle": handle, "oj_id": oj_id},
        {"$set": {"rows": rows, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


def get_vjudge_cache(handle, oj_id):
    db = _get_db()
    if db is None:
        return None
    return db.vjudge_cache.find_one({"handle": handle, "oj_id": oj_id}, {"_id": 0, "rows": 1, "updated_at": 1})
