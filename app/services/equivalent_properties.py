from __future__ import annotations

import numpy as np

from app.domain.units import pa_to_gpa


def compute_equivalent_properties(
    a_matrix: np.ndarray,
    d_matrix: np.ndarray,
    total_thickness_mm: float,
    last_nu12: float,
) -> dict[str, float | list[list[float]]]:
    a1_matrix = a_matrix / total_thickness_mm
    d1_matrix = d_matrix / total_thickness_mm

    a_inverse = np.linalg.inv(a1_matrix)
    d_inverse = np.linalg.inv(d1_matrix)

    e11 = 1.0 / a_inverse[0, 0]
    e22 = 1.0 / a_inverse[1, 1]
    g122 = 1.0 / a_inverse[2, 2]
    _e111 = 1.0 / d_inverse[0, 0]
    nu21 = -a_inverse[1, 0] / a_inverse[0, 0]
    nu12 = -a_inverse[0, 1] / a_inverse[1, 1]
    g12g = e11 / (2.0 * (1.0 + last_nu12))

    return {
        "a1_matrix": a1_matrix.tolist(),
        "d1_matrix": d1_matrix.tolist(),
        "e11_pa": float(e11),
        "e22_pa": float(e22),
        "g122_pa": float(g122),
        "nu12": float(nu12),
        "nu21": float(nu21),
        "g12g_pa": float(g12g),
        "e11_gpa": pa_to_gpa(float(e11)),
        "e22_gpa": pa_to_gpa(float(e22)),
        "g122_gpa": pa_to_gpa(float(g122)),
        "g12g_gpa": pa_to_gpa(float(g12g)),
    }
