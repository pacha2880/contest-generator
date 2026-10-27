// Cloudflare Worker usado por proxy.py: reenvía GETs a vjudge.net/status/data
// y codeforces.com/gym/* desde la red de Cloudflare (Render está bloqueado
// por reputación de IP). Se pega tal cual en el editor del Worker; necesita
// un Secret PROXY_KEY con el mismo valor que la env var PROXY_KEY de Render.
export default {
  async fetch(request, env) {
    if (!env.PROXY_KEY || request.headers.get("X-Proxy-Key") !== env.PROXY_KEY) {
      return new Response("forbidden", { status: 403 });
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
    return new Response(r.body, {
      status: r.status,
      headers: { "Content-Type": r.headers.get("Content-Type") || "text/plain" },
    });
  },
};
