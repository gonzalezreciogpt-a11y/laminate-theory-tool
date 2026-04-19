from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESERVED_MATERIAL_IDS = {"Dummy"}


@dataclass(frozen=True)
class Material:
    id: str
    name: str
    material_category: str
    fiber_family: str | None
    e1_pa: float
    e2_pa: float
    g12_pa: float
    poisson_input: float
    strength_x: float
    strength_x_compression: float
    strength_y: float
    strength_y_compression: float
    strength_s: float
    thickness_mm: float
    user_selectable: bool
    notes: str


@dataclass(frozen=True)
class ThreePointBendingDefaults:
    elastic_gradient: float
    rigidez_rig: float
    span_m: float
    span_mm: float
    width_m: float
    width_mm: float


@lru_cache(maxsize=1)
def load_material_catalog() -> dict[str, Material]:
    payload = json.loads((DATA_DIR / "materials.json").read_text(encoding="utf-8"))
    return {item["id"]: Material(**item) for item in payload}


@lru_cache(maxsize=1)
def load_three_point_bending_defaults() -> ThreePointBendingDefaults:
    payload = json.loads(
        (DATA_DIR / "three_point_bending_defaults.json").read_text(encoding="utf-8")
    )
    return ThreePointBendingDefaults(**payload)


def list_materials(*, public_only: bool = False, category: str | None = None) -> list[Material]:
    materials = list(load_material_catalog().values())
    if public_only:
        materials = [material for material in materials if material.user_selectable]
    if category is not None:
        materials = [material for material in materials if material.material_category == category]
    return materials


def material_to_dict(material: Material) -> dict[str, object]:
    return {
        "id": material.id,
        "name": material.name,
        "material_category": material.material_category,
        "fiber_family": material.fiber_family,
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


def build_material_catalog(
    custom_materials: Iterable[dict[str, object]] | None = None,
) -> dict[str, Material]:
    catalog = dict(load_material_catalog())
    if not custom_materials:
        return catalog

    for payload in custom_materials:
        material = Material(
            id=str(payload["id"]),
            name=str(payload["name"]),
            material_category=str(payload.get("material_category", "fiber")),
            fiber_family=(
                str(payload["fiber_family"])
                if payload.get("fiber_family") is not None
                else ("twill" if str(payload.get("material_category", "fiber")) == "fiber" else None)
            ),
            e1_pa=float(payload["e1_pa"]),
            e2_pa=float(payload["e2_pa"]),
            g12_pa=float(payload["g12_pa"]),
            poisson_input=float(payload["poisson_input"]),
            strength_x=float(payload["strength_x"]),
            strength_x_compression=float(payload["strength_x_compression"]),
            strength_y=float(payload["strength_y"]),
            strength_y_compression=float(payload["strength_y_compression"]),
            strength_s=float(payload["strength_s"]),
            thickness_mm=float(payload["thickness_mm"]),
            user_selectable=bool(payload.get("user_selectable", True)),
            notes=str(payload.get("notes", "Custom user material.")),
        )
        catalog[material.id] = material

    return catalog
