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


def compute_three_point_bending_physical(
    *,
    e_skin_pa: float,
    t_skin_one_side_mm: float,
    t_core_mm: float,
    defaults: ThreePointBendingDefaults,
) -> dict[str, float]:
    elastic_gradient_corrected = (
        defaults.elastic_gradient * defaults.rigidez_rig
    ) / (defaults.rigidez_rig - defaults.elastic_gradient)
    ei_ensayo = elastic_gradient_corrected * 1000.0 * (defaults.span_m**3) / 48.0

    t_skin_m = t_skin_one_side_mm * 0.001
    t_core_m = t_core_mm * 0.001
    denominator = 0.5 * defaults.width_m * t_skin_m * ((t_skin_m + t_core_m) ** 2)

    ei_theory = denominator * e_skin_pa
    elastic_gradient_theory = 48.0 * ei_theory / ((defaults.span_m**3) * 1000.0)
    e_fibra_ensayo = 0.0 if denominator == 0.0 else ei_ensayo / denominator

    return {
        "elastic_gradient": defaults.elastic_gradient,
        "rigidez_rig": defaults.rigidez_rig,
        "elastic_gradient_corrected": elastic_gradient_corrected,
        "ei_ensayo": ei_ensayo,
        "e_fibra_ensayo": e_fibra_ensayo,
        "ei_theory": ei_theory,
        "elastic_gradient_theory": elastic_gradient_theory,
        "th_fibra_mm": t_skin_one_side_mm,
        "legacy_capa_central_value": t_core_mm,
    }
