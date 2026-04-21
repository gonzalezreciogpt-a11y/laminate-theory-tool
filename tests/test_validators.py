import pytest

from app.schemas.inputs import LaminateRequestModel
from app.services.validators import validate_request


def test_rejects_unknown_material() -> None:
    payload = LaminateRequestModel(
        layers=[{"material_id": "UNKNOWN", "theta_deg": 0.0}],
        is_symmetric=True,
        core_material_id="Honeycomb",
        insert_dummy_layer_for_odd_compatibility=False,
        compatibility_mode="legacy",
    )
    with pytest.raises(ValueError, match="Material desconocido"):
        validate_request(payload)


def test_warns_when_dummy_is_explicit() -> None:
    payload = LaminateRequestModel(
        layers=[{"material_id": "Dummy", "theta_deg": 0.0}],
        is_symmetric=True,
        core_material_id="Honeycomb",
        compatibility_mode="legacy",
    )
    warnings = validate_request(payload)
    assert any("Dummy" in warning for warning in warnings)


def test_rejects_core_material_inside_layers() -> None:
    payload = LaminateRequestModel(
        layers=[{"material_id": "Honeycomb", "theta_deg": 0.0}],
        is_symmetric=True,
        core_material_id="Honeycomb",
    )
    with pytest.raises(ValueError, match="deben usar materiales de fibra"):
        validate_request(payload)


def test_rejects_fiber_material_as_core() -> None:
    payload = LaminateRequestModel(
        layers=[{"material_id": "RC416T", "theta_deg": 0.0}],
        is_symmetric=True,
        core_material_id="UD",
    )
    with pytest.raises(ValueError, match="categoria core"):
        validate_request(payload)


def test_rejects_invalid_ud_orientation() -> None:
    payload = LaminateRequestModel(
        layers=[{"material_id": "UD", "theta_deg": 45.0}],
        is_symmetric=True,
        core_material_id="Honeycomb",
    )
    with pytest.raises(ValueError, match="UD"):
        validate_request(payload)


def test_rejects_invalid_twill_orientation() -> None:
    payload = LaminateRequestModel(
        layers=[{"material_id": "RC416T", "theta_deg": 0.0}],
        is_symmetric=True,
        core_material_id="Honeycomb",
    )
    with pytest.raises(ValueError, match="twill"):
        validate_request(payload)


def test_allows_local_override_of_base_material_id() -> None:
    payload = LaminateRequestModel(
        layers=[{"material_id": "RC416T", "theta_deg": 45.0}],
        is_symmetric=True,
        core_material_id="Honeycomb",
        custom_materials=[
            {
                "id": "Honeycomb",
                "name": "Honeycomb",
                "material_category": "core",
                "e1_pa": 1000000.0,
                "e2_pa": 1000000.0,
                "g12_pa": 1000000.0,
                "poisson_input": 0.5,
                "thickness_mm": 18.0,
                "user_selectable": True,
                "notes": "Browser-local override.",
            }
        ],
    )
    warnings = validate_request(payload)
    assert isinstance(warnings, list)
