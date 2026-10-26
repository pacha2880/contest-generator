// app.js — frontend puro (sin framework): tabs, autocompletado, correr un
// flujo + progreso en vivo por SSE, y la pantalla de listas guardadas.

function splitCsv(value) {
  return value.split(",").map((s) => s.trim()).filter(Boolean);
}

// ---------------------------------------------------------------- Tabs ----

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`panel-${btn.dataset.tab}`).classList.add("active");
    if (btn.dataset.tab === "saved") loadSavedLists();
  });
});

// ---------------------------------------------------- Modo CF: rating/letra

const cfModeSelect = document.querySelector('.run-form[data-flow="codeforces"] .mode-select');
if (cfModeSelect) {
  cfModeSelect.addEventListener("change", () => {
    const mode = cfModeSelect.value;
    document.querySelectorAll(".mode-field").forEach((el) => {
      el.hidden = !el.classList.contains(`mode-${mode}`);
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

function buildPayload(flow, form) {
  const fd = new FormData(form);
  if (flow === "codeforces") {
    return {
      users: picker(form, "users").getValues(),
      users_vjudge: picker(form, "users_vjudge").getValues(),
      mode: fd.get("mode"),
      difficulties: splitCsv(fd.get("difficulties") || ""),
      letters: splitCsv(fd.get("letters") || ""),
      round_type: fd.get("round_type") || "div2",
      title: fd.get("title") || "",
    };
  }
  if (flow === "atcoder") {
    return {
      users_atcoder: picker(form, "users_atcoder").getValues(),
      users_vjudge: picker(form, "users_vjudge").getValues(),
      count: Number(fd.get("count") || 5),
      lookback: Number(fd.get("lookback") || 50),
      problems: splitCsv(fd.get("problems") || ""),
      title: fd.get("title") || "",
    };
  }
  // gym
  const filters = {};
  if (fd.get("difficulty_min")) filters.difficulty_min = Number(fd.get("difficulty_min"));
  if (fd.get("difficulty_max")) filters.difficulty_max = Number(fd.get("difficulty_max"));
  return {
    users: picker(form, "users").getValues(),
    users_vjudge: picker(form, "users_vjudge").getValues(),
    count: Number(fd.get("count") || 10),
    require_editorial: fd.get("require_editorial") === "on",
    filters,
    title: fd.get("title") || "",
  };
}

function applyParams(form, flow, p) {
  if (!p) return;
  if (flow === "codeforces") {
    picker(form, "users").setValues(p.users);
    picker(form, "users_vjudge").setValues(p.users_vjudge);
    const modeSelect = form.querySelector('[name="mode"]');
    modeSelect.value = p.mode || "difficulties";
    modeSelect.dispatchEvent(new Event("change"));
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
    form.querySelector('[name="difficulty_min"]').value = f.difficulty_min ?? "";
    form.querySelector('[name="difficulty_max"]').value = f.difficulty_max ?? "";
  }
}

function renderResults(container, flow, items, listId) {
  const data = (items || []).slice();

  function draw() {
    if (data.length === 0) {
      container.innerHTML = "<p>Sin resultados.</p>";
      return;
    }
    const canDelete = !!listId;
    const extraHead = canDelete ? "<th></th>" : "";
    const delCell = (i) =>
      canDelete ? `<td><button type="button" class="danger small-btn resolved-btn" data-i="${i}">Resuelto</button></td>` : "";

    let rows;
    if (flow === "codeforces") {
      rows = data.map((p, i) => `<tr><td>${p.label}</td><td>${p.name}</td><td><a href="${p.url}" target="_blank">${p.url}</a></td>${delCell(i)}</tr>`).join("");
      container.innerHTML = `<table><thead><tr><th>Dificultad/Letra</th><th>Nombre</th><th>Link</th>${extraHead}</tr></thead><tbody>${rows}</tbody></table>`;
    } else if (flow === "atcoder") {
      rows = data.map((c, i) => `<tr><td>${c.id}</td><td>${c.title}</td><td><a href="${c.link}" target="_blank">${c.link}</a></td>${delCell(i)}</tr>`).join("");
      container.innerHTML = `<table><thead><tr><th>Id</th><th>Título</th><th>Link</th>${extraHead}</tr></thead><tbody>${rows}</tbody></table>`;
    } else {
      rows = data.map((g, i) => `<tr><td>${g.id}</td><td>${g.name}</td><td>${g.difficulty}</td><td>${g.editorial}</td><td><a href="${g.link}" target="_blank">${g.link}</a></td>${delCell(i)}</tr>`).join("");
      container.innerHTML = `<table><thead><tr><th>Id</th><th>Nombre</th><th>Dificultad</th><th>Editorial</th><th>Link</th>${extraHead}</tr></thead><tbody>${rows}</tbody></table>`;
    }

    if (canDelete) {
      container.querySelectorAll(".resolved-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const i = Number(btn.dataset.i);
          const res = await fetch(`/api/lists/${listId}/items/${i}`, { method: "DELETE" });
          if (res.ok) {
            data.splice(i, 1);
            draw();
          }
        });
      });
    }
  }

  draw();
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

  refreshConfigSelect(form, flow);
  loadLastConfig(form, flow);

  form.querySelector(".load-config-btn").addEventListener("click", async () => {
    const id = form.querySelector(".config-select").value;
    if (!id) return;
    const res = await fetch(`/api/configs/${flow}/${id}`);
    if (!res.ok) return;
    const cfg = await res.json();
    applyParams(form, flow, cfg.params);
    form.querySelector('[name="title"]').value = cfg.name;
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
        renderResults(results, flow, payload.result && payload.result.items, payload.result && payload.result.list_id);
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
        <input type="text" value="${item.title}" data-id="${item._id}">
        <button class="view-btn">Ver</button>
        <button class="danger delete-btn">Borrar</button>
      </div>
      <p class="saved-meta">${item.flow} · ${new Date(item.created_at).toLocaleString()}</p>
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
    div.querySelector(".view-btn").addEventListener("click", async () => {
      if (!body.hidden) {
        body.hidden = true;
        return;
      }
      const full = await (await fetch(`/api/lists/${item._id}`)).json();
      renderResults(body, full.flow, full.items, full._id);
      body.hidden = false;
    });
    container.appendChild(div);
  }
}

document.getElementById("saved-flow-filter").addEventListener("change", loadSavedLists);
