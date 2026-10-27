# PachaContests

PachaContests genera recomendaciones de entrenamiento competitivo (problemas de Codeforces, contests de AtCoder y gyms de Codeforces) que ningún usuario configurado haya resuelto todavía.

## Qué hace

- Consulta las APIs públicas de Codeforces y AtCoder (más el endpoint interno de vjudge.net para submissions de Codeforces/AtCoder vía su mirror).
- Revisa los envíos aceptados de todos los handles del grupo.
- Filtra problemas/contests no resueltos por nadie según la configuración de cada flujo.
- Evita repetir problemas usando una cache local en `solved.txt`.
- Genera una salida legible en terminal y en archivo (`results.txt` o `outputs/`, según el flujo).

## Archivos principales

| Archivo | Descripción |
|---|---|
| `main.py` | Punto de entrada de consola: `py main.py codeforces`, `py main.py atcoder` o `py main.py gym`. |
| `gui.py` | GUI de escritorio (FreeSimpleGUI) — ver "Interfaz gráfica" más abajo. |
| `server.py` | Backend web (FastAPI) — ver "Backend web" más abajo. |
| `db.py` | Persistencia en MongoDB (usuarios recordados, listas guardadas) para `server.py`. |
| `auth.py` | Login de contraseña compartida para `server.py`. |
| `cancel.py` | `StoppedByUser`, usada por los 3 módulos core y por `gui.py`/`server.py` para cancelar una corrida en curso. |
| `app.py` | Genera problemas nuevos de Codeforces consultando su API. |
| `atcoder.py` | Recomienda AtCoder Beginner Contests recientes sin resolver por el grupo. |
| `gym.py` | Recomienda gyms de Codeforces sin resolver por el grupo. |
| `generate_contest.py` | Script auxiliar para generar un contest con un problema por dificultad. |
| `config.json` | Configuración local: usuarios y parámetros de cada flujo. |
| `solved.txt` | Cache de problemas ya recomendados (Codeforces). |
| `results.txt` | Resultado de la última generación (Codeforces). |
| `outputs/` | Salidas de los flujos de AtCoder y gym. |
| `CONTEXT.md` | Contexto técnico para continuar el proyecto con un LLM. |

## Instalación

```powershell
py -m pip install -r requirements.txt
```

O manualmente:

```powershell
py -m pip install requests
```

## Configuración

El archivo `config.json` tiene esta forma:

```json
{
    "codeforces": {
        "users": ["handle1", "handle2"],
        "users_vjudge": [],
        "difficulties": ["1900", "1900", "1800", "1700", "1700", "1300", "1300", "900", "900", "800"],
        "letters": [],
        "type": "div2",
        "mode": "difficulties",
        "output_links": "outputs/codeforces_results.txt"
    }
}
```

- `codeforces.users`: handles de Codeforces del grupo. Los usa `app.py` y `generate_contest.py`.
- `codeforces.users_vjudge`: handles de **vjudge.net** (opcional, lista independiente de `users` — no necesita corresponder 1:1). Cuenta como "resuelto" también lo aceptado a través del mirror de Codeforces de vjudge, que no aparece en la API de Codeforces porque vjudge envía las soluciones con su propia cuenta bot. Mismo mecanismo que ya usaba `atcoder.py` para AtCoder — ver la nota sobre vjudge más abajo.
- `codeforces.mode`: `"difficulties"` o `"letters"` — cuál de las dos listas de abajo usa esta corrida. Son excluyentes, nunca se combinan.
- `codeforces.difficulties`: lista con repeticiones, usada cuando `mode` es `"difficulties"`. Cada ocurrencia pide un problema de esa dificultad — no hay un `count` separado porque la cantidad por rating ya está codificada en las repeticiones.
- `codeforces.letters`: lista con repeticiones (ej. `["C", "C", "D"]`), usada cuando `mode` es `"letters"` — pide un problema no resuelto que haya sido esa letra (o subletra, "C" matchea "C"/"C1"/"C2", sin importar mayúsculas/minúsculas) en algún contest del tipo configurado en `type`.
- `codeforces.type`: en qué tipo de ronda buscar cuando `mode` es `"letters"`. Es un valor único, no una lista — `"div1"`, `"div3"` y `"div4"` son categorías exclusivas entre sí, pero `"div2"` (el default) ya incluye rounds combinados Div.1+Div.2 y rounds Educational, porque esos también son válidos para entrenar a nivel Div.2.
- `codeforces.output_links`: ruta del archivo de resultados (default `results.txt` en la raíz si no se especifica).

Nota sobre `type`: Codeforces no tiene un campo estructurado para la división del contest — se saca con regex del nombre (`contest.list`). En rounds "espejados" (mismo número, un contest para Div.1 y otro para Div.2), el mismo problema puede tener letra distinta según la división (confirmado: un problema fue "A" en el Div.1 y "C" en el Div.2 del mismo round) — no hace falta remapear nada a mano porque la API ya da la letra correcta por cada contest por separado, solo hay que clasificar cada `contestId`.

Con la configuración de ejemplo del repo (5 handles, 5 dificultades distintas) genera 5 problemas por tanda. La configuración original usaba 36 handles y 50 problemas:

| Dificultad | Por contest | Total |
|---|---:|---:|
| 1900 | 2 | 10 |
| 1800 | 1 | 5 |
| 1700 | 2 | 10 |
| 1300 | 2 | 10 |
| 900 | 2 | 10 |
| 800 | 1 | 5 |
| **Total** | **10** | **50** |

## Uso

### 1. Generar problemas nuevos

```powershell
py main.py codeforces
```

Si cambiaste usuarios o quieres empezar de cero, borra la cache antes:

```powershell
Remove-Item solved.txt, results.txt -ErrorAction SilentlyContinue
py main.py codeforces
```

`app.py` guarda:

- `codeforces.output_links` (default `results.txt`): lista legible de los problemas generados.
- `solved.txt`: problemas marcados como ya recomendados para no repetirlos (cache aparte, no configurable — es lo que evita repetir sugerencias entre corridas).

### 2. Recomendar AtCoder Beginner Contests

```powershell
py main.py atcoder
```

Busca, entre los ABC más recientes (`lookback` en `config.json`), los que ningún usuario configurado haya tocado (ningún problema del contest resuelto), y recomienda hasta `count` de ellos. Imprime los links en terminal y los guarda en `outputs/atcoder_links.txt`.

Cuenta como "resuelto" un problema aceptado tanto en la cuenta de **AtCoder** del usuario como en su cuenta de **vjudge.net** (si tiene una configurada) — vjudge deja enviar soluciones a problemas de AtCoder a través de su propio mirror, y esas submissions no aparecen en la API de AtCoder Problems (`kenkoooo.com`), así que sin este segundo chequeo se podían recomendar contests que alguien ya había resuelto ahí.

Configuración en `config.json`:

```json
"atcoder": {
    "users_atcoder": ["handle1", "handle2"],
    "users_vjudge": ["handle1_vj", "handle3_vj"],
    "count": 5,
    "lookback": 50,
    "problems": [],
    "output_links": "outputs/atcoder_links.txt"
}
```

- `users_atcoder`: handles de **AtCoder** (no necesariamente iguales a los de Codeforces).
- `users_vjudge`: handles de **vjudge.net**. Es una lista independiente, no tiene que tener el mismo tamaño que `users_atcoder` ni corresponder 1:1 — una persona puede estar en una sola lista, en ambas, o ninguna.
- `count`: cuántos contests recomendar.
- `lookback`: cuántos ABC recientes considerar como candidatos.
- `problems`: lista de letras (ej. `["c", "d", "e"]`) para chequear solo esos problemas del contest en vez del contest entero — se recomienda si ninguno de los problemas listados fue resuelto, aunque A/B sí lo estén. Vacía (`[]`, default) revisa el contest completo como antes. Si una letra no existe en algún contest (pasa en ABCs viejos), se reporta en terminal y se la salta para ese contest; si ninguna de las letras pedidas existe ahí, el contest entero se saltea. Cuando esta lista no está vacía, el archivo de salida pasa de `atcoder_links.txt` a `atcoder_links_C-D-E.txt` (sufijo con las letras en mayúscula, antes de la extensión).
- `output_links`: ruta del archivo de salida con los links.

Nota sobre vjudge: usa un endpoint interno no documentado (`vjudge.net/status/data`, el mismo que usa la propia página de status) — no hay garantía de que Vjudge no lo cambie sin aviso.

Nota sobre vjudge y gym desde Render: Cloudflare bloquea las IPs de Render, así que ahí esos fetches pasan por un Cloudflare Worker (`cloudflare_worker.js`, ver `PROXY_URL`/`PROXY_KEY` más abajo). Local no hace falta.

También podés seguir usando `py main.py codeforces` como alias de `py app.py`.

### 3. Recomendar gyms de Codeforces

```powershell
py main.py gym
```

Busca, entre los gyms de Codeforces que cumplen los filtros configurados, los que ningún usuario de `config.json["gym"]["users"]` haya tocado (ni resuelto ni intentado ningún problema), ordenados de más reciente a más antiguo. Sobre la lista final recomendada revisa además si cada gym tiene tutorial/editorial en "Contest materials". Imprime en terminal id, estrellas de dificultad, si tiene tutorial y el link; guarda una fila por gym (id, nombre, dificultad, editorial, link) en `outputs/gym_recommendations.csv`.

Configuración en `config.json`:

```json
"gym": {
    "users": ["handle1", "handle2"],
    "users_vjudge": [],
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
```

- `users`: handles de Codeforces para este flujo — lista separada de `codeforces.users` (los gyms viven en Codeforces, pero puede interesar probarlo con un subconjunto del grupo, o con handles distintos, sin afectar `app.py`).
- `users_vjudge`: handles de **vjudge.net** (opcional). Un gym cuenta como "tocado" si aparece entre sus submissions mirror de Codeforces, reconocido por el id de contest al principio de cada `probNum` que vjudge devuelve (ej. `"107277A"` → gym `107277`) — no confirmado empíricamente que vjudge mirrore gyms específicamente (sí confirmado para problemas normales de Codeforces), así que si no los mirrorea esto simplemente no encuentra ninguno, sin romper nada.
- `count`: cuántos gyms recomendar (por defecto 10).
- `require_editorial`: si es `true`, solo recomienda gyms que efectivamente tengan tutorial/editorial en "Contest materials" — sigue buscando más abajo en la lista (más antiguos) hasta juntar `count` o agotar los candidatos. Si es `false` (default), recomienda los `count` más recientes sin filtrar por esto, y el chequeo de editorial queda solo informativo en el output.
- `filters.type`: formato del contest, `"ICPC"` o `"IOI"` (o `null` para no filtrar).
- `filters.kind`: lista de tipos de contest aceptados (ej. `"Official ICPC Contest"`, `"Training Contest"`, `"Official School Contest"`), o `null` para cualquiera.
- `filters.icpc_region`: región ICPC exacta (ej. `"Northeastern Europe Region"`), o `null`.
- `filters.difficulty_min` / `filters.difficulty_max`: estrellas de dificultad, 1 a 5.
- `filters.duration_min_seconds` / `filters.duration_max_seconds`: duración del contest en segundos (por defecto 18000 = 5 horas).
- `filters.season_from` / `filters.season_to`: rango de temporada (ej. `"2015-2016"`), o `null`.
- `output_csv`: ruta del CSV de salida, con columnas `id,name,difficulty,editorial,link` (`editorial` es `yes`/`no`/`unknown (page fetch blocked)`).

Cualquier filtro en `null` no restringe nada.

Nota sobre el chequeo de tutorial/editorial: scrapea `codeforces.com/gym/{id}` con `curl` (no con la librería `requests` de Python, que Cloudflare bloquea por su fingerprint TLS) y reutiliza cookies entre pedidos para no disparar el challenge anti-bot. Si algún pedido puntual queda bloqueado igual, se muestra como "couldn't check" en vez de asumir que no tiene tutorial.

## Flujo recomendado al cambiar usuarios o dificultades

1. Editar `config.json`.
2. Borrar `solved.txt` y `results.txt` si querés empezar de cero.
3. Ejecutar `py main.py codeforces` (o `atcoder`/`gym`).

## Interfaz gráfica

```powershell
py gui.py
```

Ventana con una pestaña por flujo (Codeforces/AtCoder/Gym), campos precargados desde `config.json`, y un log compartido abajo. Al apretar "Generar":

1. Relee `config.json` del disco, actualiza **solo el bloque de ese flujo** con los valores del formulario, y lo guarda — la consola (`py main.py codeforces`/`atcoder`/`gym`) ve los mismos cambios después. Si algún campo no parsea (ej. "Count" con texto en vez de un número), no se guarda nada y se muestra el error.
2. Corre el mismo `app.main()`/`atcoder.main()`/`gym.main()` que usa la consola — misma lógica, mismos archivos de salida (`results.txt`, `outputs/atcoder_links...txt`, `outputs/gym_recommendations.csv`), sin código duplicado — pero inyectándole su propio callback de progreso en vez de `print`.
3. Esa corrida va en un hilo aparte (las corridas reales tardan entre 15s y un par de minutos) para no congelar la ventana; el callback usa `window.write_event_value()`, que es thread-safe, en vez de tocar el widget del log directo desde el hilo.

Los 3 botones "Generar" se deshabilitan mientras cualquiera de los 3 está corriendo, para no pisarse escribiendo `config.json` al mismo tiempo. También hay dos botones compartidos arriba del log:

- **Detener**: pide que la corrida actual pare. No es instantáneo — Python no puede matar un hilo a la fuerza, así que se le avisa con una señal (`cancel.StoppedByUser`) que se revisa entre cada usuario/contest/gym procesado, y frena ahí. Si para, **no se genera ningún archivo** (ni `results.txt`, ni `solved.txt`, ni el CSV/links de salida) — se corta antes de escribir nada, justamente porque los datos quedarían incompletos.
- **Limpiar**: vacía el log. No afecta ninguna corrida en curso.

Esto se apoya en tres cambios de `app.py`/`atcoder.py`/`gym.py`: el progreso se reporta por inyección de dependencias (`on_progress`, con `print` como default para que la consola no cambie nada), si falta configuración obligatoria los 3 módulos levantan `ValueError` en vez de pedir `input()` por consola (un `input()` colgaría la GUI esperando algo que nunca va a llegar), y los loops largos (fetch por usuario, chequeo de editorial por gym) aceptan un `should_stop` opcional que, si da `True`, corta ahí mismo.

Nota: como `gui.py` reescribe `config.json` entero con `json.dump(..., indent=4)` cada vez que guarda, el archivo va a quedar reformateado (arrays multilínea) la primera vez que uses la GUI, aunque el contenido sea el mismo.

## Backend web (`server.py`)

Pieza nueva y separada — ni la consola ni `gui.py` la usan ni dependen de ella, y al revés tampoco (no toca `config.json`, `solved.txt` ni `outputs/`). Llama a la misma lógica core (`app.generate_recommendations`, `atcoder.find_recommended_abc`, `gym.find_untouched_gyms`/`select_recommendations`), pero con parámetros que vienen de un formulario web en vez de `config.json`.

```powershell
py -m pip install -r requirements-web.txt
py -m uvicorn server:app --reload
```

Abre en `http://127.0.0.1:8000`. Variables de entorno (todas opcionales para probar local):

- `APP_PASSWORD`: contraseña compartida para el login. Sin ella, el gate queda abierto — no hace falta inventar una para desarrollar.
- `SECRET_KEY`: firma la cookie de sesión. Sin ella usa un valor fijo de desarrollo — **hay que setearla en producción**.
- `MONGODB_URI`: connection string de MongoDB. Sin ella, "usuarios recordados" y "listas guardadas" quedan vacíos pero el resto (correr los 3 flujos, ver progreso en vivo) funciona igual.
- `PROXY_URL` / `PROXY_KEY`: URL del Cloudflare Worker y su clave (secret `PROXY_KEY` del Worker). Solo en Render; local se dejan sin setear y vjudge/gym se piden directo.

### Qué tiene

- Las mismas 3 pestañas que la GUI (Codeforces/AtCoder/Gym), con autocompletado de usuarios ya usados antes (si hay Mongo configurada).
- Progreso en vivo vía Server-Sent Events — mismo patrón de fondo que `gui.py` (hilo aparte + cola de mensajes), transporte distinto (SSE en vez de `window.write_event_value`).
- Botón Detener por corrida (misma cancelación cooperativa de `cancel.py` que ya usan consola/GUI).
- Cada corrida se puede guardar con un título editable; "Listas guardadas" las lista, se pueden renombrar o borrar.
- Login simple de una sola contraseña compartida (sin cuentas individuales).

### Deploy en Render (gratis)

El repo incluye `render.yaml` para deploy con un clic (Render → New → Blueprint, apuntando a este repo). Variables a completar en el dashboard de Render: `APP_PASSWORD`, `MONGODB_URI`, `PROXY_URL` y `PROXY_KEY` (`SECRET_KEY` se genera sola). El plan free "duerme" tras 15 min sin uso — el primer request después tarda unos segundos en levantar, nada más; como la persistencia vive en MongoDB (no en disco local), no se pierde nada con eso.

Base de datos: [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) tiene un tier gratis para siempre (M0, 512MB) — alcanza de sobra para esta escala.

## Notas importantes

- `solved.txt` acumula problemas entre ejecuciones de `app.py`.
- `outputs/` acumula las salidas de `atcoder.py` y `gym.py`; está en `.gitignore`.
