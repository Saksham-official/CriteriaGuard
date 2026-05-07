from pydantic import BaseModel, Field
from typing import Optional, List

class ThresholdSchema(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = Field(None, description="crore | lakh | number | years | null")
    period: Optional[str] = Field(None, description="annual | last_3_years | last_5_years | null")
    comparison: Optional[str] = Field(None, description="greater_than_equal | equal | at_least_count | null")

class CriterionSchema(BaseModel):
    id: str
    text: str = Field(..., description="Exact text from document, verbatim")
    category: str = Field(..., description="financial | technical | compliance | certification")
    mandatory: bool
    mandatory_confidence: str = Field(..., description="high | ambiguous")
    threshold: Optional[ThresholdSchema] = None
    evidence_documents: List[str]
    source_clause: str = Field(..., description="e.g. Clause 4.2(b) or Section 3")
    source_page: Optional[int] = Field(1, description="The page number where the criterion was found")
