from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from app.domain.materials import Material, build_material_catalog
from app.schemas.inputs import LaminateRequestModel


@dataclass(frozen=True)
class SandwichDisplayLayer:
    index: int
    material_id: str
    material_name: str
    material: Material
    theta_deg: float | None
    thickness_mm: float
    zone: str
    source: str


@dataclass(frozen=True)
class SandwichTrace:
    total_thickness_mm: float
    z_interfaces_mm: list[float]
    a_matrix: list[list[float]]
    b_matrix: list[list[float]]
    d_matrix: list[list[float]]


def build_qbar(material: Material, theta_deg: float) -> np.ndarray:
    e1 = material.e1_pa
    e2 = material.e2_pa
    g12 = material.g12_pa
    nu21 = material.poisson_input
    nu12 = (e2 / e1) * nu21

    denominator = 1.0 - nu12 * nu21
    q11 = e1 / denominator
    q12 = (nu21 * e2) / denominator
    q22 = e2 / denominator
    q66 = g12

    m = math.cos(math.radians(theta_deg))
    n = math.sin(math.radians(theta_deg))
    m2 = m * m
    n2 = n * n
    m3 = m2 * m
    n3 = n2 * n
    m4 = m2 * m2
    n4 = n2 * n2

    q11_bar = q11 * m4 + 2.0 * (q12 + 2.0 * q66) * m2 * n2 + q22 * n4
    q22_bar = q11 * n4 + 2.0 * (q12 + 2.0 * q66) * m2 * n2 + q22 * m4
    q12_bar = (q11 + q22 - 4.0 * q66) * m2 * n2 + q12 * (m4 + n4)
    q16_bar = (q11 - q12 - 2.0 * q66) * m3 * n - (q22 - q12 - 2.0 * q66) * m * n3
    q26_bar = (q11 - q12 - 2.0 * q66) * m * n3 - (q22 - q12 - 2.0 * q66) * m3 * n
    q66_bar = (q11 + q22 - 2.0 * q12 - 2.0 * q66) * m2 * n2 + q66 * (m4 + n4)

    return np.array(
        [
            [q11_bar, q12_bar, q16_bar],
            [q12_bar, q22_bar, q26_bar],
            [q16_bar, q26_bar, q66_bar],
        ],
        dtype=float,
    )


def _build_skin_layers(
    request: LaminateRequestModel,
    *,
    side: str,
) -> list[SandwichDisplayLayer]:
    catalog = build_material_catalog([material.model_dump() for material in request.custom_materials])
    source_layers = request.layers if side == "top" else request.bottom_layers
    zone = "superior" if side == "top" else "inferior"
    source = "user-top-skin" if side == "top" else "user-bottom-skin"
    skin_layers: list[SandwichDisplayLayer] = []

    for index, layer in enumerate(source_layers, start=1):
        material = catalog[layer.material_id]
        if material.id == "Dummy":
            continue
        skin_layers.append(
            SandwichDisplayLayer(
                index=index,
                material_id=material.id,
                material_name=material.name,
                material=material,
                theta_deg=layer.theta_deg,
                thickness_mm=material.thickness_mm,
                zone=zone,
                source=source,
            )
        )
    return skin_layers


def build_top_skin_layers(request: LaminateRequestModel) -> list[SandwichDisplayLayer]:
    return _build_skin_layers(request, side="top")


def build_bottom_skin_layers(request: LaminateRequestModel) -> list[SandwichDisplayLayer]:
    if request.is_symmetric:
        return []
    return _build_skin_layers(request, side="bottom")


def build_visible_sandwich_layers(request: LaminateRequestModel) -> list[SandwichDisplayLayer]:
    catalog = build_material_catalog([material.model_dump() for material in request.custom_materials])
    top_layers = build_top_skin_layers(request)
    core_material = catalog[request.core_material_id]

    display_layers = list(top_layers)
    display_layers.append(
        SandwichDisplayLayer(
            index=len(display_layers) + 1,
            material_id=core_material.id,
            material_name=core_material.name,
            material=core_material,
            theta_deg=None,
            thickness_mm=core_material.thickness_mm,
            zone="core",
            source="auto-core",
        )
    )

    bottom_layers = (
        [
            SandwichDisplayLayer(
                index=0,
                material_id=layer.material_id,
                material_name=layer.material_name,
                material=layer.material,
                theta_deg=layer.theta_deg,
                thickness_mm=layer.thickness_mm,
                zone="inferior",
                source="auto-mirrored-bottom-skin",
            )
            for layer in reversed(top_layers)
        ]
        if request.is_symmetric
        else build_bottom_skin_layers(request)
    )

    for layer in bottom_layers:
        display_layers.append(
            SandwichDisplayLayer(
                index=len(display_layers) + 1,
                material_id=layer.material_id,
                material_name=layer.material_name,
                material=layer.material,
                theta_deg=layer.theta_deg,
                thickness_mm=layer.thickness_mm,
                zone="inferior",
                source=layer.source,
            )
        )

    return display_layers


def compute_trace_for_layers(layers: list[SandwichDisplayLayer]) -> SandwichTrace:
    total_thickness_mm = sum(layer.thickness_mm for layer in layers)
    current_z = total_thickness_mm / 2.0
    z_interfaces_mm = [current_z]

    a_matrix = np.zeros((3, 3), dtype=float)
    b_matrix = np.zeros((3, 3), dtype=float)
    d_matrix = np.zeros((3, 3), dtype=float)

    for layer in layers:
        next_z = current_z - layer.thickness_mm
        theta_deg = 0.0 if layer.theta_deg is None else layer.theta_deg
        qbar = build_qbar(layer.material, theta_deg)
        a_matrix = a_matrix + qbar * (current_z - next_z)
        b_matrix = b_matrix + qbar * ((current_z**2) - (next_z**2)) / 2.0
        d_matrix = d_matrix + qbar * ((current_z**3) - (next_z**3)) / 3.0
        current_z = next_z
        z_interfaces_mm.append(current_z)

    return SandwichTrace(
        total_thickness_mm=total_thickness_mm,
        z_interfaces_mm=z_interfaces_mm,
        a_matrix=a_matrix.tolist(),
        b_matrix=b_matrix.tolist(),
        d_matrix=d_matrix.tolist(),
    )


def compute_top_skin_trace(request: LaminateRequestModel) -> SandwichTrace:
    return compute_trace_for_layers(build_top_skin_layers(request))


def compute_bottom_skin_trace(request: LaminateRequestModel) -> SandwichTrace:
    return compute_trace_for_layers(build_bottom_skin_layers(request))


def compute_visible_sandwich_trace(request: LaminateRequestModel) -> SandwichTrace:
    return compute_trace_for_layers(build_visible_sandwich_layers(request))
