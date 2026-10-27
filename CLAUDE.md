# Instrucciones para Claude en este repo

## Git

- **Nunca hagas `git commit` a menos que el usuario lo pida explícitamente en ese momento.** Dejá los cambios sin commitear (working tree) para que el usuario pueda revisar el diff antes. Esto aplica aunque hayas hecho cambios grandes o terminado una tarea completa — terminar el trabajo no es lo mismo que pedir el commit.
- Tampoco hagas `git push` sin que te lo pidan explícitamente, incluso si ya hiciste el commit.
- **Antes de cada push a `main`, subí `APP_VERSION` en `server.py` (semver, a mano — no hay changelog ni CI para esto).** Patch (x.y.Z) para fixes/ajustes chicos, minor (x.Y.0) para features nuevas. Si ya hiciste el commit sin bumpear, agregalo en ese mismo commit antes de pushear (o en uno aparte si el commit ya se pusheó).

## Contexto del proyecto

Ver `CONTEXT.md` para el historial detallado de decisiones, arquitectura y gotchas encontrados. `README.md` tiene el uso actual de cada flujo (`py main.py codeforces`/`atcoder`/`gym`, y `py gui.py`).
