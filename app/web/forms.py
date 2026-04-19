from __future__ import annotations

import json

from starlette.datastructures import FormData

from app.schemas.inputs import (
    CustomMaterialModel,
    LaminateRequestModel,
    LayerInputModel,
    ThreePointBendingConfigModel,
)


def build_request_from_form(form: FormData) -> LaminateRequestModel:
    material_ids = form.getlist("material_id")
    theta_values = form.getlist("theta_deg")
    layers: list[LayerInputModel] = []

    for material_id, theta_value in zip(material_ids, theta_values, strict=False):
        material_id = material_id.strip()
        theta_value = theta_value.strip()
        if not material_id or theta_value == "":
            continue
        layers.append(LayerInputModel(material_id=material_id, theta_deg=float(theta_value)))

    custom_materials_json = str(form.get("custom_materials_json", "[]"))
    custom_materials_payload = json.loads(custom_materials_json)

    return LaminateRequestModel(
        layers=layers,
        is_symmetric=form.get("is_symmetric") == "on",
        core_material_id=form.get("core_material_id", "Honeycomb"),
        insert_dummy_layer_for_odd_compatibility=form.get(
            "insert_dummy_layer_for_odd_compatibility"
        )
        == "on",
        compatibility_mode="legacy",
        custom_materials=[CustomMaterialModel(**material) for material in custom_materials_payload],
        three_point_bending=ThreePointBendingConfigModel(
            elastic_gradient=float(form.get("elastic_gradient", 2649.0)),
            rigidez_rig=float(form.get("rigidez_rig", 14871.0)),
            span_m=float(form.get("span_m", 0.4)),
            span_mm=float(form.get("span_mm", 400.0)),
            width_m=float(form.get("width_m", 0.275)),
            width_mm=float(form.get("width_mm", 275.0)),
        ),
    )
