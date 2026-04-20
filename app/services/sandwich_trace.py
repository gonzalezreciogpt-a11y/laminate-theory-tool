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
    theta_deg: float | None
    thickness_mm: float
    zone: str


@dataclass(frozen=True)
class SandwichTrace:
    total_thickness_mm: float
    z_interfaces_mm: list[float]
    a_matrix: list[list[float]]
    b_matrix: list[list[float]]
    d_matrix: list[list[float]]


def _build_qbar(material: Material, theta_deg: float) -> np.ndarray:
    e1 = material.e1_pa
    e2 = material.e2_pa
    g12 = material.g12_pa
    nu21 = material.poisson_input
    nu12 = (e2 / e1) * nu21

    q11 = e1 / (1.0 - nu12 * nu21)
    q12 = (nu21 * e2) / (1.0 - nu12 * nu21)
    q22 = e2 / (1.0 - nu12 * nu21)
    qss = g12

    m = math.cos(math.radians(theta_deg))
    n = math.sin(math.radians(theta_deg))

    qxx = q11 * (m**4) + 2.0 * (q12 + 2.0 * qss) * (n**2) * (m**2) + q22 * (n**4)
    qyx = (q11 + q22 - 4.0 * qss) * (n**2) * (m**2) + q12 * ((n**4) + (m**4))
    qyy = q11 * (n**4) + 2.0 * (q12 + 2.0 * qss) * (n**2) * (m**2) + q22 * (m**4)
    qxs = (q11 - q12 - 2.0 * qss) * n * (m**3) + (q12 - q22 + 2.0 * qss) * n * (m**3)
    qys = (q11 - q12 - 2.0 * qss) * m * (n**3) + (q12 - q22 + 2.0 * qss) * m * (n**3)
    qss_bar = (q11 + q22 - 2.0 * q12 - 2.0 * qss) * (n**2) * (m**2) + qss * (
        (n**4) + (m**4)
    )

    return np.array(
        [
            [qxx, qyx, qxs],
            [qyx, qyy, qys],
            [qxs, qys, qss_bar],
        ],
        dtype=float,
    )


def build_visible_sandwich_layers(request: LaminateRequestModel) -> list[SandwichDisplayLayer]:
    catalog = build_material_catalog([material.model_dump() for material in request.custom_materials])
    top_layers: list[SandwichDisplayLayer] = []

    for index, layer in enumerate(request.layers, start=1):
        material = catalog[layer.material_id]
        if material.id == "Dummy":
            continue
        top_layers.append(
            SandwichDisplayLayer(
                index=index,
                material_id=material.id,
                material_name=material.name,
                theta_deg=layer.theta_deg,
                thickness_mm=material.thickness_mm,
                zone="superior",
            )
        )

    core_material = catalog[request.core_material_id]
    display_layers = list(top_layers)
    display_layers.append(
        SandwichDisplayLayer(
            index=len(display_layers) + 1,
            material_id=core_material.id,
            material_name=core_material.name,
            theta_deg=None,
            thickness_mm=core_material.thickness_mm,
            zone="core",
        )
    )

    for layer in reversed(top_layers):
        display_layers.append(
            SandwichDisplayLayer(
                index=len(display_layers) + 1,
                material_id=layer.material_id,
                material_name=layer.material_name,
                theta_deg=layer.theta_deg,
                thickness_mm=layer.thickness_mm,
                zone="inferior",
            )
        )

    return display_layers


def compute_visible_sandwich_trace(request: LaminateRequestModel) -> SandwichTrace:
    catalog = build_material_catalog([material.model_dump() for material in request.custom_materials])
    display_layers = build_visible_sandwich_layers(request)

    total_thickness_mm = sum(layer.thickness_mm for layer in display_layers)
    current_z = total_thickness_mm / 2.0
    z_interfaces_mm = [current_z]

    a_matrix = np.zeros((3, 3), dtype=float)
    b_matrix = np.zeros((3, 3), dtype=float)
    d_matrix = np.zeros((3, 3), dtype=float)

    for layer in display_layers:
        next_z = current_z - layer.thickness_mm
        theta_deg = 0.0 if layer.theta_deg is None else layer.theta_deg
        qbar = _build_qbar(catalog[layer.material_id], theta_deg)
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
