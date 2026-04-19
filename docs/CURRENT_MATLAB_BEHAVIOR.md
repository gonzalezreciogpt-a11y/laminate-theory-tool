# CURRENT_MATLAB_BEHAVIOR

## Alcance y fuente de verdad

Este documento describe el comportamiento efectivo de [Laminate_Theory_Equivalent_Properties_Updated_v1.m](../Laminate_Theory_Equivalent_Properties_Updated_v1.m) tal y como está implementado hoy. La referencia funcional no son los comentarios ni los nombres de variables, sino lo que realmente ejecuta el código.

Archivo analizado: [Laminate_Theory_Equivalent_Properties_Updated_v1.m](C:/Users/ManuelGonzalezRecio/Desktop/Teoria_Laminado_App/Laminate_Theory_Equivalent_Properties_Updated_v1.m)

Caso base ejecutado en MATLAB R2024b el 2026-04-18:

- `fiber_assignment = [1, 2, 1, 4]`
- `theta = [45, 0, 90, 0]`
- `es_simetrico = true`

## Inputs actuales del script

El script no expone una interfaz formal; los inputs son variables hardcodeadas dentro del propio archivo:

- `fiber_types`
  - Tabla celular MATLAB con 11 columnas.
  - Estructura por fila:
    - nombre
    - `E1`
    - `E2`
    - `G12`
    - coeficiente de Poisson almacenado en columna 5
    - `X`
    - `X_`
    - `Y`
    - `Y_`
    - `S`
    - espesor en mm
- `fiber_assignment`
  - Vector de índices enteros hacia `fiber_types`.
  - Define cuántas capas se procesan y qué material usa cada posición.
- `theta`
  - Vector de ángulos en grados.
  - Debe tener la misma longitud que `fiber_assignment`.
- `es_simetrico`
  - Booleano que cambia el cálculo de `z`.

No existe validación explícita de dimensiones, rangos, consistencia física o unidades.

## Catálogo actual de materiales y propiedades

Catálogo tal como aparece en MATLAB:

| Índice | Nombre | E1 (Pa) | E2 (Pa) | G12 (Pa) | Columna 5 | X | X_ | Y | Y_ | S | Espesor (mm) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `RC416T` | `62450e6` | `61200e6` | `3710e6` | `0.037` | 593 | 489.6 | 593.3 | 489.6 | 68.2 | 0.43 |
| 2 | `UD` | `130330e6` | `7220e6` | `4230e6` | `0.337` | 1433.6 | 1003.3 | 32.5 | 108.3 | 76.1 | 0.30 |
| 3 | `Honeycomb` | `1e6` | `1e6` | `1e6` | `0.5` | 10 | 10 | 10 | 10 | 10 | 20.0 |
| 4 | `Dummy` | `1e-5` | `1e-5` | `1e-5` | `1e-5` | `1e-5` | `1e-5` | `1e-5` | `1e-5` | `1e-5` | `1e-5` |

Observaciones:

- Las resistencias `X`, `X_`, `Y`, `Y_`, `S` no se usan en ningún cálculo del script.
- El `Honeycomb` existe en el catálogo, pero en el caso base no aparece en `fiber_assignment`.
- La `Dummy` sí aparece en el caso base y afecta a resultados porque se suma al espesor total y participa en `A`, `B`, `D` aunque con rigidez casi nula.

## Interpretación real de `fiber_assignment`, `theta`, `es_simetrico`, `core` y `dummy`

### `fiber_assignment`

Interpretación efectiva:

- Cada elemento es un índice de la tabla `fiber_types`.
- El orden del vector sí importa.
- El número de capas `num_capas` es exactamente `length(fiber_assignment)`.
- No existe tratamiento especial automático del `Honeycomb`; solo participa si su índice aparece en `fiber_assignment`.

Ambigüedad detectada:

- El comentario dice `Aquí 3 representa la capa central de honeycomb`, pero el caso base usa `[1,2,1,4]`, es decir, no incluye el índice 3 y sí incluye `Dummy`.

### `theta`

Interpretación efectiva:

- Un ángulo por posición de `fiber_assignment`.
- El script usa `cosd` y `sind` directamente con cada valor.
- No existe normalización de ángulos ni validación.

Ambigüedad detectada:

- El comentario indica que se añade una orientación ficticia al core, pero en el caso base el último elemento corresponde a `Dummy`, no a `Honeycomb`.

### `es_simetrico`

Interpretación efectiva:

- No fuerza una simetrización automática del stacking sequence.
- Solo cambia la forma de calcular `z`.
- Si el usuario introduce una secuencia no simétrica con `es_simetrico = true`, el código igualmente reflejará posiciones `z` de forma simétrica, aunque los materiales y orientaciones originales no se dupliquen ni reordenen.

### `core`

Interpretación efectiva:

- La variable `capa_central` se inicializa como el espesor en mm del material cuyo nombre es `Honeycomb`.
- Ese valor se usa después en el bloque final de three-point bending, independientemente de que el `Honeycomb` forme o no parte del laminado real.
- En el caso base, el `core` del bloque final es siempre `20.0 mm`, aunque el laminado calculado no lo contenga en `fiber_assignment`.

### `dummy`

Interpretación efectiva:

- Es una capa más del catálogo, con rigidez y espesor casi nulos.
- Sí afecta a:
  - `num_capas`
  - `espesor_total`
  - `z`
  - el bucle de rigidez
  - el último `nu12` disponible, que luego se reutiliza en `G12G`
- El comentario dice que se usa cuando el número de capas es impar, pero el script no la inserta automáticamente; solo existe si el usuario la incluye manualmente en `fiber_assignment`.

## Orden físico real de las capas según el código

El código no reconstruye ni refleja materiales. El orden real procesado es exactamente el orden del vector `fiber_assignment`.

Caso base:

1. `RC416T` a `45°`
2. `UD` a `0°`
3. `RC416T` a `90°`
4. `Dummy` a `0°`

Si `es_simetrico = true`, el script solo fuerza simetría en `z`, no en la secuencia de materiales.

## Cómo se calcula el espesor total

`espesor_total` se calcula como la suma simple de la columna 11 de cada fila apuntada por `fiber_assignment`.

Fórmula efectiva:

```matlab
espesor_total = 0;
for i = 1:num_capas
    fiber_index = fiber_assignment(i);
    h = fiber_types{fiber_index, 11};
    espesor_total = espesor_total + h;
end
```

Caso base:

- `0.43 + 0.30 + 0.43 + 0.00001 = 1.16001 mm`
- MATLAB imprime `1.16 mm` por formato de salida.

Importante:

- El espesor del `Honeycomb` no entra en `espesor_total` salvo que su índice esté presente en `fiber_assignment`.
- El bloque final de flexión sí usa `capa_central = 20 mm`, aunque ese espesor no forme parte de `espesor_total`.

## Cómo se calculan las posiciones `z`

### Forma del vector

- `z = zeros(num_capas + 1, 1)`
- El script usa `z(i)` para cada capa y deja `z(num_capas + 1)` como límite inferior.

### Caso `es_simetrico = true`

Algoritmo efectivo:

1. `mitad_thickness = espesor_total / 2`
2. Recorre solo `1:ceil(num_capas/2)`
3. Asigna:

```matlab
z(i) = mitad_thickness - acumulado_thickness + h / 2;
```

4. Si el número de capas es impar:
   - sobrescribe `capa_central` con un índice entero
   - calcula una capa central especial
5. Refleja las posiciones restantes con:

```matlab
z(i) = -z(num_capas + 1 - i);
```

6. Fija:

```matlab
z(num_capas + 1) = -mitad_thickness;
```

Caso base:

- `z = [0.365005, 0.000005, -0.000005, -0.365005, -0.580005]`

### Caso `es_simetrico = false`

Algoritmo efectivo:

```matlab
z(i) = acumulado_thickness - h / 2 - espesor_total / 2;
z(num_capas + 1) = -espesor_total / 2;
```

### Observación crítica

El código usa `z` como si fuesen centros de capa al calcularlos, pero luego usa `z(i)` y `z(i+1)` dentro de las integrales de `B` y `D` como si fuesen coordenadas de interfaces. Esta mezcla es una de las principales peculiaridades del comportamiento legado y debe preservarse en modo compatibilidad.

En el caso impar simétrico aparece otra rareza adicional:

- la rama “capa central” usa `capa_central = ceil(num_capas / 2) + 1`
- después el bucle de reflexión vuelve a escribir esa misma posición
- por tanto, el cálculo especial de `z` para la supuesta capa central queda efectivamente sobrescrito

## Cómo se construyen `A`, `B` y `D`

Inicialización:

```matlab
A = zeros(3, 3);
B = zeros(3, 3);
D = zeros(3, 3);
AA = zeros(3, 3)
```

`AA` no se usa y además se imprime por falta de `;`.

Por cada capa:

1. Lee `E1`, `E2`, `G12`, columna 5 y `h`.
2. Asigna:

```matlab
nu21 = fiber_types{fiber_index, 5};
nu12 = (E2 / E1) * nu21;
```

3. Construye la matriz local `Q`.
4. Aplica una transformación a global que intenta producir `QXY{i}`.
5. Acumula:

```matlab
A = A + QXY{i} * h;
B = B + QXY{i} * (z(i)^2 - z(i+1)^2) / 2.0;
D = D + QXY{i} * ((z(i)^3 - z(i+1)^3) / 3);
```

### Fórmulas efectivas de transformación

```matlab
Qxx = Q11*m^4 + 2*(Q12 + 2*QSS)*n^2*m^2 + Q22*n^4
Qyx = (Q11 + Q22 - 4*QSS)*n^2*m^2 + Q12*(n^4 + m^4)
Qyy = Q11*n^4 + 2*(Q12 + 2*QSS)*n^2*m^2 + Q22*m^4
Qxs = (Q11 - Q12 - 2*QSS)*n*m^3 + (Q12 - Q22 + 2*QSS)*n*m^3
Qys = (Q11 - Q12 - 2*QSS)*m*n^3 + (Q12 - Q22 + 2*QSS)*m*n^3
Qss = (Q11 + Q22 - 2*Q12 - 2*QSS)*n^2*m^2 + QSS*(n^4 + m^4)
```

Observación crítica:

- `Qxs` y `Qys` no usan la forma estándar de CLT para `Q16` y `Q26`.
- En ambas ecuaciones los dos términos comparten la misma potencia, lo que altera el comportamiento respecto a la formulación clásica.

Caso base MATLAB:

- `A`

```text
[[8.1090932831061249e+10, 1.3911995558156576e+10, 1.3455551942630839e+08],
 [1.3911995558156576e+10, 4.4462320630708153e+10, 1.3455551942630839e+08],
 [1.3455551942630839e+08, 1.3455551942630839e+08, 1.5687031952548189e+10]]
```

- `B`

```text
[[-1.6976305832539849e+09, 1.7393204674475107e+09, 2.0844942096762605e+07],
 [1.7393204674475107e+09, -1.7810103516410356e+09, 2.0844942096762605e+07],
 [2.0844942096762605e+07, 2.0844942096762605e+07, 1.7393204674475098e+09]]
```

- `D`

```text
[[1.57363786540322e+09, 4.967495893083269e+08, 5.0723387276376886e+06],
 [4.967495893083269e+08, 1.5939272203137603e+09, 5.0723387276376886e+06],
 [5.0723387276376886e+06, 5.0723387276376886e+06, 5.4351647677507973e+08]]
```

## Cómo se obtienen las propiedades equivalentes

El script calcula:

```matlab
A1 = A / espesor_total;
a = inv(A1);
D1 = D / espesor_total;
d = inv(D1);

E11 = 1 / a(1, 1);
E22 = 1 / a(2, 2);
G122 = 1 / a(3, 3);
E111 = 1 / d(1, 1);
nuu21 = -a(2, 1) / a(1, 1);
nuu12 = -a(1, 2) / a(2, 2);
```

Observaciones:

- `E111` se calcula pero no se usa ni se imprime.
- `A1` y `D1` dividen por `espesor_total` expresado en mm, no en metros.

Caso base MATLAB:

- `E11 = 6.6152367046165588e+10 Pa`
- `E22 = 3.6271049843420486e+10 Pa`
- `G122 = 1.3522739770461451e+10 Pa`
- `nuu12 = 0.17154864194261055`
- `nuu21 = 0.31287621331747534`

### Cálculo de `G12G`

El script usa:

```matlab
G12G = E11 / (2 * (1 + nu12));
```

Observación crítica:

- `nu12` aquí no es `nuu12` del laminado.
- Es el último valor escalar `nu12` calculado dentro del bucle de capas.
- Por tanto, `G12G` depende de la última capa procesada.
- En el caso base, la última capa es `Dummy`, así que `G12G` queda condicionado por su Poisson casi nulo.

Caso base MATLAB:

- `G12G = 3.3075852764555145e+10 Pa`

## Cómo se calcula el bloque final de three-point bending y `EI`

### Variables previas

```matlab
E1_P_Manual = 1 / a(1,1)
th_Fibra = espesor_total
```

### Constantes hardcodeadas

```matlab
Elastic_gradient = 2649
Rigidez_Rig = 14871
```

### Correcciones y resultados

```matlab
Elastic_Gradient_Corregido = (Elastic_gradient * Rigidez_Rig) / (Rigidez_Rig - Elastic_gradient)
EI_ensayo = Elastic_Gradient_Corregido * 1000 * 0.400^3 / 48

E_fibra_ensayo = 400^3 / (24 * 275 * th_Fibra * (th_Fibra + capa_central)^2) * Elastic_Gradient_Corregido

EI_theory = 0.5 * (E1_P_Manual * 0.275 * (th_Fibra * 0.001) * (th_Fibra * 0.001 + capa_central * 0.001)^2)
Elastic_gradient_Theory = 48 * EI_theory / (0.400^3 * 1000)
```

Caso base MATLAB:

- `Elastic_Gradient_Corregido = 3223.145066273215`
- `EI_ensayo = 4297.52675503191`
- `E_fibra_ensayo = 60175.875927739195`
- `EI_theory = 4724.344480352438`
- `Elastic_gradient_Theory = 3543.2583602643276`

### Interpretación real del bloque final

- El ancho `0.275` está hardcodeado.
- La luz `0.400` está hardcodeada.
- Hay una mezcla de unidades en mm y m.
- `capa_central` se usa como espesor de core, aunque ese valor puede no pertenecer al laminado real.

## Constantes hardcodeadas, unidades y conversiones

Constantes hardcodeadas detectadas:

- materiales completos en `fiber_types`
- `Elastic_gradient = 2649`
- `Rigidez_Rig = 14871`
- `0.400` en fórmulas de flexión
- `0.275` en fórmulas de flexión
- factores de conversión `1000` y `0.001`

Unidades observadas:

- `E1`, `E2`, `G12`: Pa
- espesores de capa: mm
- `espesor_total`: mm
- `z`: mm
- `A`, `B`, `D`: combinaciones implícitas derivadas de `Q` en Pa y `z/h` en mm
- `EI_theory`: parece buscar unidades SI, pero depende de conversiones manuales

## Ambigüedades detectadas

1. El comentario del `core` contradice el caso base real.
2. La columna 5 parece etiquetada como `nu12`, pero el código la usa como `nu21`.
3. `z` se calcula como centro de capa pero se integra como si fuesen interfaces.
4. `es_simetrico` no asegura simetría física del stacking sequence, solo de `z`.
5. `capa_central` significa espesor del `Honeycomb` al principio, pero en el caso impar simétrico pasa a ser un índice.

## Bugs aparentes, limitaciones o “ñapas” heredadas que no deben corregirse sin preservar compatibilidad

1. `AA` es una variable muerta que además se imprime.
2. `Qxs` y `Qys` no siguen la formulación estándar de CLT.
3. `B` no se anula en el caso base pese a `es_simetrico = true`, por la forma en que se calculan `z`, materiales y acumulación.
4. `G12G` depende del `nu12` de la última capa procesada, no del laminado.
5. `Dummy` afecta a resultados aunque conceptualmente se quiera “ocultar”.
6. El `Honeycomb` influye en flexión aunque no esté en `fiber_assignment`.
7. En laminado impar simétrico, `capa_central` cambia de espesor a índice, lo que altera `E_fibra_ensayo` y `EI_theory`.
8. No hay control de longitudes entre `fiber_assignment` y `theta`.
9. No hay control de materiales inválidos ni de capas vacías.

## Congelación de referencia del caso base

Outputs críticos capturados desde MATLAB para el caso base:

- `espesor_total = 1.16001 mm`
- `z = [0.365005, 0.000005, -0.000005, -0.365005, -0.580005]`
- `E11 = 66.15236704616559 GPa`
- `E22 = 36.27104984342049 GPa`
- `G122 = 13.522739770461451 GPa`
- `nuu12 = 0.17154864194261055`
- `nuu21 = 0.31287621331747534`
- `G12G = 33.075852764555145 GPa`
- `EI_ensayo = 4297.52675503191`
- `E_fibra_ensayo = 60175.875927739195`
- `EI_theory = 4724.344480352438`
- `Elastic_gradient_Theory = 3543.2583602643276`

La migración debe reproducir estos valores en modo compatibilidad legado antes de considerar cambios de formulación o UX avanzada.
