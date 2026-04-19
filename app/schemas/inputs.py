from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LayerInputModel(BaseModel):
    material_id: str = Field(min_length=1)
    theta_deg: float


class ThreePointBendingConfigModel(BaseModel):
    elastic_gradient: float = 2649.0
    rigidez_rig: float = 14871.0
    span_m: float = 0.4
    span_mm: float = 400.0
    width_m: float = 0.275
    width_mm: float = 275.0


class CustomMaterialModel(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    material_category: Literal["fiber", "core", "compatibility"] = "fiber"
    fiber_family: Literal["twill", "ud"] | None = None
    e1_pa: float
    e2_pa: float
    g12_pa: float
    poisson_input: float
    strength_x: float = 0.0
    strength_x_compression: float = 0.0
    strength_y: float = 0.0
    strength_y_compression: float = 0.0
    strength_s: float = 0.0
    thickness_mm: float
    user_selectable: bool = True
    notes: str = "Custom user material."


class LaminateRequestModel(BaseModel):
    layers: list[LayerInputModel]
    is_symmetric: bool = True
    core_material_id: str = "Honeycomb"
    insert_dummy_layer_for_odd_compatibility: bool = False
    compatibility_mode: str = "legacy"
    custom_materials: list[CustomMaterialModel] = Field(default_factory=list)
    three_point_bending: ThreePointBendingConfigModel = Field(
        default_factory=ThreePointBendingConfigModel
    )

    @field_validator("layers")
    @classmethod
    def ensure_layers_present(cls, value: list[LayerInputModel]) -> list[LayerInputModel]:
        if not value:
            raise ValueError("Debe existir al menos una capa.")
        return value
