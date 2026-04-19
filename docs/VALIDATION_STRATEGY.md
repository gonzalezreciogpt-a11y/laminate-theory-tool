# VALIDATION_STRATEGY

## Objetivo

Validar que la migración Python reproduce el comportamiento funcional del MATLAB actual antes de permitir cambios de formulación, UX avanzada o nuevas capacidades.

## Outputs críticos a comparar

Para cada caso validado contra MATLAB, como mínimo se deben comparar:

- `espesor_total`
- `z`
- `A`
- `B`
- `D`
- `A1`
- `D1`
- `E11`
- `E22`
- `G122`
- `nuu12`
- `nuu21`
- `G12G`
- `EI_ensayo`
- `E_fibra_ensayo`
- `EI_theory`
- `Elastic_gradient_Theory`

También conviene conservar:

- `fiber_assignment` resuelto
- `theta`
- `es_simetrico`
- materiales y espesores usados
- warnings de compatibilidad

## Tolerancias numéricas

Tolerancias por defecto propuestas:

- escalares principales:
  - `rtol = 1e-9`
  - `atol = 1e-6`
- matrices `A`, `B`, `D`, `A1`, `D1`:
  - `rtol = 1e-9`
  - `atol = 1e-3`
- posiciones `z` en mm:
  - `rtol = 0`
  - `atol = 1e-9`

Justificación:

- MATLAB y NumPy deberían coincidir muy de cerca en estas operaciones si la implementación replica las mismas fórmulas.
- Si alguna tolerancia debe relajarse, se debe documentar el motivo exacto y el caso afectado.

## Golden cases

### Casos mínimos requeridos

1. Caso base del script actual.
2. Caso con número par de capas.
3. Caso con número impar de capas.
4. Caso simétrico.
5. Caso no simétrico, si el código se confirma operativo.
6. Casos con diferentes orientaciones.

### Estrategia

- Guardar inputs en JSON estructurado.
- Guardar outputs golden en JSON estructurado.
- Mantener el caso base capturado desde el script original sin modificar.
- Los casos adicionales deben generarse con wrappers MATLAB de compatibilidad o, si no es posible aún, dejarse como manifiestos listos para captura posterior.

## Estrategia cuando MATLAB está disponible

Pasos:

1. Ejecutar el script original para congelar el caso base.
2. Usar un wrapper MATLAB de validación, sin modificar el script original, para parametrizar casos adicionales.
3. Exportar resultados a JSON.
4. Comparar en tests automatizados Python vs golden MATLAB.

Implementación actual en el repo:

- wrapper MATLAB: `matlab_reference/legacy_reference_runner.m`
- entrypoint JSON -> JSON: `matlab_reference/run_case_from_json.m`
- generador desde Python: `tools/generate_matlab_goldens.py`
- goldens ya congelados:
  - `base_case_golden.json`
  - `even_case_golden.json`
  - `odd_case_golden.json`
  - `nonsymmetric_case_golden.json`

## Estrategia cuando MATLAB u Octave no están disponibles

Si el entorno no puede ejecutar MATLAB u Octave:

- no inventar golden outputs
- crear manifiestos de casos de prueba
- dejar un runner preparado para volcar resultados reales cuando haya acceso a MATLAB
- ejecutar igualmente:
  - tests de validación de inputs
  - tests de consistencia interna
  - tests de unidades
  - tests de simetría y dummy

## Caso base ya congelado

Referencia capturada desde MATLAB para:

- `fiber_assignment = [1, 2, 1, 4]`
- `theta = [45, 0, 90, 0]`
- `es_simetrico = true`

Valores críticos:

- `espesor_total = 1.16001`
- `z = [0.365005, 0.000005, -0.000005, -0.365005, -0.580005]`
- `E11 = 6.6152367046165588e+10`
- `E22 = 3.6271049843420486e+10`
- `G122 = 1.3522739770461451e+10`
- `nuu12 = 0.17154864194261055`
- `nuu21 = 0.31287621331747534`
- `G12G = 3.3075852764555145e+10`
- `EI_ensayo = 4297.52675503191`
- `E_fibra_ensayo = 60175.875927739195`
- `EI_theory = 4724.344480352438`
- `Elastic_gradient_Theory = 3543.2583602643276`

## Checklist de validación antes de aceptar la migración

1. El script MATLAB original sigue intacto.
2. El caso base coincide con MATLAB dentro de tolerancia.
3. Los materiales y espesores coinciden exactamente con el catálogo legado.
4. El cálculo de `z` replica la convención efectiva del MATLAB.
5. `A`, `B` y `D` coinciden con la formulación legado-compatible.
6. `G12G` preserva su dependencia actual del último `nu12` calculado, si el modo es legado.
7. El bloque de three-point bending reproduce los defaults y constantes actuales.
8. Toda desviación conocida está documentada.
9. Los tests cubren casos pares, impares, simétricos y no simétricos.
10. La UI muestra el stacking sequence realmente usado y sus unidades.

## Criterio de aceptación práctico

La migración se considera aceptable en esta fase si:

- el motor Python reproduce el caso base golden
- la arquitectura permite ampliar golden cases sin rehacer el sistema
- los quirks del MATLAB están encapsulados en una capa explícita de compatibilidad

No se considera aceptable si el sistema solo “se parece” al MATLAB en outputs finales sin trazabilidad intermedia.
