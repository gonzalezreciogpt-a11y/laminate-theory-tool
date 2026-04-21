from __future__ import annotations

from app.domain.materials import RESERVED_MATERIAL_IDS, build_material_catalog, load_material_catalog
from app.schemas.inputs import LaminateRequestModel

ALLOWED_ORIENTATIONS = {-90.0, -45.0, 0.0, 45.0, 90.0}


def _normalize_orientation(theta_deg: float) -> float:
    rounded = round(float(theta_deg), 6)
    if rounded == -0.0:
        return 0.0
    return rounded


def _validate_skin_layers(
    *,
    layers,
    catalog,
    compatibility_mode: str,
    side_label: str,
) -> bool:
    seen_dummy = False
    for index, layer in enumerate(layers, start=1):
        if layer.material_id not in catalog:
            raise ValueError(f"Material desconocido '{layer.material_id}' en la {side_label} {index}.")
        material = catalog[layer.material_id]
        if material.material_category == "core":
            raise ValueError(
                f"La {side_label} {index} usa el core '{layer.material_id}'. Las capas deben usar materiales de fibra."
            )
        theta_deg = _normalize_orientation(layer.theta_deg)
        if theta_deg not in ALLOWED_ORIENTATIONS:
            raise ValueError(
                f"La {side_label} {index} usa una orientacion no permitida. Solo se admiten -90, -45, 0, 45 y 90 grados."
            )
        if material.material_category == "fiber":
            if material.fiber_family == "ud" and theta_deg != 0.0:
                raise ValueError(
                    f"La {side_label} {index} usa el material UD '{layer.material_id}' con una orientacion no valida. Las fibras UD solo admiten 0 grados."
                )
            if material.fiber_family == "twill" and theta_deg not in {-90.0, -45.0, 45.0, 90.0}:
                raise ValueError(
                    f"La {side_label} {index} usa el material twill '{layer.material_id}' con una orientacion no valida. Las fibras twill solo admiten +-45 o +-90 grados."
                )
        if layer.material_id == "Dummy":
            if compatibility_mode != "legacy":
                raise ValueError("La Dummy solo se admite en modo legado.")
            seen_dummy = True
    return seen_dummy


def validate_request(request: LaminateRequestModel) -> list[str]:
    base_catalog = load_material_catalog()
    warnings: list[str] = []

    if request.compatibility_mode not in {"legacy", "physical"}:
        raise ValueError("Modo de calculo desconocido.")

    custom_material_ids: set[str] = set()
    for material in request.custom_materials:
        if material.id in RESERVED_MATERIAL_IDS:
            raise ValueError(f"El identificador de material '{material.id}' esta reservado.")
        if material.id in custom_material_ids:
            raise ValueError(f"El identificador personalizado '{material.id}' esta duplicado.")
        if material.material_category not in {"fiber", "core", "compatibility"}:
            raise ValueError(f"El material personalizado '{material.id}' usa una categoria desconocida.")
        if material.material_category == "fiber" and material.fiber_family not in {"twill", "ud"}:
            raise ValueError(
                f"El material personalizado '{material.id}' debe indicar si es fibra twill o UD."
            )
        if material.thickness_mm <= 0 or material.e1_pa <= 0 or material.e2_pa <= 0 or material.g12_pa <= 0:
            raise ValueError(
                f"El material personalizado '{material.id}' debe usar rigideces y espesor positivos."
            )
        custom_material_ids.add(material.id)

    catalog = build_material_catalog([material.model_dump() for material in request.custom_materials])

    if request.core_material_id not in catalog:
        raise ValueError(f"Core desconocido '{request.core_material_id}'.")
    if catalog[request.core_material_id].material_category != "core":
        raise ValueError("El material seleccionado como core debe pertenecer a la categoria core.")

    if request.three_point_bending.span_m <= 0 or request.three_point_bending.width_m <= 0:
        raise ValueError("Las dimensiones del ensayo a tres puntos deben ser positivas.")

    if request.compatibility_mode == "legacy" and request.bottom_layers:
        raise ValueError("El modo legado no admite capas inferiores definidas de forma explicita.")
    if request.compatibility_mode == "physical" and request.is_symmetric and request.bottom_layers:
        raise ValueError(
            "No se deben definir capas inferiores explicitas cuando el laminado es simetrico."
        )

    seen_dummy = _validate_skin_layers(
        layers=request.layers,
        catalog=catalog,
        compatibility_mode=request.compatibility_mode,
        side_label="capa superior",
    )
    if request.bottom_layers:
        seen_dummy = (
            _validate_skin_layers(
                layers=request.bottom_layers,
                catalog=catalog,
                compatibility_mode=request.compatibility_mode,
                side_label="capa inferior",
            )
            or seen_dummy
        )

    if request.compatibility_mode == "legacy" and seen_dummy:
        warnings.append(
            "La peticion incluye la Dummy legada de forma explicita. Utilizala solo para estudios de compatibilidad."
        )

    if (
        request.compatibility_mode == "legacy"
        and request.insert_dummy_layer_for_odd_compatibility
        and len(request.layers) % 2 == 1
    ):
        warnings.append(
            "Se ha detectado un numero impar de capas. Se anadira una Dummy interna para mantener la compatibilidad legado."
        )

    return warnings
