from typing import Any

from rules.base import EligibilityRule, RuleResult


class NumericThresholdRule(EligibilityRule):
    """
    Evaluates criteria with numerical thresholds (e.g. turnover in Crores/USD,
    net worth, minimum asset values).

    Features:
    - Supports multiple comparison operators (greater_than_equal, equal, at_least_count, less_than_equal)
    - Automatic borderline detection: Values within 10% of the threshold are flagged for human officer review
    - Strict parsing safety: Unparseable numeric values trigger Needs Review with PARSE_ERROR
    """

    rule_id = "numeric_threshold"
    name = "Numeric Threshold Rule"
    description = "Evaluates numeric thresholds with borderline margin detection"

    def applies_to(self, criterion: dict[str, Any], evidence: dict[str, Any]) -> bool:
        # Check if threshold value is specified directly or in nested threshold dict
        has_direct = criterion.get("threshold_value") is not None
        has_nested = (
            isinstance(criterion.get("threshold"), dict)
            and criterion["threshold"].get("value") is not None
        )
        return has_direct or has_nested

    def evaluate(self, criterion: dict[str, Any], evidence: dict[str, Any]) -> RuleResult:
        # Extract threshold value and comparison operator
        raw_threshold = criterion.get("threshold_value")
        comp = criterion.get("threshold_comparison")

        if raw_threshold is None and isinstance(criterion.get("threshold"), dict):
            raw_threshold = criterion["threshold"].get("value")
            if not comp:
                comp = criterion["threshold"].get("comparison")

        if raw_threshold is None:
            return RuleResult(
                status="Needs Review",
                reason="Criterion indicated a threshold but threshold_value was missing.",
                review_sub_reason="PARSE_ERROR",
            )

        extracted_num = evidence.get("extracted_value_numeric")
        if extracted_num is None:
            return RuleResult(
                status="Needs Review",
                reason="Numerical threshold exists but extracted value could not be reliably parsed as a number.",
                review_sub_reason="PARSE_ERROR",
            )

        try:
            threshold = float(raw_threshold)
            extracted_num = float(extracted_num)
        except (ValueError, TypeError):
            return RuleResult(
                status="Needs Review",
                reason="Failed to parse threshold or extracted evidence as a valid float.",
                review_sub_reason="PARSE_ERROR",
            )

        # Borderline detection: Within 10% of threshold requires manual validation
        if threshold > 0:
            diff_percent = abs(extracted_num - threshold) / threshold
            if diff_percent < 0.10:
                return RuleResult(
                    status="Needs Review",
                    reason=f"Value {extracted_num} is within 10% of threshold {threshold}. Manual validation required for borderline case.",
                    review_sub_reason="BORDERLINE_VALUE",
                    metadata={"difference_percent": round(diff_percent * 100, 2)},
                )

        # Operator evaluation
        comp_str = str(comp or "greater_than_equal").lower()
        passed = False
        if comp_str in ("greater_than_equal", "at_least_count", ">="):
            passed = extracted_num >= threshold
        elif comp_str in ("equal", "=="):
            passed = extracted_num == threshold
        elif comp_str in ("greater_than", ">"):
            passed = extracted_num > threshold
        elif comp_str in ("less_than_equal", "<="):
            passed = extracted_num <= threshold
        elif comp_str in ("less_than", "<"):
            passed = extracted_num < threshold
        else:
            # Default fallback for threshold evaluation
            passed = extracted_num >= threshold

        if passed:
            return RuleResult(
                status="Eligible",
                reason=f"Value {extracted_num} meets requirement of {comp_str} {threshold}.",
                metadata={"extracted": extracted_num, "threshold": threshold, "operator": comp_str},
            )
        else:
            return RuleResult(
                status="Not Eligible",
                reason=f"Value {extracted_num} fails requirement of {comp_str} {threshold}.",
                metadata={"extracted": extracted_num, "threshold": threshold, "operator": comp_str},
            )
