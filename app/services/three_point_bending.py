from __future__ import annotations

from app.domain.materials import ThreePointBendingDefaults


def compute_three_point_bending(
    *,
    e1_p_manual: float,
    total_thickness_mm: float,
    legacy_capa_central_value: float,
    defaults: ThreePointBendingDefaults,
) -> dict[str, float]:
    elastic_gradient_corrected = (
        defaults.elastic_gradient * defaults.rigidez_rig
    ) / (defaults.rigidez_rig - defaults.elastic_gradient)
    ei_ensayo = elastic_gradient_corrected * 1000.0 * (defaults.span_m**3) / 48.0
    e_fibra_ensayo = (
        (defaults.span_mm**3)
        / (
            24.0
            * defaults.width_mm
            * total_thickness_mm
            * ((total_thickness_mm + legacy_capa_central_value) ** 2)
        )
        * elastic_gradient_corrected
    )
    ei_theory = 0.5 * (
        e1_p_manual
        * defaults.width_m
        * (total_thickness_mm * 0.001)
        * ((total_thickness_mm * 0.001 + legacy_capa_central_value * 0.001) ** 2)
    )
    elastic_gradient_theory = 48.0 * ei_theory / ((defaults.span_m**3) * 1000.0)

    return {
        "elastic_gradient": defaults.elastic_gradient,
        "rigidez_rig": defaults.rigidez_rig,
        "elastic_gradient_corrected": elastic_gradient_corrected,
        "ei_ensayo": ei_ensayo,
        "e_fibra_ensayo": e_fibra_ensayo,
        "ei_theory": ei_theory,
        "elastic_gradient_theory": elastic_gradient_theory,
        "th_fibra_mm": total_thickness_mm,
        "legacy_capa_central_value": legacy_capa_central_value,
    }
