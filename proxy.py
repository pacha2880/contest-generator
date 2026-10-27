"""
proxy.py
Relay opcional a través de un Cloudflare Worker (código en
cloudflare_worker.js) para los dos scrapes que Cloudflare bloquea desde las
IPs del datacenter de Render: vjudge.net/status/data y las páginas de gym de
codeforces.com. El Worker pide desde la red de Cloudflare, que esos dos sitios
dejan pasar (confirmado 2026-10-27).

Se activa si PROXY_URL y PROXY_KEY están en el entorno (solo se setean en
Render); si no (local), los llamadores hacen su fetch directo. Sin fallback
entre ambos.
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def is_configured():
    return bool(os.environ.get("PROXY_URL") and os.environ.get("PROXY_KEY"))


def proxy_get(url, *, timeout=20):
    """(status_code_or_None, body) — nunca levanta excepción, mismo contrato
    que app._vjudge_fetch_page."""
    try:
        r = requests.get(
            os.environ["PROXY_URL"],
            params={"url": url},
            headers={"X-Proxy-Key": os.environ["PROXY_KEY"]},
            timeout=timeout,
        )
        return r.status_code, r.text
    except Exception as e:
        return None, f"(excepción: {e})"
