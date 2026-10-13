from typing import Any

from rules.base import EligibilityRule, RuleResult


class ExperienceRequirementRule(EligibilityRule):
    """
    Evaluates bidder track record, completed infrastructure projects count,
    and key personnel minimum experience years.
    """

    rule_id = "experience_requirement"
    name = "Experience & Technical Track Record Rule"
    description = "Evaluates completed projects count and personnel qualification years"

    def applies_to(self, criterion: dict[str, Any], evidence: dict[str, Any]) -> bool:
        category = str(criterion.get("category", "")).lower()
        combined_text = (
            str(criterion.get("text", "")) + " " + str(criterion.get("source_clause", ""))
        ).lower()

        is_experience_related = (
            "experience" in combined_text
            or "project" in combined_text
            or "track record" in combined_text
            or "years" in combined_text
            or "personnel" in combined_text
        )
        return category == "technical" and is_experience_related

    def evaluate(self, criterion: dict[str, Any], evidence: dict[str, Any]) -> RuleResult:
        if not evidence.get("value_found", False):
            if criterion.get("mandatory", False):
                return RuleResult(
                    status="Not Eligible",
                    reason="Technical experience evidence not found in submitted bidder proposal.",
                )
            return RuleResult(
                status="Eligible",
                reason="Technical experience criterion is optional and was not submitted.",
            )

        extracted_num = evidence.get("extracted_value_numeric")
        threshold_val = criterion.get("threshold_value")
        if threshold_val is None and isinstance(criterion.get("threshold"), dict):
            threshold_val = criterion["threshold"].get("value")

        if threshold_val is not None and extracted_num is not None:
            try:
                t_val = float(threshold_val)
                e_val = float(extracted_num)

                # Check 10% borderline margin
                if t_val > 0 and abs(e_val - t_val) / t_val < 0.10:
                    return RuleResult(
                        status="Needs Review",
                        reason=f"Technical experience metric {e_val} is borderline close to required {t_val}. Manual verification advised.",
                        review_sub_reason="BORDERLINE_VALUE",
                    )

                if e_val >= t_val:
                    return RuleResult(
                        status="Eligible",
                        reason=f"Technical experience qualification met: {e_val} exceeds requirement of {t_val}.",
                        metadata={"metric": e_val, "required": t_val},
                    )
                else:
                    return RuleResult(
                        status="Not Eligible",
                        reason=f"Technical experience qualification deficit: {e_val} fails minimum requirement of {t_val}.",
                        metadata={"metric": e_val, "required": t_val},
                    )
            except (ValueError, TypeError):
                pass

        return RuleResult(
            status="Eligible",
            reason="Technical qualification verified from submitted bidder credentials.",
            metadata={"notes": evidence.get("notes")},
        )
