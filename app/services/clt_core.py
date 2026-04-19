from __future__ import annotations

import math

import numpy as np

from app.domain.laminate import BuiltLaminate


def compute_total_thickness_mm(laminate: BuiltLaminate) -> float:
    return sum(layer.material.thickness_mm for layer in laminate.layers)


def compute_legacy_z_positions_mm(
    laminate: BuiltLaminate,
) -> tuple[list[float], float, float]:
    num_layers = len(laminate.layers)
    z = np.zeros(num_layers + 2, dtype=float)
    total_thickness = compute_total_thickness_mm(laminate)
    legacy_capa_central_value = laminate.core_material.thickness_mm

    if laminate.is_symmetric:
        half_thickness = total_thickness / 2.0
        accumulated_thickness = 0.0

        for matlab_index in range(1, math.ceil(num_layers / 2) + 1):
            h = laminate.layers[matlab_index - 1].material.thickness_mm
            accumulated_thickness += h
            z[matlab_index] = half_thickness - accumulated_thickness + h / 2.0

        if num_layers % 2 == 1:
            capa_central_index = math.ceil(num_layers / 2) + 1
            legacy_capa_central_value = float(capa_central_index)
            h_central = laminate.layers[capa_central_index - 1].material.thickness_mm
            z[capa_central_index] = half_thickness - accumulated_thickness - h_central / 2.0
            accumulated_thickness += h_central

        for matlab_index in range(math.ceil(num_layers / 2) + 1, num_layers + 1):
            z[matlab_index] = -z[num_layers + 1 - matlab_index]

        z[num_layers + 1] = -half_thickness
    else:
        accumulated_thickness = 0.0
        for matlab_index in range(1, num_layers + 1):
            h = laminate.layers[matlab_index - 1].material.thickness_mm
            accumulated_thickness += h
            z[matlab_index] = accumulated_thickness - h / 2.0 - total_thickness / 2.0

        z[num_layers + 1] = -total_thickness / 2.0

    return z[1:].tolist(), total_thickness, legacy_capa_central_value


def compute_legacy_abd(
    laminate: BuiltLaminate,
    z_mm: list[float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    num_layers = len(laminate.layers)
    z = np.asarray([0.0, *z_mm], dtype=float)

    a_matrix = np.zeros((3, 3), dtype=float)
    b_matrix = np.zeros((3, 3), dtype=float)
    d_matrix = np.zeros((3, 3), dtype=float)
    last_nu12 = 0.0

    for matlab_index in range(1, num_layers + 1):
        layer = laminate.layers[matlab_index - 1]
        material = layer.material

        e1 = material.e1_pa
        e2 = material.e2_pa
        g12 = material.g12_pa
        nu21 = material.poisson_input
        h = material.thickness_mm
        last_nu12 = (e2 / e1) * nu21

        q11 = e1 / (1.0 - last_nu12 * nu21)
        q12 = (nu21 * e2) / (1.0 - last_nu12 * nu21)
        q22 = e2 / (1.0 - last_nu12 * nu21)
        qss = g12

        m = math.cos(math.radians(layer.theta_deg))
        n = math.sin(math.radians(layer.theta_deg))

        qxx = q11 * (m**4) + 2.0 * (q12 + 2.0 * qss) * (n**2) * (m**2) + q22 * (n**4)
        qyx = (q11 + q22 - 4.0 * qss) * (n**2) * (m**2) + q12 * ((n**4) + (m**4))
        qyy = q11 * (n**4) + 2.0 * (q12 + 2.0 * qss) * (n**2) * (m**2) + q22 * (m**4)
        qxs = (q11 - q12 - 2.0 * qss) * n * (m**3) + (q12 - q22 + 2.0 * qss) * n * (m**3)
        qys = (q11 - q12 - 2.0 * qss) * m * (n**3) + (q12 - q22 + 2.0 * qss) * m * (n**3)
        qss_bar = (q11 + q22 - 2.0 * q12 - 2.0 * qss) * (n**2) * (m**2) + qss * (
            (n**4) + (m**4)
        )

        qxy = np.array(
            [
                [qxx, qyx, qxs],
                [qyx, qyy, qys],
                [qxs, qys, qss_bar],
            ],
            dtype=float,
        )

        a_matrix = a_matrix + qxy * h
        b_matrix = b_matrix + qxy * ((z[matlab_index] ** 2) - (z[matlab_index + 1] ** 2)) / 2.0
        d_matrix = d_matrix + qxy * ((z[matlab_index] ** 3) - (z[matlab_index + 1] ** 3)) / 3.0

    return a_matrix, b_matrix, d_matrix, last_nu12
