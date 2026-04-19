# Herramienta de laminados

Aplicacion web modular para teoria del laminado, migrada desde MATLAB y desplegable como servicio publico por Docker.

## Que conserva del legado

- El MATLAB original sigue intacto en [Laminate_Theory_Equivalent_Properties_Updated_v1.m](./Laminate_Theory_Equivalent_Properties_Updated_v1.m).
- El modo `legacy` replica el comportamiento efectivo validado del script, incluyendo sus peculiaridades documentadas.
- La `Dummy` se mantiene solo como mecanismo interno de compatibilidad cuando hace falta.

## Modelo de uso de la v1 publica

- La app puede desplegarse de forma publica en la nube.
- Los calculos se ejecutan en el backend desplegado.
- Cada navegador conserva sus propios datos locales:
  - materiales personalizados
  - historial de resultados
  - estado de Shuffle
  - seleccion temporal del comparador
- Si el usuario limpia el navegador o cambia de dispositivo, pierde esa biblioteca local.
- La exportacion a Excel se genera en el servidor y se descarga al navegador del usuario.

## Estructura principal

```text
app/
  domain/
  data/
  schemas/
  services/
  web/
docs/
examples/reference_cases/
tests/
```

## Variables de entorno

La app soporta estas variables:

- `APP_ENV`: `development` o `production`
- `PORT`: puerto de escucha del servidor
- `APP_BASE_URL`: URL publica de la instancia desplegada
- `LOG_LEVEL`: nivel de logs para Uvicorn

Ejemplo local en `.env.example`:

```env
APP_ENV=development
PORT=8000
APP_BASE_URL=http://127.0.0.1:8000
LOG_LEVEL=info
```

## Desarrollo local

1. Crea un entorno virtual.
2. Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

3. Lanza la app:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Abre:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/healthz`
- `http://127.0.0.1:8000/api/materials`

## Tests

```bash
python -m pytest
```

## Regenerar goldens desde MATLAB

Si MATLAB esta disponible, los casos de referencia adicionales pueden regenerarse con:

```bash
python tools/generate_matlab_goldens.py
```

Esto ejecuta los wrappers separados en:

- `matlab_reference/legacy_reference_runner.m`
- `matlab_reference/run_case_from_json.m`

## Docker

Build local:

```bash
docker build -t laminate-theory-tool .
```

Arranque local:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 -e APP_ENV=production laminate-theory-tool
```

Verificaciones minimas:

1. `GET /healthz`
2. calculo desde la UI
3. exportacion a Excel

## Despliegue en Render

El repositorio ya incluye:

- `Dockerfile`
- `.dockerignore`
- `render.yaml`

Pasos:

1. Sube el repo a GitHub.
2. Crea un nuevo `Web Service` en Render.
3. Usa `render.yaml`.
4. Define `APP_BASE_URL` con la URL publica final.
5. Render inyecta `PORT` automaticamente; no hace falta fijarlo a mano.
6. Despliega y verifica `GET /healthz`.

## Operacion del equipo

Para despliegue, verificacion, logs, redeploy y transferencia de ownership, usa:

- [docs/DEPLOYMENT_RUNBOOK.md](docs/DEPLOYMENT_RUNBOOK.md)

## Documentacion clave

- [docs/CURRENT_MATLAB_BEHAVIOR.md](docs/CURRENT_MATLAB_BEHAVIOR.md)
- [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md)
- [docs/VALIDATION_STRATEGY.md](docs/VALIDATION_STRATEGY.md)
- [docs/DEPLOYMENT_RUNBOOK.md](docs/DEPLOYMENT_RUNBOOK.md)
- [AGENTS.md](AGENTS.md)

## Notas de compatibilidad

- La UI no expone la `Dummy` como material normal, pero el motor puede insertarla internamente para compatibilidad.
- El bloque de three-point bending mantiene las convenciones del MATLAB actual.
- `G12G` conserva la dependencia legado del ultimo `nu12` de capa procesado.
