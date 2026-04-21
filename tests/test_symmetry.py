import numpy as np

from app.schemas.inputs import LaminateRequestModel
from app.services.legacy_compatibility import analyze_laminate, analyze_laminate_legacy
from app.services.sandwich_trace import build_visible_sandwich_layers, compute_visible_sandwich_trace


def test_symmetric_flag_mirrors_z_without_reordering_layers() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
            {"material_id": "RC416T", "theta_deg": 90.0},
            {"material_id": "UD", "theta_deg": 0.0},
        ],
        is_symmetric=True,
        core_material_id="Honeycomb",
        compatibility_mode="legacy",
    )
    result = analyze_laminate_legacy(payload)

    assert [layer.material_id for layer in result.generated_layers] == ["RC416T", "UD", "RC416T", "UD"]
    assert result.trace.z_mm[0] == -result.trace.z_mm[3]
    assert result.trace.z_mm[1] == -result.trace.z_mm[2]


def test_nonsymmetric_flag_uses_direct_z_progression() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "UD", "theta_deg": 0.0},
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
        ],
        is_symmetric=False,
        core_material_id="Honeycomb",
        compatibility_mode="legacy",
    )
    result = analyze_laminate_legacy(payload)
    assert result.trace.z_mm[-1] == -(result.trace.espesor_total_mm / 2.0)


def test_physical_mode_has_nearly_null_b_matrix_for_symmetric_sandwich() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
            {"material_id": "RC416T", "theta_deg": 90.0},
        ],
        is_symmetric=True,
        core_material_id="Honeycomb",
    )

    result = analyze_laminate(payload)
    assert np.allclose(result.trace.b_matrix, np.zeros((3, 3)), atol=1e-4)


def test_visible_sandwich_layers_include_core_and_mirrored_bottom_skin() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
        ],
        is_symmetric=True,
        core_material_id="Honeycomb",
    )

    display_layers = build_visible_sandwich_layers(payload)

    assert [layer.material_id for layer in display_layers] == [
        "RC416T",
        "UD",
        "Honeycomb",
        "UD",
        "RC416T",
    ]
    assert [layer.zone for layer in display_layers] == [
        "superior",
        "superior",
        "core",
        "inferior",
        "inferior",
    ]


def test_visible_sandwich_layers_include_explicit_bottom_skin_when_unsymmetric() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
        ],
        bottom_layers=[
            {"material_id": "RC416T", "theta_deg": 90.0},
        ],
        is_symmetric=False,
        core_material_id="Honeycomb",
    )

    display_layers = build_visible_sandwich_layers(payload)
    trace = compute_visible_sandwich_trace(payload)

    assert [layer.material_id for layer in display_layers] == [
        "RC416T",
        "UD",
        "Honeycomb",
        "RC416T",
    ]
    assert trace.b_matrix[0][0] != 0.0
