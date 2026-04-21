from app.schemas.inputs import LaminateRequestModel
from app.services.legacy_compatibility import analyze_laminate_legacy


def test_auto_dummy_is_inserted_for_odd_compatibility() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
            {"material_id": "RC416T", "theta_deg": -45.0},
        ],
        is_symmetric=True,
        core_material_id="Honeycomb",
        insert_dummy_layer_for_odd_compatibility=True,
        compatibility_mode="legacy",
    )
    result = analyze_laminate_legacy(payload)
    assert result.generated_layers[-1].material_id == "Dummy"
    assert result.generated_layers[-1].source == "compatibility-auto-dummy"


def test_g12g_uses_last_layer_nu12_in_legacy_mode() -> None:
    payload = LaminateRequestModel(
        layers=[
            {"material_id": "RC416T", "theta_deg": 45.0},
            {"material_id": "UD", "theta_deg": 0.0},
            {"material_id": "Dummy", "theta_deg": 0.0},
        ],
        is_symmetric=False,
        core_material_id="Honeycomb",
        compatibility_mode="legacy",
    )
    result = analyze_laminate_legacy(payload)
    assert result.trace.last_nu12_used_for_g12g == 0.00001
