# Contexto del proyecto para LLM

Última actualización: 2026-09-03.

Este documento resume el estado real del proyecto, las decisiones tomadas y los detalles técnicos necesarios para continuar sin perder contexto.

## Qué hace el proyecto

ProblemsHunter es una herramienta de entrenamiento competitivo para un grupo de programadores bolivianos en Codeforces.

Tiene dos flujos principales:

1. `app.py`: usa la API pública de Codeforces para encontrar problemas que ningún miembro del grupo haya resuelto, filtrados por dificultad y ordenados del más reciente al más antiguo.
2. `fill_sheet.py`: sube esos problemas a una Google Sheet estructurada en 5 contests de entrenamiento, conservando problemas preexistentes del sheet y añadiendo tema, observación/pista y nombre oficial del contest.

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
py -m py_compile app.py fill_sheet.py generate_contest.py read_sheet.py update_labels.py
```

En esta máquina el comando `python` no está disponible; se usa `py`.

### Usuarios activos

El archivo `config.json["users_codeforces"]` tiene actualmente 36 handles (usados por `app.py`, `generate_contest.py` y `fill_sheet.py`):

`__profeta`, `Simurdiera_MAC`, `Alexander1755`, `Karenn`, `Andres_Espada`, `Max241`, `HeReWeGoAgAiN123`, `Oliver_Pozo_Flores`, `OPF10`, `pacha2880`, `NeverSayF`, `alexalvarez123`, `The_Lion_King_777`, `candi_ositos`, `zoryn`, `Gabriel___`, `PyroxBoy`, `pharaoh583`, `ErlandMB`, `romerproblem`, `Dilan8787`, `pablo-acha`, `eeliezercm2`, `jim_games`, `alvmaury1`, `MCMT17`, `mortyseb`, `camilo_zuleta`, `Osvaldo34`, `samuellr`, `grxchx`, `alabrito4007`, `srllamadev`, `AMAMEMIE`, `Mr_chuby`, `Zeincho`

### Dificultades activas

La tanda actual genera 50 problemas:

| Dificultad | Cantidad total |
|---|---:|
| 1900 | 10 |
| 1800 | 5 |
| 1700 | 10 |
| 1300 | 10 |
| 900 | 10 |
| 800 | 5 |

No hay dificultades 1200 ni 1600 por decisión del usuario.

### Google Sheet

URL configurada:

`https://docs.google.com/spreadsheets/d/1r3DtJmLLfe71z-kavyngaYmfs63xQq0Vq2aQd6d4Lq8/edit?usp=sharing`

Cuenta de servicio:

`pacha-labs@iron-rex-241415.iam.gserviceaccount.com`

Credenciales locales:

`credentials.json`

No subir `credentials.json` a GitHub.

### Cache y última generación

- `results.txt` contiene la última tanda principal de 50 problemas.
- `solved.txt` contiene 63 claves de problemas ya recomendados/cacheados.
- Esto significa que hay 13 problemas adicionales en cache además de los 50 del último lote documentado en `results.txt`.

## Estructura del Google Sheet

Cada contest ocupa 5 filas más 1 fila en blanco:

```text
Fila 1: Contest N   | A                        | B                        | ...
Fila 2: rating      | 1900                     | 1700                     | ...
Fila 3: tema        | Constructivo / Greedy    | Búsqueda binaria         | ...
Fila 4: observación | Pista breve de solución  | Otra pista               | ...
Fila 5: contest     | Codeforces Round ...     | Educational Round ...    | ...
Fila 6: vacía
```

Las letras en la fila 1 son fórmulas `=HYPERLINK("url","A")`, no texto plano. Al leer el sheet con `value_render_option="FORMULA"` se ven las fórmulas; con render por defecto solo se ven las letras.

Cada contest tiene actualmente 14 columnas: 4 problemas existentes más 10 problemas nuevos.

## Problemas existentes en el sheet

Estos 18 problemas ya existían antes del proyecto. Tienen ratings 1700-2900 y vienen de Bubble Cup X y Educational Rounds 1-9. Sus URLs originales se extrajeron con la Sheets API v4 (`includeGridData=true`) porque eran rich-text hyperlinks, no fórmulas.

| Contest | URL CF | Rating | Tema | Contest oficial |
|---|---|---:|---|---|
| 1-A | `/contest/852/problem/B` | 2000 | DP / Matrices | Bubble Cup X |
| 1-B | `/contest/852/problem/F` | 2200 | Combinatoria / Matemáticas | Bubble Cup X |
| 1-C | `/contest/616/problem/E` | 2200 | Matemáticas / Teoría de números | Educational Round 5 |
| 1-D | `/contest/622/problem/D` | 1900 | Constructivo | Educational Round 7 |
| 2-A | `/contest/852/problem/G` | 1700 | Implementación | Bubble Cup X |
| 2-B | `/contest/852/problem/D` | 2100 | Búsqueda binaria / Flujos | Bubble Cup X |
| 2-C | `/contest/852/problem/E` | 2100 | Programación dinámica | Bubble Cup X |
| 2-D | `/contest/612/problem/E` | 2200 | Constructivo / Ciclos | Educational Round 4 |
| 3-A | `/contest/598/problem/E` | 2000 | DP / Fuerza bruta | Educational Round 1 |
| 3-B | `/contest/598/problem/F` | 2900 | Geometría | Educational Round 1 |
| 3-C | `/contest/622/problem/F` | 2600 | Matemáticas / Interpolación | Educational Round 7 |
| 4-A | `/contest/600/problem/F` | 2800 | Grafos / Coloreo de aristas | Educational Round 2 |
| 4-B | `/contest/609/problem/D` | 2000 | Búsqueda binaria / Greedy | Educational Round 3 |
| 4-C | `/contest/622/problem/E` | 2200 | DFS / Greedy / Árboles | Educational Round 7 |
| 5-A | `/contest/609/problem/F` | 2500 | Estructuras de datos / Greedy | Educational Round 3 |
| 5-B | `/contest/612/problem/D` | 1800 | Greedy / Ordenamiento | Educational Round 4 |
| 5-C | `/contest/620/problem/D` | 2200 | Búsqueda binaria / Dos punteros | Educational Round 6 |
| 5-D | `/contest/632/problem/D` | 2100 | Fuerza bruta / Matemáticas | Educational Round 9 |

## Problemas nuevos de la última tanda

Distribución por cada contest:

- 1900 x2
- 1800 x1
- 1700 x2
- 1300 x2
- 900 x2
- 800 x1

Lista definida en `fill_sheet.py`:

| Contest | Problemas |
|---|---|
| Contest 1 | 2217D(1900), 2190B2(1900), 2196C1(1800), 2215A(1700), 2135B(1700), 2216B(1300), 2187A(1300), 2216A(900), 1758B(900), 1912L(800) |
| Contest 2 | 2189D1(1900), 2184G(1900), 2187B(1800), 2132E(1700), 2123F(1700), 2165A(1300), 2150A(1300), 1585B(900), 1582B(900), 1864A(800) |
| Contest 3 | 2174B(1900), 2138B(1900), 2185G(1800), 2122C(1700), 2090C(1700), 2022B(1300), 1978C(1300), 1501B(900), 1488A(900), 1810B(800) |
| Contest 4 | 2117G(1900), 2109D(1900), 2153D(1800), 2089A(1700), 2080B(1700), 1769C2(1300), 1693A(1300), 1468N(900), 1445B(900), 1769A(800) |
| Contest 5 | 2077B(1900), 2068F(1900), 2145D(1800), 2072F(1700), 2065G(1700), 1667A(1300), 1615B(1300), 1267B(900), 1225A(900), 1739A(800) |

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

Importante: `app.py` todavía tiene una función `upload_to_sheets()` al final. Esa subida produce una lista plana, no la estructura completa del sheet principal. Para el flujo principal usar `fill_sheet.py`.

## Arquitectura de `fill_sheet.py`

- `EXISTING`: diccionario con los 18 problemas preexistentes del sheet, sus URLs, tema, observación y contest oficial.
- `NEW`: diccionario con los 50 problemas nuevos distribuidos 10 por contest.
- `build_contest_data()`: combina `EXISTING` y `NEW`.
- `build_sheet_rows()`: construye la matriz de filas para Google Sheets.
- `upload()`: limpia y reescribe el sheet usando `value_input_option="USER_ENTERED"` para que Sheets evalúe las fórmulas `HYPERLINK`.
- Usa `random.seed(42)` para shuffle reproducible.

## Cómo extraer hyperlinks rich-text del sheet existente

Los hyperlinks originales del sheet son rich-text links creados con Insert > Link, no fórmulas. `gspread` con `value_render_option="FORMULA"` no los devuelve.

Para obtenerlos hay que llamar a la Sheets API v4 directamente:

```python
import google.auth.transport.requests

creds.refresh(google.auth.transport.requests.Request())
url = f"https://sheets.googleapis.com/v4/spreadsheets/{sid}?includeGridData=true"
r = requests.get(url, headers={"Authorization": f"Bearer {creds.token}"})

# Luego:
# data["sheets"][0]["data"][0]["rowData"][row]["values"][col]["hyperlink"]
```

## Decisiones de diseño

| Decisión | Razón |
|---|---|
| API de Codeforces en vez de Selenium | Es más rápida, estable y no depende de Chrome. |
| `solved.txt` como cache | Evita repetir sugerencias entre ejecuciones. |
| Repeticiones en `difficulties` | Cada ocurrencia representa un problema pedido de esa dificultad. |
| `random.seed(42)` | Permite reproducir el mismo orden de contests. |
| `fill_sheet.py` separado de `app.py` | Permite generar problemas sin tocar Google Sheets y subir solo cuando el lote esté listo. |
| Sin 1200 ni 1600 | Se eliminaron por decisión del usuario. |

## Flujo para actualizar usuarios o dificultades

1. Editar `config.json`.
2. Borrar `solved.txt` y `results.txt` si se quiere regenerar desde cero.
3. Ejecutar `py app.py`.
4. Revisar `results.txt`.
5. Actualizar `NEW` en `fill_sheet.py` con problemas, temas, observaciones y contests oficiales.
6. Restaurar manualmente el sheet a su estado base si hace falta.
7. Ejecutar `py fill_sheet.py`.

Para obtener nombres oficiales de contests:

```powershell
py -c "import requests; r=requests.get('https://codeforces.com/api/contest.list',params={'gym':False}); [print(c['id'],'|',c['name']) for c in r.json()['result'] if c['id'] in {2217,2190}]"
```

## Gotchas importantes

- Codeforces puede rate-limitear `user.status`; si falla, esperar y reintentar.
- `user.status` usa `count=10000`; si un handle tiene más envíos, puede hacer falta aumentar ese valor.
- El usuario suele restaurar manualmente el sheet antes de correr `fill_sheet.py`.
- `fill_sheet.py` limpia y reescribe el sheet.
- En Windows puede haber problemas de encoding en consola; los scripts ya usan configuración UTF-8 para stdout donde aplica.
- Las credenciales pertenecen al proyecto Google Cloud `iron-rex-241415` y la cuenta de servicio `pacha-labs`.

## Plan de implementación: recomendador AtCoder ABC

Estado: implementado (2026-09-03). Ver `atcoder.py` y `main.py`.

`config.json["atcoder"]["users_atcoder"]`/`["users_vjudge"]` tenían 4 handles reales confirmados cada una (`pacha2880`, `DilanJCM8787`, `AMAMEMIE`/`AMAMEMIE_uwu`, `pypyroxboy`/`PyroxBoy`), pero el usuario los recortó manualmente (2026-10-02) a solo `users_atcoder: ["DilanJCM8787"]` y `users_vjudge: ["DilanJCM8787", "DJCM8787"]` mientras probaba — posiblemente sin querer, no lo revertí porque no está claro si fue deliberado. Si la intención era recomendar para todo el grupo, falta restaurar `pacha2880`, `AMAMEMIE`/`AMAMEMIE_uwu` y `pypyroxboy`/`PyroxBoy` en ambas listas. También falta completar el resto del grupo de Codeforces (32 de 36 sin handle de AtCoder todavía).

Decisiones tomadas al implementar:

- `main.py` es un selector mínimo que no refactoriza `app.py`: `py main.py codeforces` simplemente importa y llama a `app.main()`; `py main.py atcoder` llama a `atcoder.main()`. `app.py` y `fill_sheet.py` siguen funcionando igual que antes, sin cambios.
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

- `main.py` gana un tercer modo: `py main.py gym`, mismo patrón que `atcoder.py` — no toca `app.py`/`fill_sheet.py`.
- Usa `config.json["users_gym"]`, una lista separada de `users_codeforces` (2026-09-14, a pedido del usuario) — por defecto tiene solo 4 handles de prueba (`nicolasalba`, `__profeta`, `Simurdiera_MAC`, `Alexander1755`), no los 36 del grupo completo. Permite probar el módulo sin las ~36 llamadas a `user.status` que tardan minutos, y sin acoplar el flujo de gyms al de Codeforces/Sheets.
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

1. Leer `config.json`: usuarios (`config["users_gym"]`), filtros de `config["gym"]["filters"]`, `count`, `output_csv`.
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

Probado end-to-end (2026-09-14) con los handles `nicolasalba`, `__profeta`, `Simurdiera_MAC`, `Alexander1755`: 447/2630 gyms cumplían los filtros por defecto, ese grupo había tocado 222, y la recomendación final de 10 gyms incluyó una mezcla real de con/sin tutorial (confirmado manualmente contra el HTML, no todo "encontrado" como en el primer intento con los bugs sin corregir). Primero se probó pasando esos handles directo a `find_recommended_gyms()` sin tocar el config; luego, al separar `users_codeforces`/`users_gym`, se corrió `py main.py gym` real con esos mismos 4 handles ya en `config.json["users_gym"]` y dio el mismo resultado.

Comando esperado:

```powershell
py main.py gym
```
