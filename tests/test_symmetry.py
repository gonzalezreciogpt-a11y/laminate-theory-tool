from app.schemas.inputs import LaminateRequestModel
from app.services.legacy_compatibility import analyze_laminate


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
    )
    result = analyze_laminate(payload)

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
    )
    result = analyze_laminate(payload)
    assert result.trace.z_mm[-1] == -(result.trace.espesor_total_mm / 2.0)
