"""
db.py
Capa de persistencia para el backend web (server.py).
La consola/gui.py siguen con config.json/solved.txt tal cual, sin tocar
Mongo.

Colecciones en MongoDB:
- users: cuentas para el login (usuario + contraseña con hash PBKDF2, sin
  correo). Se manejan con el script users.py. `is_admin` ve todas las listas.
- known_users: handles vistos en corridas anteriores, para autocompletar.
- saved_lists: corridas guardadas con título editable (lo que generate_*
  produjo), para poder volver a verlas/editarlas después.
- last_configs: los parámetros de la última corrida de cada flujo (uno por
  flujo), para precargar el formulario la próxima vez que se abre la página.
- saved_configs: configuraciones con nombre, guardadas a mano, para volver
  a cargarlas sin tipear todo de nuevo.

Todo lo demás tiene `owner` (el usuario dueño); cada función recibe el
`owner` con el que filtra.

Si no hay MONGODB_URI configurada (ej. corriendo local sin Mongo todavía),
todas las funciones degradan a no-ops / listas vacías en vez de romper el
resto del server — así se puede probar generación+SSE+login sin Mongo.
"""

import hashlib
import hmac
import os
import secrets
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


# --- users: cuentas del login ---------------------------------------------

PBKDF2_ITERATIONS = 200_000


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS).hex()


def _password_fields(password):
    salt = secrets.token_bytes(16)
    return {"salt": salt.hex(), "password_hash": _hash_password(password, salt)}


def get_user(username):
    db = _get_db()
    if db is None:
        return None
    return db.users.find_one({"username": username}, {"_id": 0, "username": 1, "is_admin": 1})


def verify_user(username, password):
    """El usuario (sin el hash) si la contraseña es correcta; si no, None."""
    db = _get_db()
    if db is None:
        return None
    doc = db.users.find_one({"username": username})
    if doc is None:
        return None
    expected = _hash_password(password, bytes.fromhex(doc["salt"]))
    if not hmac.compare_digest(expected, doc["password_hash"]):
        return None
    return {"username": doc["username"], "is_admin": bool(doc.get("is_admin"))}


def create_user(username, password, *, is_admin=False):
    """False si ya existe ese usuario."""
    db = _get_db()
    if db.users.find_one({"username": username}):
        return False
    db.users.insert_one({
        "username": username,
        "is_admin": is_admin,
        "created_at": datetime.now(timezone.utc),
        **_password_fields(password),
    })
    return True


def set_password(username, password):
    result = _get_db().users.update_one({"username": username}, {"$set": _password_fields(password)})
    return result.matched_count > 0


OWNED_COLLECTIONS = ("saved_lists", "saved_configs", "last_configs", "known_users")


def rename_user(old, new):
    """Renombra la cuenta y pasa todo lo suyo (listas, configs) al nombre
    nuevo. False si `old` no existe o `new` ya está usado."""
    db = _get_db()
    if db.users.find_one({"username": new}) or not db.users.find_one({"username": old}):
        return False
    db.users.update_one({"username": old}, {"$set": {"username": new}})
    for name in OWNED_COLLECTIONS:
        db[name].update_many({"owner": old}, {"$set": {"owner": new}})
    return True


def delete_user(username):
    """Borra solo la cuenta; sus listas quedan en Mongo (las ve el admin)."""
    return _get_db().users.delete_one({"username": username}).deleted_count > 0


def list_users():
    return list(_get_db().users.find({}, {"_id": 0, "username": 1, "is_admin": 1}).sort("username", 1))


def assign_unowned(owner):
    """Pone `owner` en todo lo guardado antes de que existieran usuarios.
    Devuelve cuántos documentos cambió por colección."""
    db = _get_db()
    return {
        name: db[name].update_many({"owner": {"$exists": False}}, {"$set": {"owner": owner}}).modified_count
        for name in OWNED_COLLECTIONS
    }


# --- known_users: autocompletado de handles -------------------------------

def remember_users(platform, handles, owner):
    """platform: "codeforces" | "atcoder" | "vjudge". No-op si no hay Mongo."""
    db = _get_db()
    if db is None or not handles:
        return
    now = datetime.now(timezone.utc)
    for handle in handles:
        key = {"platform": platform, "handle": handle, "owner": owner}
        db.known_users.update_one(key, {"$set": {"last_used": now}, "$setOnInsert": key}, upsert=True)


def list_known_users(platform, owner):
    db = _get_db()
    if db is None:
        return []
    cursor = db.known_users.find({"platform": platform, "owner": owner}, {"_id": 0, "handle": 1}).sort("last_used", -1)
    return [doc["handle"] for doc in cursor]


# --- saved_lists: corridas guardadas, con título editable -----------------

def _dedupe_title(mongo_db, flow, title, owner):
    """Si el título ya existe en ese flujo (del mismo dueño), le agrega
    " (1)", " (2)", etc."""
    existing = {doc["title"] for doc in mongo_db.saved_lists.find({"flow": flow, "owner": owner}, {"title": 1, "_id": 0})}
    if title not in existing:
        return title
    i = 1
    while f"{title} ({i})" in existing:
        i += 1
    return f"{title} ({i})"


def save_list(flow, title, params, result_lines, items, owner):
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
        "owner": owner,
        "title": _dedupe_title(db, flow, title, owner),
        "params": params,
        "result_lines": result_lines,
        "items": items,
        "share_token": secrets.token_urlsafe(12),
        "created_at": now,
        "updated_at": now,
    }
    result = db.saved_lists.insert_one(doc)
    return str(result.inserted_id)


def list_saved_lists(flow=None, owner=None):
    """owner=None: las de todos (para el admin)."""
    db = _get_db()
    if db is None:
        return []
    query = {"flow": flow} if flow else {}
    if owner is not None:
        query["owner"] = owner
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


def get_share_token(list_id):
    """Token del link público de la lista (fijo, nunca se regenera). Las
    listas guardadas antes de que existiera esto lo reciben acá, la primera
    vez que alguien lo pide. None si la lista no existe."""
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return None
    doc = db.saved_lists.find_one({"_id": ObjectId(list_id)}, {"share_token": 1})
    if doc is None:
        return None
    if not doc.get("share_token"):
        token = secrets.token_urlsafe(12)
        db.saved_lists.update_one({"_id": doc["_id"], "share_token": None}, {"$set": {"share_token": token}})
        doc = db.saved_lists.find_one({"_id": doc["_id"]}, {"share_token": 1})
    return doc["share_token"]


def get_list_by_share_token(token):
    db = _get_db()
    if db is None:
        return None
    doc = db.saved_lists.find_one({"share_token": token})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def update_saved_list(list_id, *, title=None, items=None, params=None):
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return False
    updates = {"updated_at": datetime.now(timezone.utc)}
    if title is not None:
        updates["title"] = title
    if items is not None:
        updates["items"] = items
    if params is not None:
        updates["params"] = params
    result = db.saved_lists.update_one({"_id": ObjectId(list_id)}, {"$set": updates})
    return result.matched_count > 0


def delete_saved_list(list_id):
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return False
    result = db.saved_lists.delete_one({"_id": ObjectId(list_id)})
    return result.deleted_count > 0


# --- last_configs: parámetros de la última corrida de cada flujo ----------

def remember_last_config(flow, params, owner):
    db = _get_db()
    if db is None:
        return
    db.last_configs.update_one(
        {"flow": flow, "owner": owner},
        {"$set": {"params": params, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


def get_last_config(flow, owner):
    db = _get_db()
    if db is None:
        return None
    doc = db.last_configs.find_one({"flow": flow, "owner": owner}, {"_id": 0, "params": 1})
    return doc["params"] if doc else None


# --- saved_configs: configuraciones con nombre, guardadas a mano -----------

def save_named_config(flow, name, params, owner):
    """Guarda (o sobreescribe si ya existe ese nombre en el flujo)."""
    db = _get_db()
    if db is None:
        return None
    now = datetime.now(timezone.utc)
    key = {"flow": flow, "name": name, "owner": owner}
    db.saved_configs.update_one(
        key,
        {"$set": {"params": params, "updated_at": now}, "$setOnInsert": {**key, "created_at": now}},
        upsert=True,
    )
    doc = db.saved_configs.find_one(key, {"_id": 1})
    return str(doc["_id"]) if doc else None


def list_named_configs(flow, owner):
    db = _get_db()
    if db is None:
        return []
    cursor = db.saved_configs.find({"flow": flow, "owner": owner}, {"params": 0}).sort("name", 1)
    out = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        out.append(doc)
    return out


def get_named_config(config_id, owner):
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return None
    doc = db.saved_configs.find_one({"_id": ObjectId(config_id), "owner": owner})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def delete_named_config(config_id, owner):
    from bson import ObjectId
    db = _get_db()
    if db is None:
        return False
    result = db.saved_configs.delete_one({"_id": ObjectId(config_id), "owner": owner})
    return result.deleted_count > 0
