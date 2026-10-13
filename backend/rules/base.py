from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleResult:
    """
    Standard output format for all CriteriaGuard eligibility rules.
    Guarantees deterministic, explainable verdicts without LLM ambiguity.
    """

    status: str  # "Eligible" | "Not Eligible" | "Needs Review"
    reason: str
    review_sub_reason: str | None = None  # e.g. "BORDERLINE_VALUE", "LOW_CONFIDENCE", "PARSE_ERROR"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary matching legacy VerdictCore format."""
        out: dict[str, Any] = {
            "status": self.status,
            "reason": self.reason,
        }
        if self.review_sub_reason:
            out["review_sub_reason"] = self.review_sub_reason
        if self.metadata:
            out["metadata"] = self.metadata
        return out


class EligibilityRule(ABC):
    """
    Abstract base class for all deterministic eligibility rules.
    Contributors can subclass this to add domain-specific rules (e.g., turnover,
    personnel experience, certifications, JV consortium limits).
    """

    rule_id: str = "base_rule"
    name: str = "Base Eligibility Rule"
    description: str = "Abstract base rule"

    @abstractmethod
    def applies_to(self, criterion: dict[str, Any], evidence: dict[str, Any]) -> bool:
        """Return True if this rule should evaluate the given criterion and evidence."""
        pass

    @abstractmethod
    def evaluate(self, criterion: dict[str, Any], evidence: dict[str, Any]) -> RuleResult:
        """
        Pure deterministic evaluation logic.
        Must NOT call external LLM APIs.
        """
        pass
