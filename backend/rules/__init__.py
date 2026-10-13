"""
CriteriaGuard Rules Engine
---------------------------
Modular, deterministic evaluation engine for government procurement eligibility.
Allows open-source contributors to add custom rules without modifying core LLM pipelines.
"""

from typing import Any

from rules.base import EligibilityRule, RuleResult
from rules.experience_requirement import ExperienceRequirementRule
from rules.mandatory_document import MandatoryDocumentRule
from rules.numeric_threshold import NumericThresholdRule


class RulesEngine:
    """
    Central dispatcher for deterministic procurement eligibility evaluation.
    Evaluates criteria against extracted evidence in strict deterministic order.
    """

    def __init__(self):
        self.rules: list[EligibilityRule] = []
        self._register_default_rules()

    def _register_default_rules(self):
        # Numeric thresholds and borderline checks take priority
        self.register_rule(NumericThresholdRule())
        self.register_rule(ExperienceRequirementRule())
        self.register_rule(MandatoryDocumentRule())

    def register_rule(self, rule: EligibilityRule):
        """Register a new eligibility rule into the engine."""
        self.rules.append(rule)

    def evaluate(
        self,
        criterion: dict[str, Any],
        evidence: dict[str, Any],
        is_tampered_source: bool = False,
    ) -> RuleResult:
        """
        Evaluate a single criterion against extracted bidder evidence.
        Guarantees explainability, zero LLM hallucinations, and safety checkpoints.
        """
        # 0. Document tampering check
        if is_tampered_source:
            return RuleResult(
                status="Needs Review",
                reason="CRITICAL RISK: Mismatched metadata or editing software signature detected in the source document.",
                review_sub_reason="TAMPERING_WARNING",
            )

        # 1. Extraction confidence check
        confidence = float(evidence.get("extraction_confidence", 1.0) or 0.0)
        ocr_quality = str(evidence.get("ocr_quality", "high")).lower()

        if confidence < 0.7:
            return RuleResult(
                status="Needs Review",
                reason=f"System confidence is low ({confidence:.2f}). Officer verification required.",
                review_sub_reason="LOW_CONFIDENCE",
            )

        # 2. OCR Quality check
        if ocr_quality == "low":
            return RuleResult(
                status="Needs Review",
                reason="OCR quality was poor, making the extraction potentially unreliable.",
                review_sub_reason="LOW_OCR",
            )

        # 3. Check if value was missing
        if not evidence.get("value_found", False):
            # Let MandatoryDocumentRule handle missing values
            doc_rule = MandatoryDocumentRule()
            return doc_rule.evaluate(criterion, evidence)

        # 4. Evaluate registered rules in sequence
        for rule in self.rules:
            if rule.applies_to(criterion, evidence):
                return rule.evaluate(criterion, evidence)

        # 5. Default pass if value was found and no failing constraints were triggered
        return RuleResult(
            status="Eligible",
            reason="Requirement satisfied based on extracted evidence.",
        )


# Global default engine instance
default_engine = RulesEngine()

__all__ = [
    "EligibilityRule",
    "RuleResult",
    "NumericThresholdRule",
    "MandatoryDocumentRule",
    "ExperienceRequirementRule",
    "RulesEngine",
    "default_engine",
]
