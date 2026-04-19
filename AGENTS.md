# AGENTS

## Reglas persistentes del repositorio

1. [Laminate_Theory_Equivalent_Properties_Updated_v1.m](C:/Users/ManuelGonzalezRecio/Desktop/Teoria_Laminado_App/Laminate_Theory_Equivalent_Properties_Updated_v1.m) es la referencia funcional original y no se modifica ni se rompe.
2. Toda migración o nueva feature debe preservar una arquitectura modular con archivos pequeños y responsabilidades claras.
3. La lógica física y numérica debe vivir separada de la UI, la capa web y el despliegue.
4. La `Dummy` layer puede existir internamente por compatibilidad legado, pero no debe exponerse como concepto obligatorio al usuario final.
5. Toda modificación numérica exige tests y comparación contra referencia MATLAB o contra golden outputs previamente congelados.
6. Toda nueva feature debe preservar el despliegue cloud por Docker y la usabilidad desde navegador móvil.
7. Si hay contradicción entre comentarios y comportamiento efectivo del MATLAB, se prioriza el comportamiento efectivo y se documenta la ambigüedad.
8. Cualquier “corrección física” respecto al legado debe introducirse solo como modo separado y nunca sustituyendo silenciosamente el modo de compatibilidad.
9. Toda salida relevante debe mantener trazabilidad entre inputs, secuencia de capas normalizada, cálculos intermedios y outputs finales.
10. Antes de aceptar cambios grandes, validar como mínimo:
   - `espesor_total`
   - `z`
   - `A`, `B`, `D`
   - propiedades equivalentes
   - three-point bending
   - `EI`
