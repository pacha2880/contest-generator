# ProblemsHunter

ProblemsHunter genera contests de entrenamiento con problemas de Codeforces que ninguno de los usuarios configurados haya resuelto todavía, y puede subirlos a una Google Sheet organizada por contests.

## Qué hace

- Consulta la API pública de Codeforces.
- Revisa los envíos aceptados de todos los handles del grupo.
- Filtra problemas no resueltos por nadie según las dificultades configuradas.
- Evita repetir problemas usando una cache local en `solved.txt`.
- Genera una salida legible en `results.txt`.
- Sube contests estructurados a Google Sheets con rating, tema, pista y nombre oficial del contest.

## Archivos principales

| Archivo | Descripción |
|---|---|
| `app.py` | Genera problemas nuevos consultando la API de Codeforces. |
| `fill_sheet.py` | Sube los contests estructurados a Google Sheets. |
| `generate_contest.py` | Script auxiliar para generar contests. |
| `read_sheet.py` | Script auxiliar para leer datos del sheet. |
| `update_labels.py` | Script auxiliar para actualizar etiquetas/metadatos. |
| `main.py` | Punto de entrada para elegir flujo: `py main.py codeforces` o `py main.py atcoder`. |
| `atcoder.py` | Recomienda AtCoder Beginner Contests recientes sin resolver por el grupo. |
| `config.json` | Configuración local: usuarios, dificultades, URL del sheet, credenciales y config de AtCoder. |
| `credentials.json` | Credenciales de Google Cloud. No subir a GitHub. |
| `solved.txt` | Cache de problemas ya recomendados (Codeforces). |
| `results.txt` | Resultado de la última generación (Codeforces). |
| `outputs/atcoder_links.txt` | Links de la última recomendación de AtCoder. |
| `CONTEXT.md` | Contexto técnico para continuar el proyecto con un LLM. |

## Instalación

```powershell
py -m pip install -r requirements.txt
```

O manualmente:

```powershell
py -m pip install requests gspread google-auth
```

## Configuración

El archivo `config.json` tiene esta forma:

```json
{
    "users_codeforces": ["handle1", "handle2"],
    "difficulties": ["1900", "1900", "1800", "1700", "1700", "1300", "1300", "900", "900", "800"],
    "sheets_url": "https://docs.google.com/spreadsheets/d/ID/edit",
    "credentials_file": "credentials.json"
}
```

- `users_codeforces`: handles de Codeforces del grupo. Los usa `app.py`, `generate_contest.py` y `fill_sheet.py`.
- `difficulties`: lista con repeticiones. Cada ocurrencia pide un problema de esa dificultad.
- `sheets_url`: URL completa de la Google Sheet.
- `credentials_file`: ruta al JSON de la cuenta de servicio de Google Cloud.

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

### 2. Subir contests a Google Sheets

```powershell
py fill_sheet.py
```

`fill_sheet.py` combina los problemas existentes del sheet con los 50 problemas nuevos definidos en el script, los mezcla de forma reproducible y sube la estructura final con:

- Letra del problema como hipervínculo a Codeforces.
- Fila `rating`.
- Fila `tema`.
- Fila `observación`.
- Fila `contest`.

Nota: para el sheet principal se recomienda usar `fill_sheet.py`. `app.py` conserva una función de subida simple, pero esa salida no tiene la estructura completa por contests.

### 3. Recomendar AtCoder Beginner Contests

```powershell
py main.py atcoder
```

Busca, entre los ABC más recientes (`lookback` en `config.json`), los que ningún usuario configurado haya tocado (ningún problema del contest resuelto), y recomienda hasta `count` de ellos. Imprime los links en terminal y los guarda en `outputs/atcoder_links.txt`.

Configuración en `config.json`:

```json
"atcoder": {
    "users": ["handle1", "handle2"],
    "count": 5,
    "lookback": 50,
    "output_links": "outputs/atcoder_links.txt"
}
```

- `users`: handles de **AtCoder** (no son necesariamente los mismos que los de Codeforces). Actualmente solo tiene un handle de prueba (`pacha2880`) — hay que completar la lista real del grupo.
- `count`: cuántos contests recomendar.
- `lookback`: cuántos ABC recientes considerar como candidatos.
- `output_links`: ruta del archivo de salida con los links.

También podés seguir usando `py main.py codeforces` como alias de `py app.py`.

### 4. Recomendar gyms de Codeforces

```powershell
py main.py gym
```

Busca, entre los gyms de Codeforces que cumplen los filtros configurados, los que ningún usuario de `config.json["users_gym"]` haya tocado (ni resuelto ni intentado ningún problema), ordenados de más reciente a más antiguo. Sobre la lista final recomendada revisa además si cada gym tiene tutorial/editorial en "Contest materials". Imprime en terminal id, estrellas de dificultad, si tiene tutorial y el link; guarda los links en `outputs/gym_links.txt`.

Configuración en `config.json`:

```json
"gym": {
    "count": 10,
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
    "output_links": "outputs/gym_links.txt"
}
```

- `count`: cuántos gyms recomendar (por defecto 10).
- `filters.type`: formato del contest, `"ICPC"` o `"IOI"` (o `null` para no filtrar).
- `filters.kind`: lista de tipos de contest aceptados (ej. `"Official ICPC Contest"`, `"Training Contest"`, `"Official School Contest"`), o `null` para cualquiera.
- `filters.icpc_region`: región ICPC exacta (ej. `"Northeastern Europe Region"`), o `null`.
- `filters.difficulty_min` / `filters.difficulty_max`: estrellas de dificultad, 1 a 5.
- `filters.duration_min_seconds` / `filters.duration_max_seconds`: duración del contest en segundos (por defecto 18000 = 5 horas).
- `filters.season_from` / `filters.season_to`: rango de temporada (ej. `"2015-2016"`), o `null`.
- `output_links`: ruta del archivo de salida con los links.

Cualquier filtro en `null` no restringe nada. `users_gym` es una lista de handles de Codeforces separada de `users_codeforces` (los gyms viven en Codeforces, pero puede interesar probarlo con un subconjunto del grupo, o con handles distintos, sin afectar `app.py`/`fill_sheet.py`).

Nota sobre el chequeo de tutorial/editorial: scrapea `codeforces.com/gym/{id}` con `curl` (no con la librería `requests` de Python, que Cloudflare bloquea por su fingerprint TLS) y reutiliza cookies entre pedidos para no disparar el challenge anti-bot. Si algún pedido puntual queda bloqueado igual, se muestra como "couldn't check" en vez de asumir que no tiene tutorial.

## Configurar Google Sheets

1. Crea un proyecto en Google Cloud.
2. Activa Google Sheets API y Google Drive API.
3. Crea una cuenta de servicio.
4. Descarga el JSON de credenciales como `credentials.json`.
5. Comparte la Google Sheet con el email de la cuenta de servicio y dale permiso de editor.
6. Pega la URL del sheet en `config.json`.

## Flujo recomendado al cambiar usuarios o dificultades

1. Editar `config.json`.
2. Borrar `solved.txt` y `results.txt`.
3. Ejecutar `py app.py`.
4. Actualizar `NEW` en `fill_sheet.py` con los problemas nuevos y sus metadatos.
5. Restaurar manualmente el sheet a su estado base si hace falta.
6. Ejecutar `py fill_sheet.py`.

## Notas importantes

- `solved.txt` acumula problemas entre ejecuciones. En el estado actual contiene 63 entradas.
- `fill_sheet.py` usa `random.seed(42)` para que el orden sea reproducible.
- Los problemas preexistentes del sheet se preservan y se completan con tema, observación y contest oficial.
- No subas `credentials.json` a GitHub.
- Si inicializas Git, agrega al menos `credentials.json`, `__pycache__/`, `.env`, `solved.txt` y `results.txt` al `.gitignore`.
