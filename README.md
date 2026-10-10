# ProblemsHunter

ProblemsHunter genera recomendaciones de entrenamiento competitivo (problemas de Codeforces, contests de AtCoder y gyms de Codeforces) que ningún usuario configurado haya resuelto todavía.

## Qué hace

- Consulta las APIs públicas de Codeforces y AtCoder (más el endpoint interno de vjudge.net para submissions de AtCoder vía su mirror).
- Revisa los envíos aceptados de todos los handles del grupo.
- Filtra problemas/contests no resueltos por nadie según la configuración de cada flujo.
- Evita repetir problemas usando una cache local en `solved.txt`.
- Genera una salida legible en terminal y en archivo (`results.txt` o `outputs/`, según el flujo).

## Archivos principales

| Archivo | Descripción |
|---|---|
| `main.py` | Punto de entrada: `py main.py codeforces`, `py main.py atcoder` o `py main.py gym`. |
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
    "users_codeforces": ["handle1", "handle2"],
    "difficulties": ["1900", "1900", "1800", "1700", "1700", "1300", "1300", "900", "900", "800"]
}
```

- `users_codeforces`: handles de Codeforces del grupo. Los usa `app.py` y `generate_contest.py`.
- `difficulties`: lista con repeticiones. Cada ocurrencia pide un problema de esa dificultad.

La configuración actual usa 36 handles y genera 50 problemas por tanda:

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
py app.py
```

Si cambiaste usuarios o quieres empezar de cero, borra la cache antes:

```powershell
Remove-Item solved.txt, results.txt -ErrorAction SilentlyContinue
py app.py
```

`app.py` guarda:

- `results.txt`: lista legible de los problemas generados.
- `solved.txt`: problemas marcados como ya recomendados para no repetirlos.

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

También podés seguir usando `py main.py codeforces` como alias de `py app.py`.

### 3. Recomendar gyms de Codeforces

```powershell
py main.py gym
```

Busca, entre los gyms de Codeforces que cumplen los filtros configurados, los que ningún usuario de `config.json["users_gym"]` haya tocado (ni resuelto ni intentado ningún problema), ordenados de más reciente a más antiguo. Sobre la lista final recomendada revisa además si cada gym tiene tutorial/editorial en "Contest materials". Imprime en terminal id, estrellas de dificultad, si tiene tutorial y el link; guarda una fila por gym (id, nombre, dificultad, editorial, link) en `outputs/gym_recommendations.csv`.

Configuración en `config.json`:

```json
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
```

- `count`: cuántos gyms recomendar (por defecto 10).
- `require_editorial`: si es `true`, solo recomienda gyms que efectivamente tengan tutorial/editorial en "Contest materials" — sigue buscando más abajo en la lista (más antiguos) hasta juntar `count` o agotar los candidatos. Si es `false` (default), recomienda los `count` más recientes sin filtrar por esto, y el chequeo de editorial queda solo informativo en el output.
- `filters.type`: formato del contest, `"ICPC"` o `"IOI"` (o `null` para no filtrar).
- `filters.kind`: lista de tipos de contest aceptados (ej. `"Official ICPC Contest"`, `"Training Contest"`, `"Official School Contest"`), o `null` para cualquiera.
- `filters.icpc_region`: región ICPC exacta (ej. `"Northeastern Europe Region"`), o `null`.
- `filters.difficulty_min` / `filters.difficulty_max`: estrellas de dificultad, 1 a 5.
- `filters.duration_min_seconds` / `filters.duration_max_seconds`: duración del contest en segundos (por defecto 18000 = 5 horas).
- `filters.season_from` / `filters.season_to`: rango de temporada (ej. `"2015-2016"`), o `null`.
- `output_csv`: ruta del CSV de salida, con columnas `id,name,difficulty,editorial,link` (`editorial` es `yes`/`no`/`unknown (page fetch blocked)`).

Cualquier filtro en `null` no restringe nada. `users_gym` es una lista de handles de Codeforces separada de `users_codeforces` (los gyms viven en Codeforces, pero puede interesar probarlo con un subconjunto del grupo, o con handles distintos, sin afectar `app.py`).

Nota sobre el chequeo de tutorial/editorial: scrapea `codeforces.com/gym/{id}` con `curl` (no con la librería `requests` de Python, que Cloudflare bloquea por su fingerprint TLS) y reutiliza cookies entre pedidos para no disparar el challenge anti-bot. Si algún pedido puntual queda bloqueado igual, se muestra como "couldn't check" en vez de asumir que no tiene tutorial.

## Flujo recomendado al cambiar usuarios o dificultades

1. Editar `config.json`.
2. Borrar `solved.txt` y `results.txt` si querés empezar de cero.
3. Ejecutar `py main.py codeforces` (o `atcoder`/`gym`).

## Notas importantes

- `solved.txt` acumula problemas entre ejecuciones de `app.py`.
- `outputs/` acumula las salidas de `atcoder.py` y `gym.py`; está en `.gitignore`.
