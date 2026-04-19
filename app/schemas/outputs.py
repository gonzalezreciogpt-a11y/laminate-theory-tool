from __future__ import annotations

from pydantic import BaseModel


class GeneratedLayerModel(BaseModel):
    index: int
    material_id: str
    material_name: str
    theta_deg: float
    thickness_mm: float
    source: str


class EquivalentPropertiesModel(BaseModel):
    e11_pa: float
    e22_pa: float
    g122_pa: float
    nu12: float
    nu21: float
    g12g_pa: float
    e11_gpa: float
    e22_gpa: float
    g122_gpa: float
    g12g_gpa: float


class ThreePointBendingResultModel(BaseModel):
    elastic_gradient: float
    rigidez_rig: float
    elastic_gradient_corrected: float
    ei_ensayo: float
    e_fibra_ensayo: float
    ei_theory: float
    elastic_gradient_theory: float
    th_fibra_mm: float
    legacy_capa_central_value: float


class TraceModel(BaseModel):
    espesor_total_mm: float
    z_mm: list[float]
    a_matrix: list[list[float]]
    b_matrix: list[list[float]]
    d_matrix: list[list[float]]
    a1_matrix: list[list[float]]
    d1_matrix: list[list[float]]
    last_nu12_used_for_g12g: float


class LaminateAnalysisResponseModel(BaseModel):
    materials_catalog_used: list[str]
    generated_layers: list[GeneratedLayerModel]
    warnings: list[str]
    equivalent_properties: EquivalentPropertiesModel
    three_point_bending: ThreePointBendingResultModel
    trace: TraceModel
