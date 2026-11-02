// render.js — compartido entre la app (index.html) y la vista pública de una
// lista (share.html): tabla de resultados, descripción de cómo se generó la
// lista, fechas y copiar el link público.

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

// Mongo devuelve datetimes sin zona (son UTC); sin la "Z" el navegador los
// tomaría como hora local.
function fmtDate(iso) {
  if (!iso) return "?";
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`).toLocaleString();
}

function renderResults(container, flow, items) {
  const data = items || [];
  if (data.length === 0) {
    container.innerHTML = "<p>Sin resultados.</p>";
    return;
  }
  const link = (url) => `<a href="${esc(url)}" target="_blank">${esc(url)}</a>`;
  // Verde: completo. Amarillo (solo AtCoder): a medias, con lo que falta.
  const missingText = (item) => (item.missing || []).length ? `faltan ${item.missing.join(", ")}` : "";
  const tr = (item, cells) => {
    const attrs = item.touched ? ' class="touched" title="Completo"'
      : missingText(item) ? ` class="partial" title="${esc(missingText(item))}"` : "";
    return `<tr${attrs}>${cells.map((c) => `<td>${c}</td>`).join("")}</tr>`;
  };
  let head, rows;
  if (flow === "codeforces") {
    head = ["Dificultad/Letra", "Nombre", "Link"];
    rows = data.map((p) => tr(p, [esc(p.label), esc(p.name), link(p.url)]));
  } else if (flow === "atcoder") {
    head = ["Id", "Título", "Link"];
    rows = data.map((c) => {
      const note = missingText(c) ? ` <span class="missing-note">(${esc(missingText(c))})</span>` : "";
      return tr(c, [esc(c.id), esc(c.title) + note, link(c.link)]);
    });
  } else {
    head = ["Id", "Nombre", "Dificultad", "Editorial", "Link"];
    rows = data.map((g) => tr(g, [esc(g.id), esc(g.name), esc(g.difficulty), esc(g.editorial), link(g.link)]));
  }
  container.innerHTML =
    `<table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table>`;
}

const ROUND_LABELS = { div1: "Div.1", div2: "Div.2 (incluye Div.1+2 y Educational)", div3: "Div.3", div4: "Div.4" };

// <dl> con usuarios, parámetros, fechas y progreso de una lista guardada.
function describeList(list) {
  const p = list.params || {};
  const join = (xs) => esc((xs || []).join(", ")) || "—";
  const rows = [];
  if (list.flow === "atcoder") {
    rows.push(["Usuarios AtCoder", join(p.users_atcoder)]);
  } else {
    rows.push(["Usuarios Codeforces", join(p.users)]);
  }
  rows.push(["Usuarios vjudge", join(p.users_vjudge)]);

  if (list.flow === "codeforces") {
    rows.push(p.mode === "letters"
      ? ["Búsqueda", `Por letra: ${join(p.letters)} · ronda ${esc(ROUND_LABELS[p.round_type] || p.round_type)}`]
      : ["Búsqueda", `Por rating: ${join(p.difficulties)}`]);
  } else if (list.flow === "atcoder") {
    const letters = (p.problems || []).map((l) => String(l).toUpperCase());
    rows.push(["Búsqueda", letters.length ? join(letters) : "contest completo"]);
  } else {
    const f = p.filters || {};
    const editorial = p.require_editorial ? " · solo con editorial" : "";
    rows.push(["Búsqueda", `${esc(p.count)} gyms sin tocar · dificultad ${esc(f.difficulty_min ?? "?")}–${esc(f.difficulty_max ?? "?")} ★${editorial}`]);
  }

  rows.push(["Creada", esc(fmtDate(list.created_at))]);
  rows.push(["Última actualización", esc(fmtDate(list.updated_at))]);
  const items = list.items || [];
  const partial = items.filter((it) => !it.touched && (it.missing || []).length).length;
  rows.push(["Progreso", `${items.filter((it) => it.touched).length} de ${items.length} completos${partial ? ` · ${partial} a medias` : ""}`]);
  return `<dl class="list-desc">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>`;
}

function refreshMessage(newlyTouched) {
  if (!newlyTouched) return "nada nuevo completo";
  return newlyTouched === 1 ? "1 nuevo completo (en verde)" : `${newlyTouched} nuevos completos (en verde)`;
}

const SHARE_ICON =
  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>';

// Copia al portapapeles. La Clipboard API puede estar bloqueada (permiso
// denegado, webviews embebidos, http sin TLS); ahí cae a execCommand("copy")
// con un textarea temporal, que no pide permiso. false si ninguno funcionó.
async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (e2) { ok = false; }
    ta.remove();
    return ok;
  }
}

// Botón "copiar link público" de una lista guardada. `onStatus(texto)` avisa
// el resultado (copiado / error).
function shareButton(listId, onStatus) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "share-btn";
  btn.title = "Copiar link público";
  btn.innerHTML = SHARE_ICON;
  btn.addEventListener("click", async () => {
    let url;
    try {
      const res = await fetch(`/api/lists/${listId}/share`);
      if (!res.ok) throw new Error(res.status);
      url = `${location.origin}/s/${(await res.json()).token}`;
    } catch (e) {
      onStatus("no se pudo obtener el link");
      return;
    }
    onStatus(await copyText(url) ? "link copiado" : `copiá el link: ${url}`);
  });
  return btn;
}
