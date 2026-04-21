from __future__ import annotations

import numpy as np

from app.domain.materials import load_three_point_bending_defaults
from app.schemas.inputs import LaminateRequestModel
from app.schemas.outputs import (
    EquivalentPropertiesModel,
    GeneratedLayerModel,
    LaminateAnalysisResponseModel,
    ThreePointBendingResultModel,
    TraceModel,
)
from app.services.equivalent_properties import compute_equivalent_properties_physical
from app.services.sandwich_trace import (
    build_visible_sandwich_layers,
    compute_top_skin_trace,
    compute_visible_sandwich_trace,
)
from app.services.three_point_bending import compute_three_point_bending_physical
from app.services.validators import validate_request


def analyze_laminate_physical(request: LaminateRequestModel) -> LaminateAnalysisResponseModel:
    warnings = validate_request(request)
    display_layers = build_visible_sandwich_layers(request)
    sandwich_trace = compute_visible_sandwich_trace(request)
    top_skin_trace = compute_top_skin_trace(request)

    a_matrix = np.array(sandwich_trace.a_matrix, dtype=float)
    d_matrix = np.array(sandwich_trace.d_matrix, dtype=float)
    top_skin_a = np.array(top_skin_trace.a_matrix, dtype=float)
    top_skin_d = np.array(top_skin_trace.d_matrix, dtype=float)

    equivalent = compute_equivalent_properties_physical(
        a_matrix=a_matrix,
        d_matrix=d_matrix,
        total_thickness_mm=sandwich_trace.total_thickness_mm,
    )
    top_skin_equivalent = compute_equivalent_properties_physical(
        a_matrix=top_skin_a,
        d_matrix=top_skin_d,
        total_thickness_mm=top_skin_trace.total_thickness_mm,
    )

    core_layer = next(layer for layer in display_layers if layer.zone == "core")
    bending = compute_three_point_bending_physical(
        e_skin_pa=float(top_skin_equivalent["e11_pa"]),
        t_skin_one_side_mm=top_skin_trace.total_thickness_mm,
        t_core_mm=core_layer.thickness_mm,
        defaults=request.three_point_bending or load_three_point_bending_defaults(),
    )

    generated_layers = [
        GeneratedLayerModel(
            index=layer.index,
            material_id=layer.material_id,
            material_name=layer.material_name,
            theta_deg=layer.theta_deg,
            thickness_mm=layer.thickness_mm,
            source=layer.source,
        )
        for layer in display_layers
    ]

    trace = TraceModel(
        espesor_total_mm=sandwich_trace.total_thickness_mm,
        z_mm=sandwich_trace.z_interfaces_mm,
        a_matrix=sandwich_trace.a_matrix,
        b_matrix=sandwich_trace.b_matrix,
        d_matrix=sandwich_trace.d_matrix,
        a1_matrix=equivalent["a1_matrix"],
        d1_matrix=equivalent["d1_matrix"],
        last_nu12_used_for_g12g=float(equivalent["nu12"]),
    )

    return LaminateAnalysisResponseModel(
        materials_catalog_used=[layer.material_id for layer in display_layers],
        generated_layers=generated_layers,
        warnings=warnings,
        equivalent_properties=EquivalentPropertiesModel(
            e11_pa=equivalent["e11_pa"],
            e22_pa=equivalent["e22_pa"],
            g122_pa=equivalent["g122_pa"],
            nu12=equivalent["nu12"],
            nu21=equivalent["nu21"],
            g12g_pa=equivalent["g12g_pa"],
            e11_gpa=equivalent["e11_gpa"],
            e22_gpa=equivalent["e22_gpa"],
            g122_gpa=equivalent["g122_gpa"],
            g12g_gpa=equivalent["g12g_gpa"],
        ),
        three_point_bending=ThreePointBendingResultModel(**bending),
        trace=trace,
    )
