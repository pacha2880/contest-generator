# Contexto del proyecto para LLM

Última actualización: 2026-10-10.

Este documento resume el estado real del proyecto, las decisiones tomadas y los detalles técnicos necesarios para continuar sin perder contexto.

## Qué hace el proyecto

PachaContests es una herramienta de entrenamiento competitivo para un grupo de programadores bolivianos, con tres flujos iguales en espíritu (API pública → filtrar lo no resuelto por el grupo → mostrar/guardar), cada uno seleccionable desde `main.py`:

1. `app.py` (`py main.py codeforces`): usa la API pública de Codeforces para encontrar problemas que ningún miembro del grupo haya resuelto, filtrados por dificultad y ordenados del más reciente al más antiguo.
2. `atcoder.py` (`py main.py atcoder`): recomienda AtCoder Beginner Contests recientes sin resolver por el grupo (AtCoder nativo + vjudge.net). Ver "Plan de implementación: recomendador AtCoder ABC" más abajo.
3. `gym.py` (`py main.py gym`): recomienda gyms de Codeforces sin resolver por el grupo. Ver "Plan de implementación: recomendador de gyms de Codeforces" más abajo.

Hasta 2026-10-10 `app.py` también subía los problemas a una Google Sheet estructurada en 5 contests (vía `fill_sheet.py`, con `read_sheet.py`/`update_labels.py` como auxiliares). Se eliminó todo eso a pedido del usuario — quería el flujo de Codeforces tan simple como los de AtCoder y gym, sin la complejidad de mantener una Sheet sincronizada. El detalle de cómo funcionaba queda en el historial de git si hace falta reconstruirlo; no se preservó aparte en este documento para no complicarlo de nuevo.

## Estado actual

### Repositorio

La carpeta ya está inicializada como repositorio Git (rama `main`). `.gitignore` excluye:

- `credentials.json`
- `__pycache__/`
- `.env`
- `solved.txt`
- `results.txt`
- `outputs/`

### Verificación local

Los scripts principales compilan correctamente con:

```powershell
py -m py_compile app.py atcoder.py gym.py generate_contest.py main.py
```

En esta máquina el comando `python` no está disponible; se usa `py`.

### Usuarios activos

`config.json["codeforces"]["users"]` tiene actualmente solo 5 handles de prueba (2026-10-10, a pedido del usuario, mismo motivo que `atcoder`/`gym`: corridas rápidas en vez de esperar las ~36 llamadas a `user.status`): `pacha2880`, `PyroxBoy`, `AMAMEMIE`, `Dilan8787`, `__profeta` — los 5 son un subconjunto de la lista completa del grupo que se usó originalmente (36 handles, ver git log si hace falta recuperarla entera).

### Dificultades activas

`config.json["codeforces"]["difficulties"]` tiene actualmente 5 dificultades distintas, una ocurrencia cada una (`1900`, `1700`, `1300`, `900`, `800`), para una tanda de prueba de 5 problemas en vez de 50. La tanda "real" original pedía:

| Dificultad | Cantidad total |
|---|---:|
| 1900 | 10 |
| 1800 | 5 |
| 1700 | 10 |
| 1300 | 10 |
| 900 | 10 |
| 800 | 5 |

No hay dificultades 1200 ni 1600 por decisión del usuario.

### Cache y última generación

- `results.txt` contiene la última tanda principal de problemas.
- `solved.txt` contiene las claves de problemas ya recomendados/cacheados.

## Arquitectura de `app.py`

- Carga `config.json`.
- Llama a `https://codeforces.com/api/user.status` por cada usuario.
- Usa un delay de 0.3 segundos entre requests.
- Llama una sola vez a `https://codeforces.com/api/problemset.problems`.
- Filtra por rating exacto.
- Excluye problemas resueltos por cualquier usuario.
- Excluye problemas ya recomendados en `solved.txt`.
- Ordena por `contestId` descendente para priorizar problemas recientes.
- Guarda claves en `solved.txt`, por ejemplo `2217D`.
- Guarda salida legible en `results.txt`.

## Decisiones de diseño

| Decisión | Razón |
|---|---|
| API de Codeforces en vez de Selenium | Es más rápida, estable y no depende de Chrome. |
| `solved.txt` como cache | Evita repetir sugerencias entre ejecuciones. |
| Repeticiones en `difficulties` | Cada ocurrencia representa un problema pedido de esa dificultad. |
| Sin 1200 ni 1600 | Se eliminaron por decisión del usuario. |
| Sin Google Sheets (2026-10-10) | `fill_sheet.py`, `read_sheet.py`, `update_labels.py` y la función `upload_to_sheets()` de `app.py` se eliminaron a pedido del usuario — quería el flujo de Codeforces tan simple como `atcoder.py`/`gym.py` (fetch → filtrar → mostrar/guardar en archivo), sin la complejidad de mantener credenciales de Google Cloud y una Sheet sincronizada. `config.json` perdió `sheets_url` y `credentials_file`; `requirements.txt` perdió `gspread`/`google-auth`. |
| Config anidada por flujo, `{flujo}.users` (2026-10-10) | `users_codeforces`/`difficulties` (raíz) y `users_gym` (raíz) pasaron a vivir dentro de `config["codeforces"]`/`config["gym"]`, igual que `atcoder` ya hacía con `users_atcoder`/`users_vjudge`. Pedido explícito del usuario: quería que el bloque de Codeforces "se pareciera a los otros". Se agregó además `codeforces.output_links` (default `results.txt`) para que los 3 flujos tengan una ruta de salida configurable, igual que `atcoder.output_links`/`gym.output_csv`. No se agregó un `count` separado para Codeforces porque ya está codificado en las repeticiones de `difficulties` — agregar un campo redundante hubiera sido complicar, no simplificar. |

## Flujo para actualizar usuarios o dificultades

1. Editar `config.json`.
2. Borrar `solved.txt` y `results.txt` si se quiere regenerar desde cero.
3. Ejecutar `py main.py codeforces`.
4. Revisar `results.txt`.

## Gotchas importantes

- Codeforces puede rate-limitear `user.status`; si falla, esperar y reintentar.
- `user.status` usa `count=10000`; si un handle tiene más envíos, puede hacer falta aumentar ese valor.
- En Windows puede haber problemas de encoding en consola; los scripts ya usan configuración UTF-8 para stdout donde aplica.

## Plan de implementación: recomendador AtCoder ABC

Estado: implementado (2026-09-03). Ver `atcoder.py` y `main.py`.

`config.json["atcoder"]["users_atcoder"]`/`["users_vjudge"]` tienen 3-4 handles reales (`AMAMEMIE`/`AMAMEMIE_uwu`, `pypyroxboy`/`PyroxBoy`, `DilanJCM8787`/`DilanJCM8787`+`DJCM8787`; el recorte temporal a solo `DilanJCM8787` del 2026-10-02 ya fue revertido por el usuario). Falta completar el resto del grupo de Codeforces (sin handle de AtCoder todavía).

Decisiones tomadas al implementar:

- `main.py` es un selector mínimo que no refactoriza `app.py`: `py main.py codeforces` simplemente importa y llama a `app.main()`; `py main.py atcoder` llama a `atcoder.main()`.
- La API de AtCoder Problems (`kenkoooo.com`) no pagina por índice sino por `from_second`; `atcoder.py` avanza `from_second` al último `epoch_second` + 1 hasta recibir un batch de menos de 500 resultados.
- Un contest se recomienda solo si **ningún** problema del contest fue resuelto (AC) por **ningún** usuario configurado (contest "intacto"), igual que especifica el algoritmo original.
- Probado end-to-end contra las APIs reales: con `lookback=50` y `count=5` devolvió abc473–abc469 (los 5 ABC más recientes al no haber overlap con el único usuario de prueba).

### Integración con vjudge.net (2026-09-14)

vjudge.net deja resolver problemas de AtCoder a través de su propio mirror, y esas submissions no aparecen en la API de AtCoder Problems (`kenkoooo.com`) — solo las hechas directo en `atcoder.jp`. Eso significaba que el recomendador podía sugerir un contest que alguien ya había resuelto, solo que vía vjudge.

Investigación: vjudge no tiene API pública, pero la propia página `vjudge.net/status#un=<user>&OJId=<oj>&probNum=<prob>` hace un fetch a un endpoint interno no documentado que sí es directamente usable:

```
GET https://vjudge.net/status/data?draw=1&start=0&length=100&un=<vjudge_handle>&OJId=AtCoder
```

Confirmado con requests reales (2026-09-14): funciona sin problema con la librería `requests` de Python (a diferencia de las páginas HTML de gym de Codeforces, acá no hay bloqueo de Cloudflare por fingerprint). Sin `probNum` en los parámetros devuelve **todas** las submissions de ese usuario en ese juez, paginadas por `start`/`length` (no por `draw`). Cada fila trae `probNum` (para AtCoder, ya viene en el mismo formato que `problem_id` de kenkoooo, ej. `"abc415_b"` — no hace falta traducir) y `status` (string literal, ej. `"Accepted"`). `recordsTotal`/`recordsFiltered` son valores sentinel (`9999999`) y no sirven para paginar; hay que cortar cuando una página devuelve menos filas que `length`. Un handle inexistente devuelve `{"data": [], ...}` sin error.

Decisiones:

- Primer intento (2026-09-14): `config.json["atcoder"]["users"]` pasó de lista plana de handles a lista de pares `{"atcoder": handle, "vjudge": handle_o_null}`. Se abandonó este diseño (2026-10-02) porque el usuario quiso editar la lista a mano y agregó una entrada `{"vjudge": "DJCM8787"}` sin `"atcoder"`, lo cual rompía `main.py` con `KeyError: 'atcoder'` — el acoplamiento forzaba que toda entrada tuviera ambas claves aunque no hiciera falta.
- Rediseño (2026-10-02): `config.json["atcoder"]["users_atcoder"]` y `["users_vjudge"]`, dos listas planas e independientes, sin requerir mismo tamaño ni correspondencia 1:1 entre ellas. El algoritmo nunca necesitó la asociación persona↔handle de todos modos: solo le interesa la unión de "resueltos en AtCoder nativo" (`users_atcoder`, vía `fetch_user_ac`) con "resueltos en AtCoder vía vjudge" (`users_vjudge`, vía `fetch_user_vjudge_ac`) — separar las listas es tanto más simple como más flexible (alguien puede aparecer en una sola lista, en ambas, o ninguna).
- `fetch_group_solved(users_atcoder, users_vjudge)` en `atcoder.py` itera cada lista por separado y une los sets resultantes.
- Probado end-to-end (2026-09-14, con el diseño de pares, 4 personas reales): el total de problemas únicos resueltos por el grupo subió de lo que daba antes (solo AtCoder nativo) a 648 al sumar vjudge (ej. `pacha2880` sumó 144 AC extra vía vjudge que no estaban en su cuenta nativa de AtCoder), confirmando que la integración captura submissions reales que antes se perdían. Vuelto a probar (2026-10-02, con el diseño de dos listas y el recorte manual del usuario a solo `DilanJCM8787`/`DilanJCM8787`+`DJCM8787`): corrió sin el `KeyError`, sumó 322 problemas únicos entre AtCoder nativo (227 AC) y las dos cuentas de vjudge (42 + 91 AC).

### Filtro por problema específico (2026-10-10)

`config.json["atcoder"]["problems"]` (lista de letras, ej. `["c", "d", "e"]`, default `[]`) achica el chequeo de "contest intacto" a solo esos problemas en vez del contest completo — pedido explícito del usuario para no descartar un contest por tener A/B resueltos cuando lo que importa es practicar problemas de cierta dificultad (C/D/E).

- `find_recommended_abc()` recibe `problem_letters` opcional. Si está vacío, se comporta exactamente igual que antes (chequea todos los problemas del contest). Si no, por cada contest candidato arma `f"{contest_id}_{letter}"` y verifica que ese id exista en el mapa de problemas de kenkoooo antes de usarlo.
- Letra que no existe para un contest puntual: se imprime una nota (`Nota: {contest_id} no tiene problema '{LETRA}', se omite para este contest`) y se sigue solo con las letras que sí existen ahí — no es un error, cada contest se evalúa con las letras que tenga disponibles.
- Si **ninguna** de las letras pedidas existe en un contest, se saltea el contest entero (no tiene sentido recomendarlo para practicar problemas que no tiene).
- Caso real encontrado al investigar antes de implementar: los ABC viejos (hasta ~abc085) usan sufijos numéricos (`abc001_1`, no `abc001_a`), y algunos de esa época (ej. `abc086`) tienen su C/D con `problem_id` de ARC (`arc089_a`), no de ABC. No hizo falta ningún caso especial para esto — como el chequeo es por membership en el mapa real de problemas (no por construcción ciega del id), esos casos simplemente caen en "letra no existe, se reporta y se saltea" sin romper nada. Verificado con `problem_letters=["z"]` y `lookback=10000`: reportó "no tiene problema Z" en los ~18 ABC más viejos y no recomendó ninguno (lista vacía), en vez de recomendar contests donde la letra ni se chequeó.
- Cuando `problems` no está vacío, el archivo de salida cambia de `outputs/atcoder_links.txt` a `outputs/atcoder_links_C-D-E.txt` (letras en mayúscula, unidas con `-`, insertadas antes de la extensión) — pedido explícito del usuario para distinguir qué filtro se usó en cada corrida.
- Probado end-to-end: con `problems: []` el resultado fue idéntico a antes del cambio (20/20, mismos contests). Con `problems: ["c", "d", "e"]` recomendó más contests que antes (lógico: es una condición más débil que "contest completo intacto") y guardó en `outputs/atcoder_links_C-D-E.txt`.

Objetivo original: agregar un módulo simple para recomendar AtCoder Beginner Contests recientes en los que ninguno de los usuarios configurados haya resuelto ningún problema.

Alcance inicial:

- Solo AtCoder Beginner Contests (`abc###`).
- Sin CSV, sin Excel y sin Google Sheets.
- Salida directa en terminal.
- Archivo simple con links en `outputs/atcoder_links.txt`.
- Configuración desde `config.json`.
- Entrada principal con `main.py`, que pueda llamar a Codeforces o AtCoder.

Configuración propuesta:

```json
{
  "atcoder": {
    "users_atcoder": ["handle1", "handle2"],
    "users_vjudge": ["handle1_vj", "handle3_vj"],
    "count": 5,
    "lookback": 50,
    "output_links": "outputs/atcoder_links.txt"
  }
}
```

(Forma original del plan, era una lista plana de handles. Pasó a pares atcoder/vjudge el 2026-09-14 y de ahí a dos listas independientes el 2026-10-02 — ver sección de integración con vjudge más arriba.)

Fuentes de datos:

- Contests: `https://kenkoooo.com/atcoder/resources/contests.json`
- Problemas por contest: `https://kenkoooo.com/atcoder/resources/contest-problem.json`
- Submissions por usuario: `https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={user}&from_second={from_second}`

Algoritmo:

1. Leer `config.json`.
2. Obtener usuarios AtCoder desde `config["atcoder"]["users"]`.
3. Descargar lista de contests.
4. Filtrar contests cuyo id cumpla `abc\d+`.
5. Ordenar por número descendente para priorizar los ABC más recientes.
6. Tomar los primeros `lookback`.
7. Descargar mapa de problemas por contest.
8. Descargar submissions AC de cada usuario.
9. Armar un set global de problemas resueltos por el grupo.
10. Recomendar contests donde ningún problema del contest esté en ese set.
11. Tomar los primeros `count`.
12. Imprimir links en terminal.
13. Guardar los mismos links en `outputs/atcoder_links.txt`.

Archivos creados/modificados (completado):

- ✅ `atcoder.py`: lógica de descarga, filtrado y recomendación.
- ✅ `main.py`: selector simple entre `codeforces` y `atcoder`.
- ✅ `config.json`: bloque `atcoder` agregado (con handle de prueba pendiente de completar).
- ✅ `README.md`: uso básico de AtCoder documentado (sección "3. Recomendar AtCoder Beginner Contests").
- ✅ `CONTEXT.md`: este archivo, actualizado.

Comandos esperados:

```powershell
py main.py atcoder
py main.py codeforces
```

Verificación:

```powershell
py -m py_compile main.py atcoder.py app.py
py main.py atcoder
```

## Plan de implementación: recomendador de gyms de Codeforces

Estado: implementado (2026-09-14). Ver `gym.py` y `main.py`.

Objetivo: agregar un módulo que recomiende gyms de Codeforces recientes donde ningún usuario del grupo haya resuelto ni intentado ningún problema, con filtros equivalentes a los del "Training filter" de la web de CF (season, contest type, contest format, ICPC region, duration, difficulty).

### Investigación hecha antes de escribir el plan

- `GET https://codeforces.com/api/contest.list?gym=true` (sin auth) devuelve los **2630 gyms existentes**, cada uno con `id`, `name`, `type` (ICPC/IOI), `kind` (Official ICPC Contest, Training Contest, Official School Contest, School/University/City/Region Championship, Official International Personal Contest, Training Camp Contest, Opencup Contest), `icpcRegion` (solo 410/2630 lo tienen), `difficulty` (1-5), `season`, `durationSeconds`, `startTimeSeconds` (no todos lo tienen). Estos campos cubren **todos** los filtros de la UI sin scrapear HTML.
- `contest.standings` para un gym **requiere autenticación** (`apiKey`/`apiSecret`) — probado, falla con "You have to be authenticated". Por eso NO se usa para saber los problemas del gym.
- No hace falta de todas formas: `user.status(handle)` (sin auth, mismo endpoint que ya usa `app.py`) **incluye los envíos a gyms** dentro del historial normal — cada submission trae `contestId`, y los IDs de gym están todos en el rango `100001–106707` (no se pisan nunca con contests normales, que van hasta ~3000). Confirmado con la cuenta `pacha2880`: de 7621 envíos, 2508 eran de gyms. Con eso alcanza para saber si un usuario "tocó" un gym (cualquier verdict, no solo AC) sin necesitar la lista de problemas del gym ni auth.
- La página `codeforces.com/gym/{id}` es HTML renderizado en servidor; el bloque "Contest materials" (Statements/Tutorial/Editorial) ya viene en el HTML inicial, sin login ni JS. **Cuidado con Cloudflare**: pegar muchos requests seguidos sin mantener cookies de sesión dispara un challenge ("Just a moment...") en vez de la página real (pasó con 8 requests seguidos a 0.3s de delay). Solución: reusar cookies entre requests + ~0.8-1s de delay.

Dos bugs encontrados y corregidos durante la implementación (2026-09-14), documentados porque no son obvios:

- **`requests` de Python queda bloqueado por Cloudflare (403), `curl` no.** Se probó en paralelo contra la misma URL: `requests.Session().get(...)` devolvía 403 "Just a moment..." aun con cookies y delay, mientras `curl` con los mismos parámetros devolvía 200 con el HTML real. Es un bloqueo por fingerprint TLS/HTTP, no por rate limit ni User-Agent. Por eso `has_editorial()` en `gym.py` shellea a `curl` vía `subprocess` en vez de usar `requests` (que sí se usa sin problema para las llamadas a la API de Codeforces — este bloqueo es específico de las páginas HTML del gym, protegidas por Cloudflare de forma distinta a la API).
- **Toda página de gym tiene `Codeforces.setupTutorials("/data/problemTutorial")` en un `<script>` cerca del principio del HTML** — es un setup genérico para el popup de tutorial por problema resuelto, no tiene nada que ver con el sidebar "Contest materials". Buscar `tutorial|editorial` contra el HTML completo da falso positivo en el 100% de los gyms. Hay que acotar la búsqueda al bloque del sidebar, delimitado por el texto "Contest materials" y el siguiente "second-level-menu" (la barra de tabs Problems/Submit/Standings que siempre sigue al sidebar). Ver `MATERIALS_RE` en `gym.py`.
- Efecto colateral de estos dos bugs: si el fetch de una página puntual queda bloqueado por Cloudflare, `has_editorial()` devuelve `None` (no `False`), y el output distingue "no tutorial/editorial" (verificado, no tiene) de "couldn't check (page fetch blocked)" (no se pudo verificar) — para no reportar falsos negativos como si fueran datos confirmados.

### Decisiones de diseño

- `main.py` gana un tercer modo: `py main.py gym`, mismo patrón que `atcoder.py` — no toca `app.py`.
- Usa `config.json["gym"]["users"]`, una lista separada de `codeforces.users` (2026-09-14, a pedido del usuario; anidada dentro de `gym` recién el 2026-10-10 — antes vivía como `users_gym` al nivel raíz, movida para que todos los flujos sigan el mismo patrón de `{flujo}.users`) — por defecto tiene unos pocos handles de prueba, no los 36 del grupo completo. Permite probar el módulo sin las ~36 llamadas a `user.status` que tardan minutos, y sin acoplar el flujo de gyms al de Codeforces.
- "Hide, if participated" de la UI de CF **no se replica aparte**: nuestro paso de exclusión (gym tocado por cualquier usuario del grupo, no solo la cuenta logueada) ya es una versión más fuerte de ese filtro.
- "Hide excluded gyms" (lista de exclusión manual guardada en la cuenta de CF) se descarta — no es información pública vía API y el usuario confirmó que no importa para este caso de uso.
- Chequeo de tutorial/editorial va **al final** por defecto, no como filtro de selección: primero se arma la lista final de recomendados (post-filtro de metadata, post-exclusión por grupo, ordenados por más recientes, top `count`), y recién sobre esa lista corta se scrapea cada página. Solo informa, no descarta gyms.
- `require_editorial: true` (agregado 2026-09-14) cambia ese orden: en vez de chequear editorial solo sobre el top `count`, camina la lista completa de candidatos (de más reciente a más antiguo) chequeando editorial uno por uno y quedándose solo con los que sí tienen, hasta juntar `count` o agotar candidatos. Si un gym no tiene editorial o el fetch queda bloqueado, se salta (no cuenta como hallazgo) y sigue con el siguiente — nunca rellena con gyms sin editorial confirmado. Probado con los 4 handles de prueba y `difficulty_max: 3`: encontró 8/10 (se agotaron los candidatos con editorial entre los no tocados por ese grupo de prueba), mostrando el conteo real en vez de fingir 10/10.
- Al mostrar cada gym recomendado en terminal: id, nombre, estrellas de dificultad, link, y si se encontró tutorial/editorial o no.
- `duration_min_seconds`/`duration_max_seconds` por defecto en `18000` (5 horas), matcheando el filtro por defecto que se ve en la UI de CF ("Duration: from 5 to 5").
- `count` por defecto `10` (no 5 como AtCoder).

### Configuración propuesta

```json
{
  "gym": {
    "count": 10,
    "require_editorial": false,
    "filters": {
      "type": "ICPC",
      "kind": ["Official ICPC Contest"],
      "icpc_region": null,
      "difficulty_min": 3,
      "difficulty_max": 4,
      "duration_min_seconds": 18000,
      "duration_max_seconds": 18000,
      "season_from": null,
      "season_to": null
    },
    "output_csv": "outputs/gym_recommendations.csv"
  }
}
```

### Algoritmo

1. Leer `config.json`: usuarios (`config["gym"]["users"]`), filtros de `config["gym"]["filters"]`, `count`, `output_csv`.
2. Descargar `contest.list?gym=true` (una sola vez, 2630 gyms).
3. Filtrar candidatos por metadata: `type`, `kind`, `icpc_region`, `difficulty_min/max`, `duration_min/max`, `season_from/to`.
4. Para cada usuario del grupo, `user.status(handle, count=10000)` y quedarse con el set de `contestId` dentro del rango de IDs de gym (cualquier verdict). Unir en un set global `touched_gyms`.
5. Excluir de los candidatos filtrados cualquier gym cuyo `id` esté en `touched_gyms`.
6. Ordenar los restantes por `startTimeSeconds` descendente (los que no lo tienen, al final) — más recientes primero.
7. Sin `require_editorial`: tomar los primeros `count` → lista final de recomendados; con `require_editorial`: caminar la lista completa de candidatos chequeando editorial en cada uno hasta juntar `count` con editorial confirmado (ver `select_recommendations()`).
8. El chequeo de editorial scrapea `codeforces.com/gym/{id}` con `curl` (no `requests`, ver bugs arriba) reutilizando una cookie jar temporal y ~0.9s de delay entre requests; busca el bloque "Contest materials" acotado por `MATERIALS_RE` y matchea `tutorial|editorial` dentro de ese bloque.
9. Imprimir en terminal cada recomendado: id, nombre, estrellas (`difficulty`), link, y si tiene tutorial/editorial, no tiene, o no se pudo verificar.
10. Guardar en `outputs/gym_recommendations.csv` una fila por gym con columnas `id,name,difficulty,editorial,link` (`editorial` es `yes`/`no`/`unknown (page fetch blocked)`). Cambiado de un archivo de solo links a CSV (2026-09-14) porque el usuario pidió ver también dificultad y estado de editorial en el archivo, no solo en terminal.

### Archivos creados/modificados (completado)

- ✅ `gym.py`: lógica de descarga, filtrado, exclusión por grupo y chequeo de editorial.
- ✅ `main.py`: modo `gym` agregado.
- ✅ `config.json`: bloque `gym` agregado con los valores por defecto del plan.
- ✅ `README.md`: uso documentado (sección "4. Recomendar gyms de Codeforces").
- ✅ `CONTEXT.md`: este archivo, actualizado.

Probado end-to-end (2026-09-14) con los handles `nicolasalba`, `__profeta`, `Simurdiera_MAC`, `Alexander1755`: 447/2630 gyms cumplían los filtros por defecto, ese grupo había tocado 222, y la recomendación final de 10 gyms incluyó una mezcla real de con/sin tutorial (confirmado manualmente contra el HTML, no todo "encontrado" como en el primer intento con los bugs sin corregir). Primero se probó pasando esos handles directo a `find_recommended_gyms()` sin tocar el config; luego, al separar `users_codeforces`/`users_gym` (ambas al nivel raíz en ese momento), se corrió `py main.py gym` real y dio el mismo resultado. Vuelto a probar (2026-10-10) tras mover `users_gym` adentro de `gym.users`: 7 usuarios reales, 453/2654 gyms cumplían filtros, 187 tocados, 20/20 recomendados — sin errores.

Comando esperado:

```powershell
py main.py gym
```

## Plan de implementación: GUI de escritorio (en construcción)

Estado: decidido el approach, esqueleto creado (2026-10-10), wiring real pendiente.

### Contexto de la decisión

El usuario quiere eventualmente 3 interfaces para el mismo backend: consola (ya existe), GUI de escritorio (primera prioridad), y web de acceso libre (después, sin apuro). Se discutió a fondo antes de tocar código:

- **Streamlit** quedó descartado para la GUI de escritorio porque siempre levanta un servidor local (Tornado) aunque sea en `localhost` — y el usuario preguntó específicamente por empaquetar a `.exe` más adelante, donde Streamlit+PyInstaller tiene fricción documentada (assets estáticos del paquete no siempre se detectan). Tkinter/FreeSimpleGUI empaquetan mucho más confiable con PyInstaller al ser stdlib o liviano.
- **FreeSimpleGUI** (fork libre de PySimpleGUI, que pasó a ser de pago) elegido sobre Tkinter puro por menos código de layout, y sobre PyQt/PySide por ser más liviano.
- **Streamlit sigue siendo la recomendación para la versión web** cuando llegue ese momento — ahí sí tiene sentido un servidor, y Streamlit Community Cloud es gratis y se despliega solo desde GitHub. Para esa fase faltará decidir: (a) dashboard fijo del grupo vs (b) herramienta pública multi-tenant (usuarios ingresan sus propios handles), porque cambia bastante el diseño — no decidido todavía. También hay riesgo real de rate-limit compartido si varios visitantes corren flujos a la vez desde la misma IP del servidor.
- **La consola tiene que seguir funcionando siempre**, leyendo/escribiendo el mismo `config.json`. Diseño acordado: la GUI (y después la web) son capas finas que llaman a las mismas funciones reusables (`find_recommended_abc`, `find_untouched_gyms`, etc.), no una reimplementación paralela.

### Inyección de dependencias para el progreso (2026-10-10)

Antes de esto, el progreso de fetch (qué usuario se está consultando, cuántos aceptados, etc.) se imprimía con `print()` directo adentro de las funciones de fetch — imposible de mostrar en vivo en una GUI sin hackear `sys.stdout`. Se cambió a DI explícita, pedido así por el usuario:

- Toda función de fetch/orquestación reusable (`get_user_solved`, `fetch_problemset` en `app.py`; `fetch_contests`, `fetch_contest_problems`, `fetch_user_ac`, `fetch_user_vjudge_ac`, `fetch_group_solved`, `find_recommended_abc` en `atcoder.py`; `fetch_gym_contests`, `fetch_user_touched_gyms`, `find_untouched_gyms` en `gym.py`) ahora pide `on_progress` como parámetro **obligatorio y keyword-only** (`*, on_progress`) — nada de default a `print` escondido adentro de la función. Quien llama decide la implementación.
- `main()` de cada módulo (el punto de entrada de consola) es quien inyecta `on_progress=print` — es literalmente la única parte del código que sabe que está corriendo en una terminal. Cuando la GUI llame a estas mismas funciones directo (no a través de `main()`), va a inyectar su propio callback (ej. uno que escriba en el `Multiline` del log) en vez de `print`.
- Cada mensaje de progreso ahora es una llamada completa a `on_progress(mensaje)` en vez del patrón anterior de `print(..., end="", flush=True)` + un segundo `print()` que completaba la misma línea — se perdió el efecto "aparece antes de terminar la request" en consola, pero a cambio cada call es un mensaje autocontenido, que es lo que necesita cualquier widget de log (una línea nueva por evento, no fragmentos a pegar).
- `check_editorials`/`select_recommendations`/`has_editorial` en `gym.py` no se tocaron — no tenían ningún `print()` propio que convertir (el único progreso de esa etapa ya vivía en el `=== Checking contest materials ===` de `main()`, que queda como print directo de consola).
- Probado end-to-end después del cambio: los 3 flujos corrieron limpio (`py main.py codeforces/atcoder/gym`) con el mismo comportamiento visible, solo con el formato de línea ligeramente distinto.

### `input()` reemplazado por error explícito (2026-10-10)

`app.py` pedía usuarios/dificultades por `input()` de consola si `config.json` los tenía vacíos. Eso colgaría una GUI esperando un input que nunca llega, sin ningún mensaje de error visible. Se reemplazó por `raise ValueError(...)` en los 3 módulos (antes `atcoder.py`/`gym.py` solo imprimían un mensaje y hacían `return` silencioso, que tiene el mismo problema de fondo — fallar en silencio en vez de fuerte): si falta `codeforces.users`/`difficulties`, `atcoder.users_atcoder`/`users_vjudge`, o `gym.users`, ahora cada módulo levanta `ValueError` con un mensaje que dice exactamente qué clave de `config.json` falta. Una futura capa de GUI puede capturar `ValueError` de forma uniforme en los 3 flujos y mostrar un messagebox, en vez de necesitar un manejo especial por módulo.

### `gui.py` (esqueleto 2026-10-10, cableado completo 2026-10-11)

Creado con FreeSimpleGUI (`py -m pip install FreeSimpleGUI`, agregado a `requirements.txt`). Arrancó como solo estructura (pestañas + campos precargados, botones placeholder) y el mismo día se conectó al backend real, resolviendo las 4 pendientes que había dejado anotadas.

**Decisión de persistencia (Opción A, confirmada explícitamente por el usuario 2026-10-11):** "Generar" SIEMPRE escribe los valores del formulario de vuelta a `config.json` antes de correr — no hay modo "ad hoc" sin persistir. La GUI es, literalmente, "un `config.json` dinámico" como se planteó al principio de esta idea: editás en la ventana, apretás el botón, y tanto el archivo como la consola quedan con esos mismos valores después.

**Cómo se resolvieron las 4 pendientes:**

1. **`main()` de los 3 módulos ahora acepta `on_progress=print` opcional** (antes de esto, solo las funciones internas de fetch tenían `on_progress` obligatorio — `main()` seguía hardcodeado a `print` por dentro). Se convirtieron también los `print()` propios de cada `main()` (listado de usuarios, resultados, "Saved N..." etc.) a `on_progress`. Esto es clave: la GUI llama literalmente a `app.main(on_progress=...)`/`atcoder.main(on_progress=...)`/`gym.main(on_progress=...)` — la misma función que usa la consola, sin duplicar lógica ni reimplementar la orquestación en `gui.py`. `main.py` (consola) sigue llamando `app.main()`/`atcoder.main()`/`gym.main()` sin argumentos, así que el comportamiento de consola no cambió en nada.
2. **Progreso thread-safe**: en vez de `queue.Queue` + `window.read(timeout=...)` (lo que había quedado anotado como plan), se usó `window.write_event_value("-PROGRESS-", msg)` — mecanismo propio de PySimpleGUI/FreeSimpleGUI pensado exactamente para esto, más simple que armar el polling a mano. El hilo de trabajo llama `on_progress=lambda msg: window.write_event_value("-PROGRESS-", msg)`; el loop principal de eventos recibe esos `-PROGRESS-` como cualquier otro evento de la ventana y escribe en `-LOG-`.
3. **Persistencia resuelta como Opción A** (ver arriba). Cada `run_codeforces`/`run_atcoder`/`run_gym` en `gui.py`: relee `config.json` fresco del disco (no reusa el `cfg` cargado al abrir la ventana, por si cambió desde afuera), actualiza **solo las claves de su propio bloque** (preserva intactas las otras dos secciones y los filtros de gym que el formulario no expone, ej. `type`/`kind`/`season_from`/`season_to`), guarda, y recién ahí llama al `main()` real. Si algún campo no parsea (ej. "Count" con texto), la excepción se levanta **antes** de `save_config()` — probado explícitamente: un "Count" inválido no modifica `config.json` en absoluto.
4. **Mostrar resultados**: resuelto gratis por el punto 1 — como TODO el `main()` de cada módulo (incluyendo el listado final de problemas/contests/gyms recomendados) pasa por `on_progress`, el log de la GUI termina mostrando exactamente lo mismo que mostraría la consola, sin necesidad de armar una tabla aparte ni tocar las funciones del backend para que devuelvan algo distinto.

**Threading**: cada click en "Generar" dispara un `threading.Thread(target=worker, ...)` — `worker()` llama a `run_codeforces`/`run_atcoder`/`run_gym`, captura cualquier excepción (de parseo o de la corrida real) y la reporta vía `window.write_event_value("-DONE-", (label, status, error))`, con `status` en `"ok"`/`"stopped"`/`"error"`. Los 3 botones "Generar" se deshabilitan mientras cualquiera de los 3 está corriendo (no solo el que se apretó) — simplificación deliberada para que dos flujos no escriban `config.json` al mismo tiempo.

**Nota de formato**: como `save_config()` usa `json.dump(cfg, f, indent=4)`, la primera vez que se guarda desde la GUI el archivo entero queda reformateado (arrays que antes eran una línea pasan a multilínea) aunque el contenido sea equivalente — es inevitable con el módulo `json` estándar, no hay forma de hacer una edición parcial preservando el formato original byte a byte. Confirmado en la práctica: el usuario probó la ventana real (no solo los tests de funciones) y `config.json` quedó reformateado con el mismo contenido tras usar las pestañas Codeforces y AtCoder.

**Probado (2026-10-11)**:
- Validación: `run_atcoder` con `"-AC-COUNT-": "not-a-number"` levantó `ValueError` y `config.json` quedó byte-a-byte idéntico (comparado antes/después).
- Camino feliz (función directa, sin ventana): `run_codeforces` con los valores reales de `config.json` corrió `app.main()` de punta a punta (5 usuarios, fetch real, 6 problemas encontrados, `solved.txt`/`outputs/codeforces_results.txt` escritos) con `on_progress=print` simulando el callback de la GUI.
- **Camino feliz (ventana real)**: el usuario usó `py gui.py` de verdad — confirmado por timestamps de archivo que `outputs/codeforces_results.txt` y `outputs/atcoder_links_F.txt` se generaron recién al apretar "Generar" en esas pestañas, con el mismo formato/ubicación que la consola. Confirma que el flujo completo (guardar config → correr en hilo → escribir archivo) funciona de punta a punta desde la UI real, no solo en los tests de funciones.

### Botones Detener y Limpiar (2026-10-11)

Pedido explícito del usuario después de probar la primera versión cableada. "Detener" necesitaba soporte nuevo en el backend — Python no puede matar un hilo a la fuerza, así que se implementó cancelación cooperativa:

- **`cancel.py`** (nuevo, mínimo): define `StoppedByUser(Exception)`, compartida por los 3 módulos y por `gui.py`. Una sola clase en un módulo chico en vez de duplicarla en cada uno, para que `gui.py` pueda capturarla con un solo `except` sin `isinstance` contra 3 tipos distintos.
- Los loops largos de `app.py`/`atcoder.py`/`gym.py` aceptan un `should_stop` opcional (default `lambda: False`, así ningún llamador existente — consola incluida — se ve afectado) y lo chequean **entre items**, no dentro de las sub-paginaciones de cada fetch individual: el checkpoint vive en `get_user_solved` (app.py), en `fetch_group_solved` y en el loop de contests de `find_recommended_abc` (atcoder.py), y en `find_untouched_gyms` y en `check_editorials`/`select_recommendations` (gym.py, el loop más lento por el delay de 0.9s de `curl` por gym). Si `should_stop()` da `True`: se llama `on_progress("Detenido por el usuario.")` y se levanta `StoppedByUser` — se propaga sola hasta `main()` sin necesitar manejo especial en cada nivel intermedio.
- Como todos los checkpoints caen **antes** del paso final de escritura de archivo en los 3 `main()`, detener una corrida nunca deja un archivo de salida a medio escribir — se corta antes de llegar ahí. Verificado explícitamente: `app.main(should_stop=lambda: True)` y `app.main(should_stop=<para después de 1 usuario>)` ambos levantan `StoppedByUser` sin tocar `solved.txt` ni `outputs/codeforces_results.txt`.
- **`gui.py`**: agrega un `threading.Event` (`stop_event`) creado una vez al abrir la ventana, reseteado (`.clear()`) antes de cada corrida nueva. El botón "Detener" llama `stop_event.set()`; `should_stop=stop_event.is_set` se pasa a `run_codeforces`/`run_atcoder`/`run_gym` y de ahí a `app.main()`/`atcoder.main()`/`gym.main()`. `worker()` distingue tres desenlaces (`"ok"`/`"stopped"`/`"error"`) en vez de solo éxito/excepción, para que el log diga explícitamente "detenido por el usuario" en vez de mostrarlo como un error genérico.
- Botón "Limpiar": vacía `-LOG-` (`window["-LOG-"].update("")`), no toca nada del backend ni del estado de `running`.
- `save_config()` ahora agrega un `\n` final después del `json.dump` (detalle menor, evita el "no newline at end of file" en los diffs de git).

Pendiente real (no bloqueante, para cuando haga falta):

- No hay feedback visual de "corriendo" más allá del log y los botones deshabilitados (sin spinner ni barra de progreso) — suficiente por ahora.
- `gym.py` tiene más filtros en `config.json["gym"]["filters"]` (`type`, `kind`, `icpc_region`, `duration_min_seconds`, `duration_max_seconds`, `season_from`, `season_to`) que no tienen campo en la pestaña — se preservan tal cual están en el archivo (no se pierden), pero no son editables desde la GUI todavía.
- Empaquetado a `.exe` (motivo original de elegir FreeSimpleGUI sobre Streamlit) sigue sin intentarse.

## Modo "letra" para el recomendador de Codeforces (2026-10-16)

Pedido del usuario: poder pedir problemas de Codeforces por **letra de problema** (ej. "la C") en vez de por rating exacto, restringido a rounds Div.2, Div.1+Div.2 combinados, o Educational — el patrón clásico de entrenamiento "practicar todas las C" sin importar el rating puntual.

### Investigación antes de implementar

- `contest.list` **no tiene campo estructurado de división** — ni siquiera `type` sirve (Educational y Div.3 aparecen con `type: "ICPC"`, igual que rounds con nombre propio). Hay que sacarlo del texto libre de `name` con regex.
- Patrones reales confirmados contra la API: `"Codeforces Round N (Div. 2)"`, `"Codeforces Round N (Div. 1 + Div. 2)"` (a veces con nombre de sponsor antes, ej. `"WorldQuant Round 1 (Codeforces Round 1128, Div. 1 + Div. 2)"`), `"Educational Codeforces Round N (Rated for Div. 2)"`. Importante: el texto de Educational y de los combinados **contienen** la substring "Div. 2" sueltos, así que clasificar mal el orden de los checks los metería como "div2" plano por error — por eso `classify_round()` chequea `educational` y `div1+div2` primero, y recién después `div2`/`div1` planos.
- **Rounds espejados** (mismo número, un `contestId` para Div.1 y otro para Div.2) pueden tener **la misma letra apuntando a problemas distintos**, o el mismo problema con **letra distinta según la división**: verificado con un caso real (round 1127) — "Lavencia Oranges" es el problema A en el listado del Div.1 (contest 2273) pero el C en el listado del Div.2 (contest 2274). Buena noticia: `problemset.problems` ya devuelve cada contest por separado con su propia letra correcta — no hace falta remapear nada a mano, solo clasificar el `contestId` de cada entrada.

### Diseño (confirmado con el usuario antes de implementar)

- `config.json["codeforces"]["letters"]`: lista con repeticiones (ej. `["C", "C", "D"]`), análoga a `difficulties` pero pidiendo por letra en vez de por rating. **No se combina con `difficulties`** — es modo alternativo: si `letters` tiene algo, esa corrida usa modo letra e ignora `difficulties` por completo; si está vacía (default), sigue el modo rating de siempre. Decisión explícita del usuario tras preguntarle, porque mi primera lectura (combinar ambos filtros en la misma corrida) no era lo que quería.
- `config.json["codeforces"]["round_types"]`: lista de categorías permitidas cuando `letters` está activo. Default `["div2", "div1+div2", "educational"]` — exactamente lo pedido, pero queda configurable (también acepta `"div1"`, `"div3"`, `"div4"`, `"other"`). **Nota: esto cambió el mismo día** — ver "Revisión: `type` único + `mode` explícito" más abajo, ahora es `type` (valor único) en vez de `round_types` (lista).
- Letra matchea con subletras: `"C"` matchea `"C"`, `"C1"`, `"C2"` (`index.upper().startswith(letter)`) — decisión explícita del usuario, porque los problemas más difíciles de cada letra casi siempre vienen partidos en easy/hard version y un match exacto dejaría afuera la mayoría.

### Implementación en `app.py`

- `classify_round(name)`: clasifica un nombre de contest contra `ROUND_TYPE_PATTERNS` (lista ordenada de `(label, regex)`, primer match gana).
- `fetch_contest_round_types(*, on_progress)`: trae `contest.list` (`gym=False`) una vez y devuelve `{contestId: round_type}` para todos los ~2150 contests regulares.
- `find_unsolved_by_letter(problems, stats, allowed_contest_ids, letter, user_solved, past, count)`: espejo de `find_unsolved()` existente, pero filtra por `contestId in allowed_contest_ids` + `index` empieza con la letra, en vez de por `rating`.
- `main()`: decide el modo (`letter_mode = bool(letters)`) antes de todo. Ambos modos comparten el mismo paso 1 (`get_user_solved`) y paso 2 (`fetch_problemset`) — solo el bloque de selección de candidatos y el paso extra de clasificar contests difieren. El resto (anti-repeat vía `solved.txt`, escritura del archivo de salida, `save_past`) es idéntico en ambos modos, sin duplicar esa parte.
- La GUI (`gui.py`) **no expone `letters`/`round_types` todavía** — mismo gap que los filtros extra de gym: el campo existe y se preserva en `config.json` si ya está seteado (porque `run_codeforces` solo pisa las claves que sí maneja: `users`/`difficulties`/`output_links`), pero no es editable desde la ventana por ahora.

### Probado (2026-10-16)

- `classify_round()` contra 11 nombres reales de contests (incluyendo el caso combinado con sponsor, Educational, Div.1/2/3/4, un round espejado, y dos "other" genéricos) — los 11 clasificaron correctamente.
- Modo rating sin tocar nada (`letters` ausente/vacía): corrida real sin cambios de comportamiento.
- Modo letra real: `letters: ["C", "C", "D"]` con los 5 usuarios reales → 1158/2157 contests matchearon los `round_types` default, encontró 2 C's y 1 D no resueltos, mismo `solved.txt`/archivo de salida de siempre. Probado y revertido sobre una copia de respaldo de `config.json`, no quedó el valor de prueba en el archivo real.

### Revisión: `type` único + `mode` explícito (2026-10-16, mismo día)

El usuario pidió simplificar el diseño inicial después de verlo:

- `round_types` (lista) → **`config.json["codeforces"]["type"]`** (valor único, no lista). `"div1"`, `"div3"`, `"div4"` quedan categorías exclusivas entre sí, pero `"div2"` (default) ahora **engloba** `div1+div2` y `educational` — no se eligen por separado, `"div2"` ya las incluye porque las tres sirven para entrenar a nivel Div.2. Implementado como `ROUND_TYPE_GROUPS = {"div1": {"div1"}, "div2": {"div2", "div1+div2", "educational"}, "div3": {"div3"}, "div4": {"div4"}}` — `classify_round()` sigue devolviendo las 7 etiquetas finas de siempre (incluyendo `div1+div2`/`educational`/`other` por separado), `ROUND_TYPE_GROUPS` es solo el mapeo de qué etiquetas finas cubre cada valor de `type`.
- `letter_mode = bool(letters)` (inferido) → **`config.json["codeforces"]["mode"]`**, enum explícito `"letters"` / `"difficulties"` (default `"difficulties"`, preserva el comportamiento de antes). Ya no se infiere de si `letters` tiene contenido — ahora es el campo `mode` el que manda.
- Ambos campos nuevos (`type`, `mode`) validan su valor y levantan `ValueError` con mensaje claro si no son uno de los permitidos (ej. `mode: "bogus"` → `"...must be 'letters' or 'difficulties', got 'bogus'"`) — mismo patrón "fallar fuerte" que el resto del proyecto. Validado en vivo con `mode` y `type` inválidos, ambos levantaron el error esperado.
- `config.json` real quedó con `"mode": "letters"`, `"type": "div2"`, `"letters": ["c", "C", "D"]` — modo letra activo por decisión explícita del usuario (ya lo había dejado así en el turno anterior).
- Pendiente igual que antes: la GUI no expone `letters`/`type`/`mode` todavía.

## Backend web: `server.py` (2026-10-26)

### Por qué, y las decisiones grandes tomadas antes de escribir código

El usuario quiere publicar esto en la web (no solo consola/GUI de escritorio), con usuarios recordados (autocompletado), listas generadas con título editable y guardadas para volver a verlas, y un login simple. Antes de programar se evaluaron opciones a fondo:

- **¿Sitio 100% estático (sin servidor)?** Se probó CORS contra las 4 fuentes reales que usa el proyecto: la API de Codeforces y la de AtCoder Problems (kenkoooo) **sí** mandan `Access-Control-Allow-Origin: *` (confirmado con y sin header `Origin` explícito) — esas dos se podrían llamar desde JS del navegador sin backend. Pero el endpoint interno de vjudge y las páginas HTML de gym de Codeforces **no** mandan CORS — el navegador bloquea la respuesta si se piden desde otro dominio. Conclusión: no se puede ir 100% estático, porque 2 de los 3 flujos (vjudge dentro de AtCoder, y todo el flujo de gym) necesitan sí o sí un backend real. No vale la pena un híbrido estático+función serverless solo para esos dos, porque de todas formas hace falta un backend con estado para login+Mongo.
- **¿Cambiar de lenguaje para facilitar el deploy?** No — el bloqueo de arriba es política CORS del lado de vjudge/Codeforces, no algo que dependa de en qué lenguaje esté escrita nuestra lógica. Reescribir en JS no destraba nada y tira a la basura meses de lógica ya probada (el bypass de Cloudflare vía `curl`, la clasificación de rondas, etc.). Se decidió quedarse en Python y reusar todo lo ya construido.
- **Framework**: FastAPI (elegido por el usuario) en vez de Streamlit — con los requisitos nuevos (listas guardadas editables, login, autocompletado) la app dejó de ser "un formulario con botón generar" y pasó a ser "una app chica con registros persistentes y CRUD", donde FastAPI + frontend propio da más control que Streamlit.
- **Base de datos**: evaluamos SQL (Postgres vía Neon/Supabase) vs NoSQL vs SQLite-hosteado (Turso). Elegida **MongoDB Atlas** (tier M0 gratis para siempre, 512MB) — decisión del usuario, justificada porque los datos a guardar no tienen relaciones (usuarios conocidos, listas con título) y no vale la pena la ceremonia de esquema/migraciones de Postgres para esto.
- **Hosting**: **Render**, plan free. Como la persistencia vive en Mongo (externa), no importa que el filesystem de Render sea efímero ni que el plan free "duerma" tras 15 min sin uso — el único costo es un cold start de unos segundos en la primera visita después de estar inactivo.
- **Restricción explícita del usuario, repetida varias veces en la conversación**: "el local tiene que seguir funcionando como siempre" y "el backend se comparte" (= la lógica core se comparte entre consola/GUI/web, pero el backend de FastAPI en sí es una pieza nueva y separada). Esto es la base de todo el diseño de abajo.

### Refactor previo necesario: `app.py` no tenía su lógica separada de `config.json`

A diferencia de `atcoder.py` (`find_recommended_abc`) y `gym.py` (`find_untouched_gyms`/`select_recommendations`), que ya eran funciones puras sin tocar `config.json`, toda la lógica de búsqueda de `app.py` vivía mezclada adentro de `main()` junto con la lectura del archivo. Se extrajo a una función nueva **`generate_recommendations(users, mode, *, difficulties=None, letters=None, round_type="div2", on_progress, should_stop=lambda: False, past=None)`** — sin I/O de archivo propio (ni siquiera `solved.txt`; el caller decide qué `past` pasarle), devuelve `(result_lines, newly_recommended_keys, items)` en vez de escribir nada. `main()` quedó como wrapper delgado que lee `config.json`+`solved.txt` y llama a esta función, exactamente el mismo patrón que ya tenían los otros dos módulos. `items` es nuevo: la lista de dicts estructurados (antes solo se guardaban las `keys` para el cache) — hace falta para que el backend web pueda guardar/mostrar resultados como datos, no reparseando las líneas de texto.

Verificado explícitamente que este refactor no cambió nada visible: recompilado y vuelto a correr `py main.py codeforces` dos veces (antes y después de agregar `items` al return) con resultados coherentes con lo esperado.

### Arquitectura de `server.py`

- **No lo importan ni lo usan** `main.py`/`gui.py`, y tampoco al revés — `server.py` nunca toca `config.json`, `solved.txt` ni `outputs/`. Llama directo a `app.generate_recommendations(...)`, `atcoder.find_recommended_abc(...)`, `gym.find_untouched_gyms(...)` + `gym.select_recommendations(...)` con parámetros que vienen del body JSON del request, no de archivos.
- **Un hilo por corrida** (`threading.Thread`, igual que `gui.py`), con una `RunState` en memoria (`RUNS: dict[run_id, RunState]`, protegido por un lock solo al crear/leer la entrada) conteniendo `queue.Queue` para el progreso, `threading.Event` para `should_stop`, y el resultado final. **Solo funciona con un worker de Uvicorn** — si en algún momento se corre con múltiples workers/procesos, `RUNS` dejaría de ser compartido entre ellos y haría falta un store externo (ej. Redis). Para la escala de este proyecto (un grupo chico) un solo worker alcanza de sobra.
- **Progreso en vivo vía Server-Sent Events** (`GET /api/run/{run_id}/stream`, `text/event-stream`) en vez de WebSockets — más simple, un solo sentido (servidor→cliente) alcanza. La ruta es `def` sync a propósito, no `async def`: así FastAPI la corre en un threadpool y el `queue.get()` bloqueante de adentro no traba el event loop del resto del server mientras espera el próximo mensaje.
- **Cancelación**: mismo `cancel.StoppedByUser` que ya usan consola/GUI — `should_stop=state.stop_event.is_set` se pasa directo a las funciones core, sin código nuevo de cancelación, solo reusando lo que ya existía.
- **Auth**: `auth.py`, una sola contraseña compartida (`APP_PASSWORD` env var) en vez de cuentas individuales — decisión explícita del usuario ("super simple"). Sesión en cookie firmada vía `SessionMiddleware` de Starlette (`SECRET_KEY` env var). Sin `APP_PASSWORD` seteada, el gate queda abierto — para poder probar local sin inventar una contraseña. `require_login_page` (rutas de página completa, redirige a `/login`) vs `require_login_api` (rutas de API/SSE, devuelve 401) son dos funciones separadas porque una redirección no tiene sentido para un fetch/EventSource.
- **Mongo**: `db.py`, degrada con gracia si no hay `MONGODB_URI` — todas las funciones devuelven `[]`/`None`/no-op en vez de romper, así se pudo probar todo el resto del server (auth, los 3 flujos, SSE) sin tener un cluster de Mongo real a mano en este entorno. `get_default_database()` necesita `default="problemshunter"` porque el connection string que copia Atlas por default no trae el nombre de la base en la URL. Colecciones: `known_users` (`platform`, `handle`, `last_used`, upsert por corrida), `saved_lists` (`flow`, `title`, `params`, `result_lines`, `items`, `created_at`/`updated_at`, CRUD vía `/api/lists/*`, con título deduplicado por flujo agregando `" (1)"`, `" (2)"`... si ya existe), `last_configs` (un doc por flujo con los parámetros de la última corrida, para precargar el form al abrir la página) y `saved_configs` (configuraciones con nombre guardadas a mano, upsert por `(flow, name)` — guardar de nuevo con el mismo nombre sobreescribe).
- **Frontend**: HTML+JS plano servido por el mismo FastAPI (`templates/` con Jinja2, `static/` para CSS/JS) — sin framework de frontend, consistente con la preferencia de simplicidad de todo el proyecto. `static/app.js` maneja: tabs, autocompletado (datalist poblado desde `/api/known-users`), submit de formulario → `POST /api/run/{flow}` → `EventSource` al stream → render de resultados en tabla, botón Detener → `POST /api/run/{run_id}/stop`, y la pantalla de listas guardadas (listar/renombrar/ver/borrar).
- **Dependencias separadas**: `requirements-web.txt` es un subconjunto de `requirements.txt` sin `FreeSimpleGUI` — esa depende de Tk a nivel de sistema (no solo pip), que puede no estar en el contenedor Linux mínimo que usa Render, y si falla instalarla se cae el build entero del deploy aunque `server.py` nunca la importe. Confirmado que ningún otro módulo importa `FreeSimpleGUI` salvo `gui.py` (`grep` en todo el repo).
- **`render.yaml`**: deploy por Blueprint con un clic. Variables a completar a mano en el dashboard: `APP_PASSWORD`, `MONGODB_URI` (`SECRET_KEY` se autogenera).

### Probado (2026-10-26), todo corriendo local con `uvicorn server:app`, sin Mongo real configurado

- `GET /`, `GET /login`, `GET /api/health` — responden bien; `/api/health` reporta `db: false` correctamente sin `MONGODB_URI`.
- **Corrida real de Codeforces de punta a punta vía HTTP**: `POST /api/run/codeforces` con 2 usuarios reales + rating 1900 → `run_id` → stream SSE con las mismas líneas de progreso que ya mostraba consola/GUI → evento `done` con `status: "ok"` y un ítem estructurado real. Confirmado por timestamp de archivo que esta corrida **no tocó** `solved.txt` ni `outputs/codeforces_results.txt` (quedaron con el timestamp de una corrida de consola anterior en la misma sesión, no de la corrida web).
- **AtCoder vía HTTP**: corrida real con `pacha2880`, encontró 2 ABCs reales no tocados.
- **Gym vía HTTP**: corrida real con `pacha2880`, incluyendo el chequeo de editorial vía `curl` (el bypass de Cloudflare) — funcionó corriendo adentro del proceso de FastAPI, no solo como script suelto.
- `/api/lists` y `/api/known-users` devuelven `[]` limpiamente sin Mongo configurada, sin romper nada.
- **Auth completo**: sin sesión, `GET /` → 303 a `/login` y `GET /api/known-users` → 401. Contraseña incorrecta → 401. Contraseña correcta → 303 + cookie de sesión; con esa cookie, `GET /api/known-users` → 200.

### `.env` para desarrollo local (2026-10-26)

`server.py` carga `python-dotenv` (`load_dotenv()` al importar) para poder leer `APP_PASSWORD`/`SECRET_KEY`/`MONGODB_URI` de un archivo `.env` en la raíz durante desarrollo local. `.env` está en `.gitignore`, nunca se commitea. En Render esto no hace nada (no hay archivo `.env` ahí) — las env vars se setean directo en el dashboard del servicio, que es lo que ya declaraba `render.yaml`.

### UX del formulario web: usuarios con autocompletado, configuraciones guardadas, borrado puntual (2026-10-26)

Pedido del usuario: no le gustaba el campo de usuarios como texto CSV; quería un botón "+" verde que agregue el usuario actual con autocompletado, guardar/cargar configuraciones con nombre (y que cargar una precargue el título como plantilla), que se recuerde la última configuración usada, que los títulos repetidos de listas guardadas se numeren automáticamente, y poder sacar un ítem puntual de una lista guardada (a modo de "ya lo resolví").

- **`static/app.js` — `initUserPicker`**: cada campo de usuarios pasó de `<input name="users">` con CSV a un `<div class="user-picker" data-field="...">` con chips + un input de texto (con `<datalist>` para autocompletar desde `known_users`) + un botón `+` verde (`#16a34a`) que agrega el valor actual como chip (también con Enter). Cada chip tiene una `×` para sacarlo. `root._picker` expone `getValues()`/`setValues()`; `buildPayload`/`applyParams` lo usan en vez de `splitCsv` sobre un input con `name`.
- **Configuraciones con nombre**: cada form tiene una `.config-bar` (select + Cargar + 🗑 + "Guardar configuración actual"). Guardar hace `prompt()` del nombre y `POST /api/configs/{flow}` (upsert por `(flow, name)` en Mongo). Cargar trae los params guardados (`GET /api/configs/{flow}/{id}`), los aplica al form con `applyParams` y **rellena el campo "Título para guardar" con el nombre de la configuración** como plantilla editable.
- **Último config usado**: cada corrida llama a `db.remember_last_config(flow, payload)` al arrancar (dentro del hilo de fondo, igual que ya hacía `db.remember_users`/`db.save_list`, para no bloquear el event loop con una llamada sync a Mongo). Al abrir la página, cada form pide `GET /api/configs/{flow}/last` y precarga los campos (sin tocar el título, que queda limpio para cada corrida nueva).
- **Títulos duplicados**: `db._dedupe_title` revisa los títulos ya usados en ese flujo y agrega `" (1)"`, `" (2)"`... antes de insertar — aplica también a "Sin título" cuando no se puso ninguno.
- **Borrar un ítem suelto**: `DELETE /api/lists/{list_id}/items/{index}` (`db.remove_item_from_list`) saca un ítem puntual del array `items` sin borrar la lista entera. En el frontend aparece como botón "Resuelto" por fila, tanto en el resultado recién generado (usa el `list_id` que ya devuelve la corrida) como en una lista guardada ya abierta. `renderResults` ahora mantiene el array de ítems en un closure y re-dibuja la tabla entera en cada borrado para que los índices de fila sigan coincidiendo con los índices reales en Mongo (si solo se ocultara la fila sin re-renderizar, los índices de las filas restantes quedarían desalineados tras el primer borrado).

Probado en vivo contra un cluster de Mongo Atlas real (ya configurado en `.env`): dedupe de títulos, borrado de ítem puntual, guardar/listar/obtener/sobreescribir/borrar configuración con nombre, y último-config-usado — los 4 vía llamada directa a `db.py` y los de API también vía HTTP con sesión autenticada real.

### Usuarios de vjudge en Codeforces y Gym (2026-10-26)

Pedido del usuario: que Codeforces y Gym también acepten handles de vjudge para detectar "ya resuelto"/"ya tocado", igual que ya hacía AtCoder desde antes.

- **Verificado en vivo contra el endpoint real** (`vjudge.net/status/data`, `OJId=CodeForces`, mismo endpoint no documentado que ya usaba `atcoder.py` filtrado a `OJId=AtCoder`): `probNum` para problemas de Codeforces ya viene como `"{contestId}{index}"` (ej. `"2203B"`, `"1458A"`) — el mismo formato de key que usa este proyecto, sin necesidad de traducir nada.
- **`app.py`**: nuevas `fetch_user_vjudge_cf_rows` (paginación cruda contra el endpoint, compartida), `fetch_user_vjudge_solved` (filtra `status == "Accepted"`, arma el set de keys) y `get_group_solved(users, users_vjudge, ...)` (unión de ambas fuentes, mismo patrón que `atcoder.fetch_group_solved`). `generate_recommendations` ahora acepta `users_vjudge=None` y ya no exige que `users` no esté vacía — exige que **al menos una** de las dos listas lo esté, igual que ya hacía `atcoder.find_recommended_abc`.
- **`gym.py`**: importa `fetch_user_vjudge_cf_rows` de `app.py` (sin ciclo — `app.py` no importa `gym.py`) y agrega `fetch_user_vjudge_touched_gyms`, que parsea el contestId real de los primeros dígitos de `probNum` (el campo `"contestId"` que devuelve vjudge es un id *interno* suyo, no el real de Codeforces) y lo marca tocado si es `>= GYM_ID_MIN`. **No se confirmó empíricamente que vjudge mirrore problemas de gym específicamente** (sí se confirmó para problemas normales de Codeforces) — si no los mirrorea, esta función simplemente no encuentra ninguno, sin romper nada.
- `find_untouched_gyms` ahora acepta `users_vjudge=None`. `server.py` pasa `payload.get("users_vjudge", [])` en los runners de `codeforces` y `gym`, y llama `db.remember_users("vjudge", ...)` en ambos. El frontend agrega un segundo `user-picker` ("Usuarios (vjudge)") en esos dos tabs, reusando el mismo `<datalist id="dl-vj-users">` que ya existía en el tab de AtCoder (un solo `<datalist>` en el documento, varios `<input list="dl-vj-users">` apuntándole — válido en HTML).
- `config.json` ahora declara `"users_vjudge": []` en `codeforces` y `gym` para que la clave sea descubrible (comportamiento sin cambios si se deja vacía).

Probado en vivo: `app.fetch_user_vjudge_solved("pacha2880", ...)` trajo 83 problemas reales; `generate_recommendations([], "difficulties", ..., users_vjudge=["pacha2880"])` funcionó con `users` vacía; `gym.fetch_user_vjudge_touched_gyms("pacha2880", ...)` corrió sin error (0 encontrados, esperable dado el caveat de arriba); `py main.py codeforces` y `py main.py gym` corridos de punta a punta sin cambios de comportamiento visible; una corrida real vía HTTP (`POST /api/run/codeforces` con `users: []`, `users_vjudge: ["pacha2880"]`) funcionó completa con SSE + guardado en Mongo real.

### Cloudflare Worker para vjudge y gym desde Render (2026-10-27)

Cloudflare bloquea por reputación de IP las requests desde Render a `vjudge.net/status/data` y a `codeforces.com/gym/{id}` (challenge "Just a moment", con cualquier cliente HTTP). Desde un Cloudflare Worker (plan free) ambos responden 200, así que en Render esos dos fetches pasan por el Worker.

- `cloudflare_worker.js`: código del Worker (`proxy.pacha2881.workers.dev`). Exige header `X-Proxy-Key` == secret `PROXY_KEY` (401 si no coincide) y solo reenvía a esos dos destinos (no es un proxy abierto). Loguea en Observability las respuestas no-200 de upstream.
- **Placement del Worker fijado en Region → GCP `southamerica-east1`** (Settings → Runtime). Por defecto el Worker corre en el colo más cercano a quien lo llama — desde Render eso es PDX (Portland), y ahí vjudge le devuelve el challenge "Just a moment" (403); desde São Paulo pasa. Smart Placement no alcanzó.
- `proxy.py`: `is_configured()` (hay `PROXY_URL` y `PROXY_KEY` en el entorno) y `proxy_get(url)`.
- `app._vjudge_fetch_page` y `gym.has_editorial`: si `proxy.is_configured()` usan el Worker; si no, fetch directo (`requests` para vjudge, `curl` para gym). Sin fallback entre ambos — las env vars solo se setean en Render.
- `"solution"` es sinónimo de tutorial/editorial en `TUTORIAL_RE` (algunos gyms lo listan así).

### Versión visible en la web (2026-10-27)

`server.py` define `APP_VERSION = "0.4.0"` (hardcodeada, sin changelog ni automatización todavía — pedido explícito del usuario de "vos decidí el número") y la inyecta como global de Jinja2 (`templates.env.globals["app_version"]`), así que cualquier template la usa sin pasarla por cada `TemplateResponse`. Se muestra discreta, `position: fixed` en la esquina inferior derecha (`.version-tag` en `style.css`), en `index.html` y `login.html`.

### Pendiente real (no bloqueante)

- Gym en `server.py` solo expone `filters.difficulty_min`/`difficulty_max` en el form (igual que `gui.py`) — el resto de los filtros de gym (`type`, `kind`, `icpc_region`, `duration_*`, `season_*`) no tienen campo en la UI web todavía, aunque si vienen en el payload JSON sí se respetan.
- No hay un equivalente de `solved.txt` (cache anti-repetición entre corridas) para el flujo de Codeforces en la web — cada corrida web empieza con `past=set()` vacío. Es una simplificación deliberada por ahora, no una decisión final — si hace falta, se podría guardar en Mongo un set de keys ya usadas en listas guardadas.
