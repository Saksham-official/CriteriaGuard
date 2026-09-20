from pydantic import BaseModel, Field


class ExtractionSchema(BaseModel):
    criterion_id: str
    value_found: bool
    not_found_reason: str | None = Field(
        None, description="document_missing | value_unreadable | not_stated | null"
    )
    extracted_value: str | None = None
    extracted_value_numeric: float | None = None
    source_document: str | None = None
    source_page: int | None = None
    source_excerpt: str | None = None
    ocr_quality: str = Field(..., description="high | medium | low")
    alignment_score: float = Field(..., description="0.0 to 1.0")
    authenticity_score: float = Field(..., description="0.0 to 1.0")
    notes: str | None = None
