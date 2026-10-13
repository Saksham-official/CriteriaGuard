from typing import Any

from rules.base import EligibilityRule, RuleResult


class MandatoryDocumentRule(EligibilityRule):
    """
    Evaluates mandatory compliance documents (e.g. ISO 9001 certificates,
    Bid Security / EMD, CA Net Worth certificates, Anti-Corruption declarations).

    Logic:
    - If evidence was not found and criterion is mandatory with high confidence -> Not Eligible
    - If evidence was not found and criterion is mandatory with ambiguous confidence -> Needs Review (AMBIGUOUS_CRITERION)
    - If evidence was not found and criterion is optional -> Eligible
    """

    rule_id = "mandatory_document"
    name = "Mandatory Document & Compliance Rule"
    description = "Verifies required tender documents, certificates, and submission checklists"

    def applies_to(self, criterion: dict[str, Any], evidence: dict[str, Any]) -> bool:
        # Applies if evidence value was not found, or if category is compliance/certification
        # without numeric threshold
        value_found = evidence.get("value_found", False)
        category = criterion.get("category", "")
        has_no_threshold = criterion.get("threshold_value") is None and not (
            isinstance(criterion.get("threshold"), dict)
            and criterion["threshold"].get("value") is not None
        )
        return not value_found or (category in ("compliance", "certification") and has_no_threshold)

    def evaluate(self, criterion: dict[str, Any], evidence: dict[str, Any]) -> RuleResult:
        value_found = evidence.get("value_found", False)
        is_mandatory = criterion.get("mandatory", False)
        mandatory_confidence = criterion.get("mandatory_confidence", "high")

        if not value_found:
            if is_mandatory:
                if mandatory_confidence == "ambiguous":
                    return RuleResult(
                        status="Needs Review",
                        reason="Value not found. Criterion is mandatory but originally marked as ambiguous by the system.",
                        review_sub_reason="AMBIGUOUS_CRITERION",
                    )
                else:
                    return RuleResult(
                        status="Not Eligible",
                        reason="Mandatory criterion value not found in submitted documents.",
                    )
            else:
                return RuleResult(
                    status="Eligible",
                    reason="Criterion is optional and value was not provided.",
                )

        # Document/value was found
        extracted_val = str(evidence.get("extracted_value", "")).lower()
        if "pending" in extracted_val or "expired" in extracted_val or "invalid" in extracted_val:
            return RuleResult(
                status="Needs Review",
                reason=f"Document was submitted but contains potential validity concerns: '{evidence.get('extracted_value')}'.",
                review_sub_reason="LOW_CONFIDENCE",
            )

        return RuleResult(
            status="Eligible",
            reason="Requirement satisfied based on extracted evidence.",
            metadata={"evidence_excerpt": evidence.get("source_excerpt")},
        )
