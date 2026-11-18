"""
users.py
Manejo de las cuentas del login web (colección `users`, ver db.py), desde la
consola: sin correo ni servicios externos. Usa la MONGODB_URI de .env, o sea
la misma base que el deploy.

    py users.py list
    py users.py create <usuario> [--admin]      contraseña aleatoria, se imprime
    py users.py passwd <usuario> [contraseña]   sin contraseña: aleatoria, se imprime
    py users.py rename <usuario> <nuevo>        también pasa sus listas/configs
    py users.py delete <usuario>                solo la cuenta; sus listas quedan
    py users.py migrate                         una vez: crea pacha2880 (admin) con
                                                la APP_PASSWORD de .env y le asigna
                                                todo lo guardado sin dueño
"""

import argparse
import os
import secrets
import sys

from dotenv import load_dotenv

load_dotenv()

import db

ADMIN = "pacha2880"


def random_password():
    return secrets.token_urlsafe(9)


def main():
    parser = argparse.ArgumentParser(description="Cuentas del login de PachaContests")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("create")
    p.add_argument("username")
    p.add_argument("--admin", action="store_true")
    p = sub.add_parser("passwd")
    p.add_argument("username")
    p.add_argument("password", nargs="?")
    p = sub.add_parser("rename")
    p.add_argument("username")
    p.add_argument("new_username")
    p = sub.add_parser("delete")
    p.add_argument("username")
    sub.add_parser("migrate")
    args = parser.parse_args()

    if not db.is_configured():
        sys.exit("Falta MONGODB_URI (en .env).")

    if args.cmd == "list":
        for u in db.list_users():
            print(u["username"] + ("  (admin)" if u.get("is_admin") else ""))
    elif args.cmd == "create":
        password = random_password()
        if not db.create_user(args.username, password, is_admin=args.admin):
            sys.exit(f"Ya existe '{args.username}'.")
        print(f"{args.username}\t{password}")
    elif args.cmd == "passwd":
        password = args.password or random_password()
        if not db.set_password(args.username, password):
            sys.exit(f"No existe '{args.username}'.")
        if not args.password:
            print(f"{args.username}\t{password}")
    elif args.cmd == "rename":
        if not db.rename_user(args.username, args.new_username):
            sys.exit(f"No existe '{args.username}' o ya existe '{args.new_username}'.")
    elif args.cmd == "delete":
        if not db.delete_user(args.username):
            sys.exit(f"No existe '{args.username}'.")
    elif args.cmd == "migrate":
        password = os.environ.get("APP_PASSWORD")
        if not password:
            sys.exit("Falta APP_PASSWORD (en .env): es la contraseña que conserva pacha2880.")
        created = db.create_user(ADMIN, password, is_admin=True)
        print(f"{ADMIN}: {'creado (admin)' if created else 'ya existía'}")
        for name, n in db.assign_unowned(ADMIN).items():
            print(f"  {name}: {n} documentos pasados a {ADMIN}")


if __name__ == "__main__":
    main()
