from __future__ import annotations

from pydantic import BaseModel, Field


class ExportSummaryModel(BaseModel):
    elastic_gradient_theory: float
    ei_theory: float
    fiber_thickness_mm: float
    total_thickness_mm: float
    core_material_id: str
    is_symmetric: bool
    visible_layers: int
    panel_length_mm: float = 400.0
    panel_width_mm: float = 275.0
    laminate_sequence: str = ""


class ExportHistoryEntryModel(BaseModel):
    signature: str
    saved_at: str | None = None
    form_state: dict[str, object]
    summary: ExportSummaryModel
    results_html: str | None = None
    result_data: dict[str, object] = Field(default_factory=dict)


class ExportResultsRequestModel(BaseModel):
    entries: list[ExportHistoryEntryModel]
