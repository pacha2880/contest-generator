# Contexto del proyecto para LLM

Última actualización: 2026-10-10.

Este documento resume el estado real del proyecto, las decisiones tomadas y los detalles técnicos necesarios para continuar sin perder contexto.

## Qué hace el proyecto

ProblemsHunter es una herramienta de entrenamiento competitivo para un grupo de programadores bolivianos, con tres flujos iguales en espíritu (API pública → filtrar lo no resuelto por el grupo → mostrar/guardar), cada uno seleccionable desde `main.py`:

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
- **Streamlit sigue siendo la recomendación para la versión web** cuando llegue ese momento — ahí sí tiene sentido un servidor, y Streamlit Community Cloud es gratis y se despliega solo desde GitHub. Para esa fase faltará decidir: (a) dashboard fijo del grupo vs (b) herramienta pública multi-tenant (usuarios ingresan sus propios handles), porque cambia bastante el diseño — no decidido todavía. También hay riesgo real de rate-limit compartido si varios visitantes corren flujos a la vez desde la misma IP del servidor, y el bypass de Cloudflare vía `curl` en `gym.py` no está garantizado que se comporte igual desde una IP de datacenter — habría que probarlo en vivo.
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

### Esqueleto de `gui.py` (2026-10-10)

Creado con FreeSimpleGUI (`py -m pip install FreeSimpleGUI`, agregado a `requirements.txt`). Es estructura nada más — todavía no está conectado al backend real:

- Una ventana con `TabGroup` de 3 pestañas (Codeforces/AtCoder/Gym), cada una con los campos de su bloque de `config.json` precargados (usuarios, dificultades/count/lookback/problems, filtros de gym) como `sg.Input`/`sg.Checkbox`.
- Un `sg.Multiline` compartido abajo de las pestañas, pensado como destino del futuro `on_progress`.
- Un botón "Generar" por pestaña — por ahora el handler del loop de eventos solo escribe una línea de placeholder en el log ("todavía no conectado al backend (esqueleto)"), no llama a ningún flujo real todavía.
- Probado lanzándolo (`py gui.py` en background): abre sin errores, no se investigó interacción real de click porque no hay forma de probar eso desde este entorno — falta confirmarlo visualmente del lado del usuario.

Pendiente (próximos pasos, no implementado todavía):

1. Conectar cada botón "Generar": leer los campos del tab, armar el dict de config equivalente, y correr la función real del módulo correspondiente (`app.main()`-equivalente, `atcoder.find_recommended_abc(...)`, `gym.find_untouched_gyms(...)` + `select_recommendations(...)`) en un **hilo aparte** — si corre en el hilo principal de Tkinter, la ventana se congela durante el minuto o más que tarda.
2. El `on_progress` que le pase la GUI a esas funciones tiene que ser thread-safe respecto al widget: lo estándar es que el hilo de trabajo empuje mensajes a una `queue.Queue`, y el loop de eventos de la GUI los vaya sacando con `window.read(timeout=...)` y escribiéndolos en `-LOG-` — no llamar directo a métodos de un widget Tkinter desde otro hilo.
3. Decidir si el botón "Generar" escribe los valores del formulario de vuelta a `config.json` antes de correr (para que la consola vea los mismos cambios después) o si corre "ad hoc" sin persistir — se discutió en la conversación que la idea original era que la GUI fuera "un `config.json` dinámico", así que probablemente conviene que sí escriba a disco.
4. Mostrar los resultados en la GUI (tabla o el mismo texto que ya se guarda en el archivo de salida) — más fácil: después de que termine el hilo, leer el archivo de salida (`output_links`/`output_csv`) y mostrarlo, sin tocar las funciones del backend para que devuelvan algo distinto a lo que ya devuelven.
