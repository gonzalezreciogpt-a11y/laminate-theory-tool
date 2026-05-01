from __future__ import annotations

import json
from numbers import Number

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.config import settings
from app.domain.materials import list_materials, material_to_dict
from app.schemas.batch import BatchCalculateRequestModel
from app.schemas.inputs import LaminateRequestModel
from app.schemas.results_export import ExportHistoryEntryModel, ExportResultsRequestModel, ExportSummaryModel
from app.services.legacy_compatibility import analyze_laminate
from app.services.results_export import build_export_filename, build_results_export_workbook
from app.services.sandwich_trace import build_visible_sandwich_layers
from app.web.forms import build_request_from_form


router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")
templates.env.globals["app_env"] = settings.app_env
templates.env.globals["app_base_url"] = settings.app_base_url
templates.env.globals["public_storage_notice"] = (
    "Servicio público: los cálculos se ejecutan en el servidor, pero los resultados, "
    "materiales personalizados y el estado de Shuffle se guardan solo en este navegador."
)


def _round_nested(value: object, digits: int = 3) -> object:
    if isinstance(value, list):
        return [_round_nested(item, digits) for item in value]
    if isinstance(value, Number):
        return round(float(value), digits)
    return value


def format_decimal(value: object, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, Number):
        return f"{float(value):.{digits}f}"
    return str(value)


def format_nested(value: object, digits: int = 3) -> str:
    return json.dumps(_round_nested(value, digits), ensure_ascii=False)


templates.env.filters["fmt3"] = format_decimal
templates.env.filters["fmt_nested"] = format_nested


def build_material_palette(generated_layers: list[object] | None) -> dict[str, str]:
    if not generated_layers:
        return {}
    palette = [
        "#15345f",
        "#c79a4f",
        "#2f6b4f",
        "#9a4d3c",
        "#5261a8",
        "#7a5f2f",
        "#2f7b90",
        "#6e447f",
    ]
    mapping: dict[str, str] = {}
    for layer in generated_layers:
        material_id = getattr(layer, "material_id", "")
        if (
            not material_id
            or material_id == "Dummy"
            or material_id in mapping
            or getattr(layer, "source", "") == "auto-core"
        ):
            continue
        mapping[material_id] = palette[len(mapping) % len(palette)]
    return mapping


def build_default_form_state() -> dict[str, object]:
    return {
        "layers": [
            {"material_id": "RC416T", "theta_deg": 45},
            {"material_id": "UD", "theta_deg": 0},
            {"material_id": "RC416T", "theta_deg": 90},
        ],
        "bottom_layers": [],
        "is_symmetric": True,
        "core_material_id": "Honeycomb",
        "insert_dummy_layer_for_odd_compatibility": False,
        "elastic_gradient": 2649.0,
        "rigidez_rig": 14871.0,
        "span_m": 0.4,
        "span_mm": 400.0,
        "width_m": 0.275,
        "width_mm": 275.0,
        "custom_materials": [],
    }


def _build_export_summary(
    request_model: LaminateRequestModel,
    result_model,
) -> ExportSummaryModel:
    visible_layers = (
        len(request_model.layers)
        if request_model.is_symmetric
        else len(request_model.layers) + len(request_model.bottom_layers)
    )
    return ExportSummaryModel(
        elastic_gradient_theory=result_model.three_point_bending.elastic_gradient_theory,
        ei_theory=result_model.three_point_bending.ei_theory,
        fiber_thickness_mm=result_model.three_point_bending.th_fibra_mm,
        total_thickness_mm=result_model.trace.espesor_total_mm,
        core_material_id=request_model.core_material_id,
        is_symmetric=request_model.is_symmetric if request_model.compatibility_mode == "physical" else False,
        visible_layers=visible_layers,
        panel_length_mm=request_model.three_point_bending.span_mm,
        panel_width_mm=request_model.three_point_bending.width_mm,
        laminate_sequence=_build_laminate_sequence_text(request_model),
    )


def _format_angle(theta_deg: float) -> str:
    value = float(theta_deg)
    absolute = abs(value)
    if absolute < 1e-12:
        return "0°"
    if absolute.is_integer():
        return f"±{int(absolute)}°"
    return f"±{absolute:.3f}".rstrip("0").rstrip(".") + "°"


def _build_laminate_sequence_text(request_model: LaminateRequestModel) -> str:
    top = " / ".join(_format_angle(layer.theta_deg) for layer in request_model.layers)
    core = f"Core {request_model.core_material_id}"
    if request_model.is_symmetric:
        return f"[{top}]s / {core}"
    bottom = " / ".join(_format_angle(layer.theta_deg) for layer in request_model.bottom_layers)
    if bottom:
        return f"{top} / {core} / {bottom}"
    return f"{top} / {core}"


def _normalize_export_entry(entry: ExportHistoryEntryModel) -> ExportHistoryEntryModel:
    request_model = LaminateRequestModel(**entry.form_state)
    result_model = analyze_laminate(request_model)
    normalized_form_state = request_model.model_dump()
    return ExportHistoryEntryModel(
        signature=entry.signature,
        saved_at=entry.saved_at,
        form_state=normalized_form_state,
        summary=_build_export_summary(request_model, result_model),
        results_html=entry.results_html,
        result_data=result_model.model_dump(),
    )


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    base_materials = [material_to_dict(material) for material in list_materials(public_only=True)]
    all_materials = [material_to_dict(material) for material in list_materials(public_only=False)]
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "materials": list_materials(public_only=True, category="fiber"),
            "core_materials": list_materials(public_only=True, category="core"),
            "base_materials_data": base_materials,
            "all_materials_data": all_materials,
            "form_state": build_default_form_state(),
            "result": None,
            "display_layers": [],
            "material_palette": {},
            "errors": [],
        },
    )


@router.post("/", response_class=HTMLResponse)
async def calculate(request: Request) -> HTMLResponse:
    form = await request.form()
    errors: list[str] = []
    result = None
    display_layers = []
    form_state = build_default_form_state()
    base_materials = [material_to_dict(material) for material in list_materials(public_only=True)]
    all_materials = [material_to_dict(material) for material in list_materials(public_only=False)]

    try:
        payload = build_request_from_form(form)
        form_state = {
            "layers": [layer.model_dump() for layer in payload.layers],
            "bottom_layers": [layer.model_dump() for layer in payload.bottom_layers],
            "is_symmetric": payload.is_symmetric,
            "core_material_id": payload.core_material_id,
            "insert_dummy_layer_for_odd_compatibility": payload.insert_dummy_layer_for_odd_compatibility,
            "elastic_gradient": payload.three_point_bending.elastic_gradient,
            "rigidez_rig": payload.three_point_bending.rigidez_rig,
            "span_m": payload.three_point_bending.span_m,
            "span_mm": payload.three_point_bending.span_mm,
            "width_m": payload.three_point_bending.width_m,
            "width_mm": payload.three_point_bending.width_mm,
            "custom_materials": [material.model_dump() for material in payload.custom_materials],
        }
        result = analyze_laminate(payload)
        display_layers = build_visible_sandwich_layers(payload)
    except (ValidationError, ValueError) as exc:
        errors = [str(exc)]

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "materials": list_materials(public_only=True, category="fiber"),
            "core_materials": list_materials(public_only=True, category="core"),
            "base_materials_data": base_materials,
            "all_materials_data": all_materials,
            "form_state": form_state,
            "result": result,
            "display_layers": display_layers,
            "material_palette": build_material_palette(result.generated_layers if result else None),
            "errors": errors,
        },
    )


@router.get("/materials-library", response_class=HTMLResponse)
async def materials_library(request: Request) -> HTMLResponse:
    base_materials = [material_to_dict(material) for material in list_materials(public_only=True)]
    return templates.TemplateResponse(
        request,
        "materials_library.html",
        {
            "base_materials_data": base_materials,
            "base_twill_materials": [
                material
                for material in base_materials
                if material["material_category"] == "fiber" and material.get("fiber_family") == "twill"
            ],
            "base_ud_materials": [
                material
                for material in base_materials
                if material["material_category"] == "fiber" and material.get("fiber_family") == "ud"
            ],
            "base_core_materials": [material for material in base_materials if material["material_category"] == "core"],
            "errors": [],
        },
    )


@router.get("/tutorial", response_class=HTMLResponse)
async def tutorial(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "tutorial.html",
        {
            "title": "Guia de uso",
        },
    )


@router.get("/results", response_class=HTMLResponse)
async def results_library(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "title": "Resultados",
        },
    )


@router.get("/compare", response_class=HTMLResponse)
async def compare_results(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "compare.html",
        {
            "title": "Comparador",
        },
    )


def _shuffle_page_context() -> dict[str, object]:
    base_materials = [material_to_dict(material) for material in list_materials(public_only=True)]
    all_materials = [material_to_dict(material) for material in list_materials(public_only=False)]
    return {
        "title": "Shuffle",
        "base_materials_data": base_materials,
        "all_materials_data": all_materials,
    }


@router.get("/shuffle", response_class=HTMLResponse)
async def shuffle(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "sweeps.html", _shuffle_page_context())


@router.get("/sweeps", response_class=HTMLResponse)
async def sweeps(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "sweeps.html", _shuffle_page_context())


@router.get("/healthz")
async def healthcheck() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@router.get("/api/materials")
async def api_materials() -> JSONResponse:
    return JSONResponse(
        [
            {
                "id": material.id,
                "name": material.name,
                "material_category": material.material_category,
                "e1_pa": material.e1_pa,
                "e2_pa": material.e2_pa,
                "g12_pa": material.g12_pa,
                "poisson_input": material.poisson_input,
                "fiber_family": material.fiber_family,
                "strength_x": material.strength_x,
                "strength_x_compression": material.strength_x_compression,
                "strength_y": material.strength_y,
                "strength_y_compression": material.strength_y_compression,
                "strength_s": material.strength_s,
                "thickness_mm": material.thickness_mm,
                "user_selectable": material.user_selectable,
                "notes": material.notes,
                "source": "base",
            }
            for material in list_materials(public_only=False)
        ]
    )


@router.post("/api/calculate")
async def api_calculate(payload: LaminateRequestModel) -> JSONResponse:
    return JSONResponse(analyze_laminate(payload).model_dump())


@router.post("/api/batch-calculate")
async def api_batch_calculate(payload: BatchCalculateRequestModel) -> JSONResponse:
    return JSONResponse(
        {
            "entries": [
                {
                    "label": entry.label,
                    "request": entry.request.model_dump(),
                    "result": analyze_laminate(entry.request).model_dump(),
                }
                for entry in payload.entries
            ]
        }
    )


@router.post("/api/export-results")
async def api_export_results(payload: ExportResultsRequestModel) -> StreamingResponse:
    normalized_entries = [_normalize_export_entry(entry) for entry in payload.entries]
    workbook_bytes = build_results_export_workbook(normalized_entries)
    filename = build_export_filename()
    return StreamingResponse(
        iter([workbook_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
