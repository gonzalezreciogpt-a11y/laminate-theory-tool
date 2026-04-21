from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from app.schemas.inputs import LaminateRequestModel
from app.services.legacy_compatibility import analyze_laminate_legacy


REFERENCE_DIR = Path("examples/reference_cases")
REFERENCE_PAIRS = (
    ("base_case.json", "base_case_golden.json"),
    ("even_case_manifest.json", "even_case_golden.json"),
    ("odd_case_manifest.json", "odd_case_golden.json"),
    ("nonsymmetric_case_manifest.json", "nonsymmetric_case_golden.json"),
)


def load_json(name: str) -> dict:
    return json.loads((REFERENCE_DIR / name).read_text(encoding="utf-8"))


def assert_close_matrix(actual: list[list[float]], expected: list[list[float]]) -> None:
    np.testing.assert_allclose(actual, expected, rtol=1e-9, atol=1e-3)


@pytest.mark.parametrize(("input_name", "golden_name"), REFERENCE_PAIRS)
def test_reference_case_matches_matlab_golden(input_name: str, golden_name: str) -> None:
    payload = LaminateRequestModel(**load_json(input_name))
    payload.compatibility_mode = "legacy"
    golden = load_json(golden_name)
    result = analyze_laminate_legacy(payload)

    np.testing.assert_allclose(result.trace.espesor_total_mm, golden["espesor_total_mm"], rtol=0, atol=1e-9)
    np.testing.assert_allclose(result.trace.z_mm, golden["z_mm"], rtol=0, atol=1e-9)
    assert_close_matrix(result.trace.a_matrix, golden["a_matrix"])
    assert_close_matrix(result.trace.b_matrix, golden["b_matrix"])
    assert_close_matrix(result.trace.d_matrix, golden["d_matrix"])
    assert_close_matrix(result.trace.a1_matrix, golden["a1_matrix"])
    assert_close_matrix(result.trace.d1_matrix, golden["d1_matrix"])
    np.testing.assert_allclose(result.equivalent_properties.e11_pa, golden["e11_pa"], rtol=1e-9, atol=1e-6)
    np.testing.assert_allclose(result.equivalent_properties.e22_pa, golden["e22_pa"], rtol=1e-9, atol=1e-6)
    np.testing.assert_allclose(result.equivalent_properties.g122_pa, golden["g122_pa"], rtol=1e-9, atol=1e-6)
    np.testing.assert_allclose(result.equivalent_properties.nu12, golden["nu12"], rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(result.equivalent_properties.nu21, golden["nu21"], rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(result.equivalent_properties.g12g_pa, golden["g12g_pa"], rtol=1e-9, atol=1e-6)
    np.testing.assert_allclose(result.three_point_bending.ei_ensayo, golden["ei_ensayo"], rtol=1e-9, atol=1e-9)
    np.testing.assert_allclose(
        result.three_point_bending.e_fibra_ensayo,
        golden["e_fibra_ensayo"],
        rtol=1e-9,
        atol=1e-6,
    )
    np.testing.assert_allclose(result.three_point_bending.ei_theory, golden["ei_theory"], rtol=1e-9, atol=1e-9)
    np.testing.assert_allclose(
        result.three_point_bending.elastic_gradient_theory,
        golden["elastic_gradient_theory"],
        rtol=1e-9,
        atol=1e-9,
    )
    if "last_nu12_used_for_g12g" in golden:
        np.testing.assert_allclose(
            result.trace.last_nu12_used_for_g12g,
            golden["last_nu12_used_for_g12g"],
            rtol=1e-9,
            atol=1e-12,
        )
