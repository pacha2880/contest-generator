// share.js — vista pública de una lista guardada (/s/{token}): la lista, cómo
// se generó y el botón Actualizar, sin login.

const token = document.querySelector(".share-page").dataset.token;
const titleEl = document.getElementById("share-title");
const descEl = document.getElementById("share-desc");
const resultsEl = document.getElementById("share-results");
const actionsEl = document.querySelector(".share-actions");
const refreshBtn = document.getElementById("share-refresh");
const statusEl = document.getElementById("share-status");

function show(list) {
  titleEl.textContent = list.title || "Lista sin título";
  document.title = `${list.title || "Lista"} — PachaContests`;
  descEl.innerHTML = describeList(list);
  renderResults(resultsEl, list.flow, list.items);
  actionsEl.hidden = false;
}

async function load() {
  const res = await fetch(`/api/public/${encodeURIComponent(token)}`);
  if (!res.ok) {
    titleEl.textContent = "Lista no encontrada";
    return;
  }
  show(await res.json());
}

refreshBtn.addEventListener("click", async () => {
  refreshBtn.disabled = true;
  statusEl.textContent = "actualizando...";
  try {
    const res = await fetch(`/api/public/${encodeURIComponent(token)}/refresh`, { method: "POST" });
    if (!res.ok) throw new Error(res.status);
    const list = await res.json();
    show(list);
    statusEl.textContent = refreshMessage(list.newly_touched);
  } catch (e) {
    statusEl.textContent = "no se pudo actualizar";
  } finally {
    refreshBtn.disabled = false;
  }
});

load();
