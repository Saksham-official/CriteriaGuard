from pydantic import BaseModel, Field


class ThresholdSchema(BaseModel):
    value: float | None = None
    unit: str | None = Field(None, description="crore | lakh | number | years | null")
    period: str | None = Field(None, description="annual | last_3_years | last_5_years | null")
    comparison: str | None = Field(
        None, description="greater_than_equal | equal | at_least_count | null"
    )


class CriterionSchema(BaseModel):
    id: str
    text: str = Field(..., description="Exact text from document, verbatim")
    category: str = Field(..., description="financial | technical | compliance | certification")
    mandatory: bool
    mandatory_confidence: str = Field(..., description="high | ambiguous")
    threshold: ThresholdSchema | None = None
    evidence_documents: list[str]
    source_clause: str = Field(..., description="e.g. Clause 4.2(b) or Section 3")
    source_page: int | None = Field(1, description="The page number where the criterion was found")
