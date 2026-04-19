from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.inputs import LaminateRequestModel


class BatchCalculateEntryModel(BaseModel):
    label: str = Field(min_length=1)
    request: LaminateRequestModel


class BatchCalculateRequestModel(BaseModel):
    entries: list[BatchCalculateEntryModel]

    @field_validator("entries")
    @classmethod
    def ensure_entries_present(cls, value: list[BatchCalculateEntryModel]) -> list[BatchCalculateEntryModel]:
        if not value:
            raise ValueError("Debe existir al menos un caso para el barrido.")
        if len(value) > 60:
            raise ValueError("El barrido guiado admite como maximo 60 variantes por ejecucion.")
        return value
