from pydantic import BaseModel, Field
from typing import Optional

class ExtractionSchema(BaseModel):
    criterion_id: str
    value_found: bool
    not_found_reason: Optional[str] = Field(None, description="document_missing | value_unreadable | not_stated | null")
    extracted_value: Optional[str] = None
    extracted_value_numeric: Optional[float] = None
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    source_excerpt: Optional[str] = None
    ocr_quality: str = Field(..., description="high | medium | low")
    alignment_score: float = Field(..., description="0.0 to 1.0")
    authenticity_score: float = Field(..., description="0.0 to 1.0")
    notes: Optional[str] = None
