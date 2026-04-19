from __future__ import annotations

from app.domain.laminate import LaminateDefinition, LayerInput
from app.domain.materials import Material
from app.domain.materials import load_three_point_bending_defaults
from app.schemas.inputs import LaminateRequestModel
from app.schemas.outputs import (
    EquivalentPropertiesModel,
    GeneratedLayerModel,
    LaminateAnalysisResponseModel,
    ThreePointBendingResultModel,
    TraceModel,
)
from app.services.clt_core import compute_legacy_abd, compute_legacy_z_positions_mm
from app.services.equivalent_properties import compute_equivalent_properties
from app.services.laminate_builder import build_laminate
from app.services.three_point_bending import compute_three_point_bending
from app.services.validators import validate_request


def analyze_laminate(request: LaminateRequestModel) -> LaminateAnalysisResponseModel:
    warnings = validate_request(request)
    definition = LaminateDefinition(
        layers=[
            LayerInput(material_id=layer.material_id, theta_deg=layer.theta_deg)
            for layer in request.layers
        ],
        is_symmetric=request.is_symmetric,
        core_material_id=request.core_material_id,
        insert_dummy_layer_for_odd_compatibility=request.insert_dummy_layer_for_odd_compatibility,
        compatibility_mode=request.compatibility_mode,
        bending_defaults=load_three_point_bending_defaults(),
        custom_materials=[
            Material(
                id=material.id,
                name=material.name,
                material_category=material.material_category,
                e1_pa=material.e1_pa,
                e2_pa=material.e2_pa,
                g12_pa=material.g12_pa,
                poisson_input=material.poisson_input,
                strength_x=material.strength_x,
                strength_x_compression=material.strength_x_compression,
                strength_y=material.strength_y,
                strength_y_compression=material.strength_y_compression,
                strength_s=material.strength_s,
                thickness_mm=material.thickness_mm,
                user_selectable=material.user_selectable,
                notes=material.notes,
                fiber_family=material.fiber_family,
            )
            for material in request.custom_materials
        ],
    )
    laminate = build_laminate(definition)
    z_mm, total_thickness_mm, legacy_capa_central_value = compute_legacy_z_positions_mm(laminate)
    a_matrix, b_matrix, d_matrix, last_nu12 = compute_legacy_abd(laminate, z_mm)
    equivalent = compute_equivalent_properties(a_matrix, d_matrix, total_thickness_mm, last_nu12)
    bending = compute_three_point_bending(
        e1_p_manual=equivalent["e11_pa"],
        total_thickness_mm=total_thickness_mm,
        legacy_capa_central_value=legacy_capa_central_value,
        defaults=definition.bending_defaults or load_three_point_bending_defaults(),
    )

    warnings.extend(laminate.warnings)
    warnings.append(
        "El modo legado conserva la convencion MATLAB en la que G12G usa el nu12 de la ultima capa, no el nu12 equivalente del laminado."
    )
    if laminate.is_symmetric and len(laminate.layers) % 2 == 1:
        warnings.append(
            "En modo legado simetrico impar, el calculo especial de z central se sobrescribe durante la reflexion para reproducir MATLAB."
        )

    generated_layers = [
        GeneratedLayerModel(
            index=layer.index,
            material_id=layer.material.id,
            material_name=layer.material.name,
            theta_deg=layer.theta_deg,
            thickness_mm=layer.material.thickness_mm,
            source=layer.source,
        )
        for layer in laminate.layers
    ]

    trace = TraceModel(
        espesor_total_mm=total_thickness_mm,
        z_mm=z_mm,
        a_matrix=a_matrix.tolist(),
        b_matrix=b_matrix.tolist(),
        d_matrix=d_matrix.tolist(),
        a1_matrix=equivalent["a1_matrix"],
        d1_matrix=equivalent["d1_matrix"],
        last_nu12_used_for_g12g=last_nu12,
    )

    return LaminateAnalysisResponseModel(
        materials_catalog_used=[layer.material.id for layer in laminate.layers],
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
