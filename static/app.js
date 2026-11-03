// app.js — frontend puro (sin framework): tabs, autocompletado, correr un
// flujo + progreso en vivo por SSE, y la pantalla de listas guardadas.

function splitCsv(value) {
  return value.split(",").map((s) => s.trim()).filter(Boolean);
}

// ---------------------------------------------------------------- Tabs ----

// La última pestaña abierta se recuerda en este navegador; sin una guardada
// arranca en la Guía (la activa por defecto en el HTML).
const LAST_TAB_KEY = "lastTab";

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`panel-${btn.dataset.tab}`).classList.add("active");
    try { localStorage.setItem(LAST_TAB_KEY, btn.dataset.tab); } catch (e) {}
    if (btn.dataset.tab === "saved") loadSavedLists();
  });
});

// ---------------------------------------------------- Modo CF: rating/letra

// Switch: apagado = por rating, prendido = por letra. Los campos del otro
// modo quedan visibles pero deshabilitados (y FormData los ignora).
const cfModeToggle = document.querySelector('.run-form[data-flow="codeforces"] .mode-toggle');

function cfMode() {
  return cfModeToggle.checked ? "letters" : "difficulties";
}

if (cfModeToggle) {
  cfModeToggle.addEventListener("change", () => {
    const mode = cfMode();
    document.querySelectorAll(".mode-field").forEach((el) => {
      const active = el.classList.contains(`mode-${mode}`);
      el.classList.toggle("inactive", !active);
      el.querySelectorAll("input, select").forEach((f) => { f.disabled = !active; });
    });
  });
}

// ----------------------------------------- Usuarios: chips + "+" verde ----

function initUserPicker(root) {
  const chipsEl = root.querySelector(".chips");
  const input = root.querySelector("input");
  const addBtn = root.querySelector(".add-user-btn");
  let values = [];

  function render() {
    chipsEl.innerHTML = values
      .map((v, i) => `<span class="chip">${v}<button type="button" class="chip-remove" data-i="${i}">&times;</button></span>`)
      .join("");
    chipsEl.querySelectorAll(".chip-remove").forEach((btn) => {
      btn.addEventListener("click", () => {
        values.splice(Number(btn.dataset.i), 1);
        render();
      });
    });
  }

  function addCurrent() {
    const v = input.value.trim();
    if (!v || values.includes(v)) {
      input.value = "";
      return;
    }
    values.push(v);
    input.value = "";
    render();
    input.focus();
  }

  addBtn.addEventListener("click", addCurrent);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addCurrent();
    }
  });

  root._picker = {
    getValues: () => values.slice(),
    setValues: (arr) => {
      values = (arr || []).slice();
      render();
    },
  };
  render();
}

document.querySelectorAll(".user-picker").forEach(initUserPicker);

function picker(form, field) {
  return form.querySelector(`.user-picker[data-field="${field}"]`)._picker;
}

// ------------------------------------- Dificultad: estrellas min/max ------

function initDifficultyRange(root) {
  const minPicker = root.querySelector('.star-picker[data-field="difficulty_min"]');
  const maxPicker = root.querySelector('.star-picker[data-field="difficulty_max"]');
  let minValue = 1;
  let maxValue = 5;

  function paint(picker, value) {
    picker.querySelectorAll(".star").forEach((s) => {
      s.classList.toggle("filled", Number(s.dataset.v) <= value);
    });
  }

  function wireHover(picker) {
    const stars = [...picker.querySelectorAll(".star")];
    stars.forEach((s) => {
      s.addEventListener("mouseenter", () => {
        const v = Number(s.dataset.v);
        stars.forEach((s2) => s2.classList.toggle("hover", Number(s2.dataset.v) <= v));
      });
    });
    picker.addEventListener("mouseleave", () => {
      stars.forEach((s2) => s2.classList.remove("hover"));
    });
  }

  function setMin(v) {
    minValue = v;
    if (maxValue < minValue) maxValue = minValue;
    paint(minPicker, minValue);
    paint(maxPicker, maxValue);
  }

  function setMax(v) {
    maxValue = v;
    if (minValue > maxValue) minValue = maxValue;
    paint(minPicker, minValue);
    paint(maxPicker, maxValue);
  }

  minPicker.querySelectorAll(".star").forEach((s) => {
    s.addEventListener("click", () => setMin(Number(s.dataset.v)));
  });
  maxPicker.querySelectorAll(".star").forEach((s) => {
    s.addEventListener("click", () => setMax(Number(s.dataset.v)));
  });
  wireHover(minPicker);
  wireHover(maxPicker);
  paint(minPicker, minValue);
  paint(maxPicker, maxValue);

  root._range = {
    getMin: () => minValue,
    getMax: () => maxValue,
    setRange: (min, max) => {
      minValue = min == null ? 1 : Number(min);
      maxValue = max == null ? 5 : Number(max);
      if (minValue > maxValue) maxValue = minValue;
      paint(minPicker, minValue);
      paint(maxPicker, maxValue);
    },
  };
}

document.querySelectorAll(".difficulty-range").forEach(initDifficultyRange);

function difficultyRange(form) {
  return form.querySelector(".difficulty-range")._range;
}

// --------------------------------------------------- Autocompletado -------

async function loadKnownUsers(platform, datalistId) {
  try {
    const res = await fetch(`/api/known-users?platform=${encodeURIComponent(platform)}`);
    if (!res.ok) return;
    const handles = await res.json();
    const dl = document.getElementById(datalistId);
    dl.innerHTML = handles.map((h) => `<option value="${h}">`).join("");
  } catch (e) {
    // sin Mongo configurada esto puede fallar en silencio, no es crítico
  }
}

function refreshAllKnownUsers() {
  loadKnownUsers("codeforces", "dl-cf-users");
  loadKnownUsers("codeforces", "dl-gym-users");
  loadKnownUsers("atcoder", "dl-ac-users");
  loadKnownUsers("vjudge", "dl-vj-users");
}
refreshAllKnownUsers();

// --------------------------------------------------- Correr un flujo ------

function saveToggleState(form) {
  const toggle = form.querySelector(".save-list-toggle");
  const titleInput = form.querySelector('[name="title"]');
  return { save: toggle.checked, title: titleInput.value.trim() };
}

function buildPayload(flow, form) {
  const fd = new FormData(form);
  const { save, title } = saveToggleState(form);
  if (flow === "codeforces") {
    const mode = cfMode();
    const byMode = mode === "letters"
      ? { letters: splitCsv(fd.get("letters") || ""), round_type: fd.get("round_type") || "div2" }
      : { difficulties: splitCsv(fd.get("difficulties") || "") };
    return {
      users: picker(form, "users").getValues(),
      users_vjudge: picker(form, "users_vjudge").getValues(),
      mode,
      ...byMode,
      save,
      title,
    };
  }
  if (flow === "atcoder") {
    return {
      users_atcoder: picker(form, "users_atcoder").getValues(),
      users_vjudge: picker(form, "users_vjudge").getValues(),
      count: Number(fd.get("count") || 5),
      lookback: Number(fd.get("lookback") || 50),
      problems: splitCsv(fd.get("problems") || ""),
      save,
      title,
    };
  }
  // gym
  const range = difficultyRange(form);
  const filters = {
    difficulty_min: range.getMin(),
    difficulty_max: range.getMax(),
  };
  return {
    users: picker(form, "users").getValues(),
    users_vjudge: picker(form, "users_vjudge").getValues(),
    count: Number(fd.get("count") || 10),
    require_editorial: fd.get("require_editorial") === "on",
    filters,
    save,
    title,
  };
}

function applyParams(form, flow, p) {
  if (!p) return;
  if (flow === "codeforces") {
    picker(form, "users").setValues(p.users);
    picker(form, "users_vjudge").setValues(p.users_vjudge);
    cfModeToggle.checked = p.mode === "letters";
    cfModeToggle.dispatchEvent(new Event("change"));
    form.querySelector('[name="difficulties"]').value = (p.difficulties || []).join(", ");
    form.querySelector('[name="letters"]').value = (p.letters || []).join(", ");
    form.querySelector('[name="round_type"]').value = p.round_type || "div2";
  } else if (flow === "atcoder") {
    picker(form, "users_atcoder").setValues(p.users_atcoder);
    picker(form, "users_vjudge").setValues(p.users_vjudge);
    form.querySelector('[name="count"]').value = p.count ?? 5;
    form.querySelector('[name="lookback"]').value = p.lookback ?? 50;
    form.querySelector('[name="problems"]').value = (p.problems || []).join(", ");
  } else {
    picker(form, "users").setValues(p.users);
    picker(form, "users_vjudge").setValues(p.users_vjudge);
    form.querySelector('[name="count"]').value = p.count ?? 10;
    form.querySelector('[name="require_editorial"]').checked = !!p.require_editorial;
    const f = p.filters || {};
    difficultyRange(form).setRange(f.difficulty_min, f.difficulty_max);
  }
}

// --------------------------------------------- Configuraciones guardadas --

async function refreshConfigSelect(form, flow) {
  const select = form.querySelector(".config-select");
  try {
    const res = await fetch(`/api/configs/${flow}`);
    const configs = res.ok ? await res.json() : [];
    select.innerHTML =
      '<option value="">— Cargar configuración guardada —</option>' +
      configs.map((c) => `<option value="${c._id}">${c.name}</option>`).join("");
  } catch (e) {
    // sin Mongo esto puede fallar en silencio, no es crítico
  }
}

async function loadLastConfig(form, flow) {
  try {
    const res = await fetch(`/api/configs/${flow}/last`);
    if (!res.ok) return;
    const { params } = await res.json();
    applyParams(form, flow, params);
  } catch (e) {
    // sin Mongo no hay último config guardado, no es crítico
  }
}

document.querySelectorAll(".run-form").forEach((form) => {
  const flow = form.dataset.flow;
  const log = form.closest("section").querySelector(".log");
  const results = form.closest("section").querySelector(".results");
  const runBtn = form.querySelector(".run-btn");
  const stopBtn = form.querySelector(".stop-btn");
  let currentRunId = null;
  let currentSource = null;

  const saveToggle = form.querySelector(".save-list-toggle");
  const titleInput = form.querySelector('[name="title"]');
  saveToggle.addEventListener("change", () => {
    titleInput.disabled = !saveToggle.checked;
    if (saveToggle.checked) titleInput.focus();
  });

  refreshConfigSelect(form, flow);
  loadLastConfig(form, flow);

  form.querySelector(".load-config-btn").addEventListener("click", async () => {
    const id = form.querySelector(".config-select").value;
    if (!id) return;
    const res = await fetch(`/api/configs/${flow}/${id}`);
    if (!res.ok) return;
    const cfg = await res.json();
    applyParams(form, flow, cfg.params);
    saveToggle.checked = true;
    titleInput.disabled = false;
    titleInput.value = cfg.name;
  });

  form.querySelector(".delete-config-btn").addEventListener("click", async () => {
    const id = form.querySelector(".config-select").value;
    if (!id) return;
    if (!confirm("¿Borrar esta configuración guardada?")) return;
    await fetch(`/api/configs/${flow}/${id}`, { method: "DELETE" });
    refreshConfigSelect(form, flow);
  });

  form.querySelector(".save-config-btn").addEventListener("click", async () => {
    const name = prompt("Nombre para esta configuración:");
    if (!name) return;
    await fetch(`/api/configs/${flow}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, params: buildPayload(flow, form) }),
    });
    refreshConfigSelect(form, flow);
  });

  function appendLog(msg) {
    log.textContent += msg + "\n";
    log.scrollTop = log.scrollHeight;
  }

  function setRunning(isRunning) {
    runBtn.disabled = isRunning;
    stopBtn.disabled = !isRunning;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (saveToggle.checked && !titleInput.value.trim()) {
      alert("Poné un título para guardar la lista.");
      titleInput.focus();
      return;
    }
    log.textContent = "";
    results.innerHTML = "";
    setRunning(true);

    let res;
    try {
      res = await fetch(`/api/run/${flow}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildPayload(flow, form)),
      });
    } catch (err) {
      appendLog(`Error de red: ${err}`);
      setRunning(false);
      return;
    }
    if (!res.ok) {
      appendLog(`Error al iniciar: HTTP ${res.status}`);
      setRunning(false);
      return;
    }
    const { run_id } = await res.json();
    currentRunId = run_id;

    const source = new EventSource(`/api/run/${run_id}/stream`);
    currentSource = source;
    source.onmessage = (ev) => appendLog(JSON.parse(ev.data));
    source.addEventListener("done", (ev) => {
      const payload = JSON.parse(ev.data);
      if (payload.status === "ok") {
        appendLog("=== Listo ===");
        renderResults(results, flow, payload.result && payload.result.items);
        const listId = payload.result && payload.result.list_id;
        if (listId) {
          const status = document.createElement("span");
          status.className = "share-status";
          const bar = document.createElement("div");
          bar.className = "share-bar";
          bar.append("Lista guardada ", shareButton(listId, (msg) => { status.textContent = msg; }), status);
          results.prepend(bar);
        }
        refreshAllKnownUsers();
      } else if (payload.status === "stopped") {
        appendLog("=== Detenido por el usuario — no se generó ningún archivo ===");
      } else {
        appendLog(`=== Error: ${payload.error} ===`);
      }
      source.close();
      setRunning(false);
    });
    source.onerror = () => {
      appendLog("(conexión de progreso cortada)");
      source.close();
      setRunning(false);
    };
  });

  stopBtn.addEventListener("click", async () => {
    if (!currentRunId) return;
    await fetch(`/api/run/${currentRunId}/stop`, { method: "POST" });
    appendLog("=== Deteniendo (puede tardar unos segundos en frenar) ===");
  });
});

// --------------------------------------------------- Listas guardadas -----

async function loadSavedLists() {
  const flow = document.getElementById("saved-flow-filter").value;
  const container = document.getElementById("saved-list");
  container.innerHTML = "Cargando...";
  const url = flow ? `/api/lists?flow=${encodeURIComponent(flow)}` : "/api/lists";
  const res = await fetch(url);
  if (!res.ok) {
    container.innerHTML = "<p>No se pudo cargar (¿Mongo configurado?).</p>";
    return;
  }
  const lists = await res.json();
  if (lists.length === 0) {
    container.innerHTML = "<p>Todavía no hay listas guardadas.</p>";
    return;
  }
  container.innerHTML = "";
  for (const item of lists) {
    const div = document.createElement("div");
    div.className = "saved-item";
    div.innerHTML = `
      <div class="saved-item-head">
        <input type="text" value="${esc(item.title)}">
        <button class="view-btn">Ver</button>
        <button class="primary refresh-btn">Actualizar</button>
        <button class="danger delete-btn">Borrar</button>
      </div>
      <p class="saved-meta">${esc(item.flow)} · ${esc(fmtDate(item.created_at))} <span class="refresh-status"></span></p>
      <div class="saved-item-body" hidden></div>
    `;
    const titleInput = div.querySelector("input");
    titleInput.addEventListener("change", async () => {
      await fetch(`/api/lists/${item._id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: titleInput.value }),
      });
    });
    div.querySelector(".delete-btn").addEventListener("click", async () => {
      if (!confirm("¿Borrar esta lista guardada?")) return;
      await fetch(`/api/lists/${item._id}`, { method: "DELETE" });
      div.remove();
    });
    const body = div.querySelector(".saved-item-body");
    const refreshBtn = div.querySelector(".refresh-btn");
    const refreshStatus = div.querySelector(".refresh-status");
    refreshBtn.after(shareButton(item._id, (msg) => { refreshStatus.textContent = `· ${msg}`; }));
    // Vuelve a chequear la lista contra sus propios usuarios y pinta de verde lo ya tocado.
    refreshBtn.addEventListener("click", async () => {
      refreshBtn.disabled = true;
      refreshStatus.textContent = "· actualizando...";
      try {
        const res = await fetch(`/api/lists/${item._id}/refresh`, { method: "POST" });
        if (!res.ok) throw new Error(res.status);
        const list = await res.json();
        refreshStatus.textContent = `· ${refreshMessage(list.newly_touched)}`;
        if (!body.hidden) renderResults(body, list.flow, list.items);
      } catch (e) {
        refreshStatus.textContent = "· no se pudo actualizar";
      } finally {
        refreshBtn.disabled = false;
      }
    });
    div.querySelector(".view-btn").addEventListener("click", async () => {
      if (!body.hidden) {
        body.hidden = true;
        return;
      }
      const full = await (await fetch(`/api/lists/${item._id}`)).json();
      renderResults(body, full.flow, full.items);
      body.hidden = false;
    });
    container.appendChild(div);
  }
}

document.getElementById("saved-flow-filter").addEventListener("change", loadSavedLists);

// Restaurar la última pestaña (al final, cuando ya está todo cableado).
try {
  const lastTab = localStorage.getItem(LAST_TAB_KEY);
  const lastBtn = lastTab && document.querySelector(`.tab-btn[data-tab="${lastTab}"]`);
  if (lastBtn) lastBtn.click();
} catch (e) {}
