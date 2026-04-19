from __future__ import annotations

from app.domain.laminate import BuiltLaminate, LaminateDefinition, ResolvedLayer
from app.domain.materials import build_material_catalog


def build_laminate(definition: LaminateDefinition) -> BuiltLaminate:
    catalog = build_material_catalog(
        [
            {
                "id": material.id,
                "name": material.name,
                "material_category": material.material_category,
                "e1_pa": material.e1_pa,
                "e2_pa": material.e2_pa,
                "g12_pa": material.g12_pa,
                "poisson_input": material.poisson_input,
                "strength_x": material.strength_x,
                "strength_x_compression": material.strength_x_compression,
                "strength_y": material.strength_y,
                "strength_y_compression": material.strength_y_compression,
                "strength_s": material.strength_s,
                "thickness_mm": material.thickness_mm,
                "user_selectable": material.user_selectable,
                "notes": material.notes,
            }
            for material in definition.custom_materials
        ]
    )
    warnings: list[str] = []
    resolved_layers: list[ResolvedLayer] = []

    for index, layer in enumerate(definition.layers, start=1):
        material = catalog[layer.material_id]
        resolved_layers.append(
            ResolvedLayer(
                index=index,
                material=material,
                theta_deg=layer.theta_deg,
                source="user",
            )
        )

    dummy_inserted = False
    if definition.insert_dummy_layer_for_odd_compatibility and len(resolved_layers) % 2 == 1:
        dummy_inserted = True
        resolved_layers.append(
            ResolvedLayer(
                index=len(resolved_layers) + 1,
                material=catalog["Dummy"],
                theta_deg=0.0,
                source="compatibility-auto-dummy",
            )
        )
        warnings.append(
            "Se ha anadido una Dummy interna para preservar la compatibilidad con el caso legado de numero impar de capas."
        )

    core_material = catalog[definition.core_material_id]
    if core_material.id not in [layer.material.id for layer in resolved_layers]:
        warnings.append(
            "El bloque de flexion a tres puntos seguira usando el core seleccionado aunque no forme parte del apilado visible."
        )

    if definition.is_symmetric:
        warnings.append(
            "El modo simetrico solo refleja las posiciones z del legado; no reconstruye automaticamente un apilado simetrico."
        )

    return BuiltLaminate(
        layers=resolved_layers,
        is_symmetric=definition.is_symmetric,
        core_material=core_material,
        compatibility_mode=definition.compatibility_mode,
        dummy_inserted=dummy_inserted,
        warnings=warnings,
    )
