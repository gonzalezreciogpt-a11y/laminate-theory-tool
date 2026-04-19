from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.materials import Material, ThreePointBendingDefaults


@dataclass(frozen=True)
class LayerInput:
    material_id: str
    theta_deg: float


@dataclass(frozen=True)
class ResolvedLayer:
    index: int
    material: Material
    theta_deg: float
    source: str = "user"


@dataclass(frozen=True)
class LaminateDefinition:
    layers: list[LayerInput]
    is_symmetric: bool
    core_material_id: str = "Honeycomb"
    insert_dummy_layer_for_odd_compatibility: bool = False
    compatibility_mode: str = "legacy"
    bending_defaults: ThreePointBendingDefaults | None = None
    custom_materials: list[Material] = field(default_factory=list)


@dataclass(frozen=True)
class BuiltLaminate:
    layers: list[ResolvedLayer]
    is_symmetric: bool
    core_material: Material
    compatibility_mode: str
    dummy_inserted: bool = False
    warnings: list[str] = field(default_factory=list)
