from __future__ import annotations

import json

from starlette.datastructures import FormData

from app.domain.materials import build_material_catalog
from app.schemas.inputs import (
    CustomMaterialModel,
    LaminateRequestModel,
    LayerInputModel,
    ThreePointBendingConfigModel,
)

MM_TO_M = 0.001


def _parse_float_or_default(form: FormData, key: str, default: float) -> float:
    raw_value = str(form.get(key, "")).strip()
    if raw_value == "":
        return default
    return float(raw_value)


def _millimeters_to_meters(value_mm: float) -> float:
    return value_mm * MM_TO_M


def build_request_from_form(form: FormData) -> LaminateRequestModel:
    material_ids = form.getlist("material_id")
    theta_values = form.getlist("theta_deg")
    bottom_material_ids = form.getlist("bottom_material_id")
    bottom_theta_values = form.getlist("bottom_theta_deg")
    layers: list[LayerInputModel] = []
    bottom_layers: list[LayerInputModel] = []

    for material_id, theta_value in zip(material_ids, theta_values, strict=False):
        material_id = material_id.strip()
        theta_value = theta_value.strip()
        if not material_id or theta_value == "":
            continue
        layers.append(LayerInputModel(material_id=material_id, theta_deg=float(theta_value)))

    for material_id, theta_value in zip(bottom_material_ids, bottom_theta_values, strict=False):
        material_id = material_id.strip()
        theta_value = theta_value.strip()
        if not material_id or theta_value == "":
            continue
        bottom_layers.append(LayerInputModel(material_id=material_id, theta_deg=float(theta_value)))

    custom_materials_json = str(form.get("custom_materials_json", "[]"))
    custom_materials_payload = json.loads(custom_materials_json)
    core_material_id = str(form.get("core_material_id", "Honeycomb"))
    core_thickness_override_raw = str(form.get("core_thickness_mm_override", "")).strip()

    if core_thickness_override_raw:
        core_catalog = build_material_catalog(custom_materials_payload)
        if core_material_id in core_catalog:
            core_material = core_catalog[core_material_id]
            if core_material.material_category == "core":
                override_payload = {
                    "id": core_material.id,
                    "name": core_material.name,
                    "material_category": core_material.material_category,
                    "fiber_family": core_material.fiber_family,
                    "e1_pa": core_material.e1_pa,
                    "e2_pa": core_material.e2_pa,
                    "g12_pa": core_material.g12_pa,
                    "poisson_input": core_material.poisson_input,
                    "strength_x": core_material.strength_x,
                    "strength_x_compression": core_material.strength_x_compression,
                    "strength_y": core_material.strength_y,
                    "strength_y_compression": core_material.strength_y_compression,
                    "strength_s": core_material.strength_s,
                    "thickness_mm": float(core_thickness_override_raw),
                    "user_selectable": core_material.user_selectable,
                    "notes": core_material.notes,
                }
                custom_materials_payload = [
                    material
                    for material in custom_materials_payload
                    if str(material.get("id")) != core_material_id
                ]
                custom_materials_payload.append(override_payload)

    span_mm = _parse_float_or_default(form, "span_mm", 400.0)
    width_mm = _parse_float_or_default(form, "width_mm", 275.0)

    return LaminateRequestModel(
        layers=layers,
        bottom_layers=bottom_layers,
        is_symmetric=form.get("is_symmetric") == "on",
        core_material_id=core_material_id,
        insert_dummy_layer_for_odd_compatibility=form.get(
            "insert_dummy_layer_for_odd_compatibility"
        )
        == "on",
        compatibility_mode="physical",
        custom_materials=[CustomMaterialModel(**material) for material in custom_materials_payload],
        three_point_bending=ThreePointBendingConfigModel(
            elastic_gradient=_parse_float_or_default(form, "elastic_gradient", 2649.0),
            rigidez_rig=_parse_float_or_default(form, "rigidez_rig", 14871.0),
            span_m=_millimeters_to_meters(span_mm),
            span_mm=span_mm,
            width_m=_millimeters_to_meters(width_mm),
            width_mm=width_mm,
        ),
    )
