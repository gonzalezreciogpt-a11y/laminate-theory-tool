from __future__ import annotations

import numpy as np

from app.schemas.inputs import LaminateRequestModel
from app.services.equivalent_properties import compute_equivalent_properties_physical
from app.services.legacy_compatibility import analyze_laminate
from app.services.sandwich_trace import compute_top_skin_trace


def test_physical_mode_builds_full_sandwich_and_uses_one_side_fiber_thickness() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
            {"material_id": "RC416T", "theta_deg": 90.0},
        ],
        core_material_id="Honeycomb",
    )

    result = analyze_laminate(payload)

    assert [layer.material_id for layer in result.generated_layers] == [
        "RC416T",
        "UD",
        "RC416T",
        "Honeycomb",
        "RC416T",
        "UD",
        "RC416T",
    ]
    assert result.three_point_bending.th_fibra_mm == 1.16
    assert round(result.trace.espesor_total_mm, 3) == 22.32


def test_physical_mode_sets_g12g_equal_to_g12() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
        ],
        core_material_id="Honeycomb",
    )

    result = analyze_laminate(payload)

    assert result.equivalent_properties.g12g_pa == result.equivalent_properties.g122_pa
    assert result.equivalent_properties.g12g_gpa == result.equivalent_properties.g122_gpa


def test_physical_mode_ei_theory_matches_professor_formula() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
            {"material_id": "RC416T", "theta_deg": 90.0},
        ],
        core_material_id="Honeycomb",
    )

    result = analyze_laminate(payload)
    top_skin_trace = compute_top_skin_trace(payload)
    top_skin_properties = compute_equivalent_properties_physical(
        a_matrix=np.array(top_skin_trace.a_matrix, dtype=float),
        d_matrix=np.array(top_skin_trace.d_matrix, dtype=float),
        total_thickness_mm=top_skin_trace.total_thickness_mm,
    )
    defaults = payload.three_point_bending
    t_skin_m = result.three_point_bending.th_fibra_mm * 0.001
    t_core_m = result.three_point_bending.legacy_capa_central_value * 0.001

    expected = (
        0.5
        * top_skin_properties["e11_pa"]
        * defaults.width_m
        * t_skin_m
        * ((t_skin_m + t_core_m) ** 2)
    )

    assert np.isclose(result.three_point_bending.ei_theory, expected, rtol=1e-9, atol=1e-9)


def test_physical_mode_e_fibra_ensayo_inverts_professor_formula() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
            {"material_id": "RC416T", "theta_deg": 90.0},
        ],
        core_material_id="Honeycomb",
    )

    result = analyze_laminate(payload)
    defaults = payload.three_point_bending
    t_skin_m = result.three_point_bending.th_fibra_mm * 0.001
    t_core_m = result.three_point_bending.legacy_capa_central_value * 0.001
    denominator = 0.5 * defaults.width_m * t_skin_m * ((t_skin_m + t_core_m) ** 2)

    assert np.isclose(
        result.three_point_bending.e_fibra_ensayo,
        result.three_point_bending.ei_ensayo / denominator,
        rtol=1e-9,
        atol=1e-9,
    )
