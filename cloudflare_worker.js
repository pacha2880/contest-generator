// Cloudflare Worker usado por proxy.py: reenvía GETs a vjudge.net/status/data
// y codeforces.com/gym/* desde la red de Cloudflare (Render está bloqueado
// por reputación de IP). Se pega tal cual en el editor del Worker; necesita
// un Secret PROXY_KEY con el mismo valor que la env var PROXY_KEY de Render.
// Placement: Region → GCP southamerica-east1 (Settings → Runtime). Sin eso
// corre cerca de Render (colo PDX) y vjudge le sirve el challenge.
export default {
  async fetch(request, env) {
    if (!env.PROXY_KEY || request.headers.get("X-Proxy-Key") !== env.PROXY_KEY) {
      // 401 (no 403) para no confundirlo con un 403 de vjudge/Codeforces.
      return new Response("bad proxy key", { status: 401 });
    }
    let target;
    try {
      target = new URL(new URL(request.url).searchParams.get("url"));
    } catch {
      return new Response("bad url", { status: 400 });
    }

    // Solo estos dos destinos, para que no sea un proxy abierto.
    const ok =
      (target.hostname === "vjudge.net" && target.pathname === "/status/data") ||
      (target.hostname === "codeforces.com" && target.pathname.startsWith("/gym/"));
    if (target.protocol !== "https:" || !ok) {
      return new Response("target not allowed", { status: 400 });
    }

    const r = await fetch(target.toString(), {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/json,*/*",
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    const body = await r.text();
    if (r.status !== 200) {
      // Visible en Observability del Worker.
      console.log(`upstream ${r.status} (colo ${request.cf?.colo}): ${body.slice(0, 200)}`);
    }
    return new Response(body, {
      status: r.status,
      headers: { "Content-Type": r.headers.get("Content-Type") || "text/plain" },
    });
  },
};
