from typing import Any

from rules import default_engine


def compute_verdict(
    criterion: dict[str, Any], extraction: dict[str, Any], is_tampered_source: bool = False
) -> dict[str, Any]:
    """
    Pure deterministic logic. Zero LLM hallucinations.
    Delegates to the modular RulesEngine to determine bidder qualification.

    Returns:
        dict containing:
          - status: ("Eligible" | "Not Eligible" | "Needs Review")
          - reason: Plain-language explanation for procurement officers
          - review_sub_reason: Optional subcategory for human review queue
    """
    result = default_engine.evaluate(
        criterion=criterion,
        evidence=extraction,
        is_tampered_source=is_tampered_source,
    )
    return result.to_dict()
