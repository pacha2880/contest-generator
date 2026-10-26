# Instrucciones para Claude en este repo

## Git

- **Nunca hagas `git commit` a menos que el usuario lo pida explícitamente en ese momento.** Dejá los cambios sin commitear (working tree) para que el usuario pueda revisar el diff antes. Esto aplica aunque hayas hecho cambios grandes o terminado una tarea completa — terminar el trabajo no es lo mismo que pedir el commit.
- Tampoco hagas `git push` sin que te lo pidan explícitamente, incluso si ya hiciste el commit.

## Contexto del proyecto

Ver `CONTEXT.md` para el historial detallado de decisiones, arquitectura y gotchas encontrados. `README.md` tiene el uso actual de cada flujo (`py main.py codeforces`/`atcoder`/`gym`, y `py gui.py`).
