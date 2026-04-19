# Runbook de despliegue y operacion

## Objetivo

Este documento deja la app lista para operar una instancia oficial publica sin depender del ordenador personal de una sola persona.

## Modelo operativo de la v1

- La app es publica y no requiere login.
- Los calculos se ejecutan en el backend desplegado.
- Los datos de sesion del usuario viven en su navegador:
  - materiales personalizados
  - historial de resultados
  - seleccion del comparador
  - estado de Shuffle
- La exportacion a Excel se genera en el servidor y se descarga al navegador.

## Requisitos previos

- Repositorio accesible desde GitHub.
- Cuenta del equipo en Render.
- Acceso de mantenimiento al repositorio y al servicio de Render.

## Despliegue inicial en Render

1. Sube el repositorio a GitHub.
2. En Render, crea un nuevo `Web Service`.
3. Selecciona el repositorio del proyecto.
4. Usa el `render.yaml` del repo.
5. Define `APP_BASE_URL` con la URL publica final de Render.
6. Render inyecta `PORT` automaticamente al contenedor.
7. Lanza el despliegue.

## Verificacion tras desplegar

Comprueba como minimo:

1. `GET /healthz` devuelve `{"status":"ok"}`.
2. La home carga sin errores visuales.
3. Se puede calcular un laminado desde cero.
4. Se puede guardar un resultado y verlo en `Resultados`.
5. `Shuffle` funciona desde el ultimo calculo.
6. La exportacion a Excel descarga un `.xlsx` valido.
7. La biblioteca de materiales guarda materiales personalizados en el navegador.

## Logs y diagnostico

En Render:

1. Abre el servicio desplegado.
2. Entra en `Logs`.
3. Revisa errores al arrancar, excepciones de FastAPI o fallos de exportacion.

## Redeploy

Opciones recomendadas:

- `Auto deploy` tras merge a la rama principal.
- `Manual deploy` desde Render si se necesita relanzar una build sin cambios de codigo.

## Cambio de materiales base

Los materiales base no se cambian desde la app publica. Para actualizarlos:

1. Edita `app/data/materials.json`.
2. Si el cambio afecta a comportamiento numerico, actualiza tests y referencias.
3. Ejecuta `pytest`.
4. Haz merge y redeploy.

## Transferencia de ownership

Si cambia el equipo responsable:

1. Transfiere acceso al repositorio.
2. Transfiere acceso al servicio en Render.
3. Verifica que la nueva persona sabe:
   - hacer deploy
   - revisar logs
   - cambiar materiales base
   - validar `healthz`, calculo y exportacion

## Siguiente escalon futuro

Esta v1 no usa base de datos ni autenticacion. Si el proyecto crece, los siguientes pasos naturales serian:

- autenticacion por usuario
- persistencia cloud de resultados y materiales
- panel de administracion para materiales base
