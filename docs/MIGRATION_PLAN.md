# MIGRATION_PLAN

## Objetivo

Migrar el cálculo legado de teoría del laminado desde un script MATLAB monolítico a una aplicación web en Python con FastAPI, modular, validable y desplegable por Docker, preservando primero la equivalencia funcional y dejando preparada una evolución futura para comparativas y barridos.

## Principios de migración

1. El archivo MATLAB original no se toca ni se sobrescribe.
2. El primer contrato funcional es el comportamiento efectivo del MATLAB actual, incluidas sus peculiaridades.
3. La lógica de dominio y cálculo queda separada de la UI y de la capa web.
4. Toda desviación numérica se mide, se documenta y se justifica.
5. La primera web debe ser simple, server-rendered y mantenible.

## Decisiones de arquitectura

### Backend

- Framework: FastAPI.
- Exposición dual:
  - HTML server-rendered para usuarios finales.
  - API JSON interna para futuras comparativas, automatización y barridos.

### Frontend

- Plantillas Jinja2.
- CSS propio ligero y responsive.
- JavaScript mínimo para añadir o eliminar capas y alternar modo básico/avanzado.
- Sin SPA ni dependencia de un frontend build complejo.

### Núcleo de dominio

Separación por responsabilidades:

- `app/domain`
  - materiales, unidades, modelos internos del laminado
- `app/services`
  - construcción del stacking sequence
  - validación
  - cálculo CLT legado
  - propiedades equivalentes
  - flexión a tres puntos
  - compatibilidad legado
- `app/schemas`
  - contratos de entrada y salida
- `app/web`
  - rutas, formularios, plantillas y estáticos

### Datos y configuración

- Catálogo de materiales estructurado y tipado.
- Constantes del bloque experimental convertidas a configuración con defaults equivalentes al MATLAB.
- Casos de referencia en JSON para trazabilidad.

### Despliegue

- Una sola imagen Docker.
- Preparado para Render con `render.yaml`.
- Portable a otros proveedores gracias a FastAPI + Docker + variables de entorno mínimas.

## Fases del proyecto

### Fase 1. Análisis y congelación de referencia

- Analizar el MATLAB línea por línea.
- Documentar inputs, outputs, unidades, ambigüedades y bugs heredados.
- Capturar al menos el caso base como referencia real MATLAB.
- Crear `AGENTS.md`.

### Fase 2. Motor Python modular

- Modelos tipados.
- Catálogo de materiales.
- Validadores.
- Constructor de laminado.
- Núcleo CLT con modo compatibilidad legado.
- Bloque de equivalent properties.
- Bloque de three-point bending.

### Fase 3. Validación y compatibilidad

- Casos de prueba unitarios e integración.
- Casos golden si MATLAB está disponible.
- Reporte de diferencias numéricas y tolerancias.
- Aislar quirks en la capa de compatibilidad.

### Fase 4. Interfaz web

- Formulario guiado.
- Modo básico y modo avanzado.
- Resumen del stacking sequence realmente usado.
- Resultados y avisos claros.

### Fase 5. Despliegue y extensibilidad

- Dockerfile, `.dockerignore`, `render.yaml`.
- README con desarrollo y despliegue.
- Preparar API y estructura para comparativas y barridos.

## Riesgos

### Riesgos funcionales

- Reproducir demasiado “bien” la física estándar y romper la equivalencia con el MATLAB real.
- Corregir implícitamente bugs heredados que hoy afectan a resultados.
- Interpretar mal el papel del `Honeycomb` y de la `Dummy`.

### Riesgos técnicos

- Diferencias numéricas MATLAB vs Python en trigonometría, inversión de matrices y formato.
- Falta de golden cases si el wrapper MATLAB no cubre varios escenarios.
- Complejidad innecesaria en frontend si se cae en una SPA.

### Riesgos de producto

- Exponer a usuario no experto conceptos internos como la `Dummy`.
- Formularios ambiguos que no reflejen el stacking real usado por el motor.
- Mezcla de unidades sin visualización clara.

## Orden de implementación

1. Documentación obligatoria y captura del caso base.
2. Estructura del repositorio.
3. Catálogo de materiales y esquemas de entrada.
4. Normalización y validadores.
5. Cálculo legado-compatible de `z`, `Q`, `A`, `B`, `D`.
6. Equivalent properties y three-point bending.
7. Casos de referencia y tests.
8. UI web.
9. Docker y despliegue.

## Estrategia de validación

- Mantener un modo explícito `legacy_compatible`.
- Comparar contra MATLAB:
  - `espesor_total`
  - `z`
  - `A`, `B`, `D`
  - `A1`, `D1`
  - propiedades equivalentes
  - `G12G`
  - salidas de flexión
- Usar tolerancias estrictas por defecto.
- Si aparecen desviaciones:
  - registrar input
  - registrar output Python
  - registrar output MATLAB
  - clasificar si es error de migración o diferencia esperable de entorno

## Qué se implementa ahora

- Documentación de comportamiento actual.
- Arquitectura base.
- Primer motor Python modular con modo de compatibilidad legado.
- Caso base golden capturado desde MATLAB.
- UI inicial responsive.
- Docker y guías de despliegue inicial.

## Qué se deja preparado para futuro

- Comparación entre múltiples laminados.
- Barridos paramétricos.
- Exportación estructurada de resultados.
- Gráficas.
- Posible segundo modo “físicamente corregido” separado del modo legado.

Ese segundo modo no debe activarse por defecto ni mezclarse con la validación de equivalencia del primer entregable.
