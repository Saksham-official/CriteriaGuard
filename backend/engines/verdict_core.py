from typing import Dict, Any

def compute_verdict(criterion: Dict[str, Any], extraction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure deterministic logic. No LLM calls here.
    Returns: status (Eligible, Not Eligible, Needs Review), reason, review_sub_reason (optional)
    """
    # 1. Low OCR quality or low confidence always needs human review
    confidence = extraction.get("extraction_confidence", 0)
    ocr_quality = extraction.get("ocr_quality", "high")
    
    if confidence < 0.7:
        return {
            "status": "Needs Review",
            "reason": f"System confidence is low ({confidence:.2f}). Officer verification required.",
            "review_sub_reason": "LOW_CONFIDENCE"
        }
    
    if ocr_quality == "low":
        return {
            "status": "Needs Review",
            "reason": "OCR quality was poor, making the extraction potentially unreliable.",
            "review_sub_reason": "LOW_OCR"
        }
        
    # 2. Check if value was found
    if not extraction.get("value_found", False):
        if criterion.get("mandatory", False):
            if criterion.get("mandatory_confidence") == "ambiguous":
                return {
                    "status": "Needs Review",
                    "reason": "Value not found. Criterion is mandatory but originally marked as ambiguous by the system.",
                    "review_sub_reason": "AMBIGUOUS_CRITERION"
                }
            else:
                return {
                    "status": "Not Eligible",
                    "reason": "Mandatory criterion value not found in submitted documents."
                }
        else:
            # Not mandatory, so missing it doesn't fail them
            return {
                "status": "Eligible",
                "reason": "Criterion is optional and value was not provided."
            }
            
    # 3. If value is found, evaluate threshold if it exists
    if criterion.get("threshold_value") is not None:
        extracted_num = extraction.get("extracted_value_numeric")
        if extracted_num is None:
            return {
                "status": "Needs Review",
                "reason": "Numerical threshold exists but extracted value could not be reliably parsed as a number.",
                "review_sub_reason": "PARSE_ERROR"
            }
            
        threshold = float(criterion["threshold_value"])
        extracted_num = float(extracted_num)
        comp = criterion.get("threshold_comparison")
        
        # Borderline detection (within 10% of threshold)
        if threshold > 0:
            diff_percent = abs(extracted_num - threshold) / threshold
            if diff_percent < 0.10:
                return {
                    "status": "Needs Review",
                    "reason": f"Value {extracted_num} is within 10% of threshold {threshold}. Manual validation required for borderline case.",
                    "review_sub_reason": "BORDERLINE_VALUE"
                }

        passed = False
        if comp == "greater_than_equal" or comp == "at_least_count":
            passed = extracted_num >= threshold
        elif comp == "equal":
            passed = extracted_num == threshold
        else:
            # Default fallback if unknown comparison
            passed = extracted_num >= threshold
            
        if passed:
            return {
                "status": "Eligible",
                "reason": f"Value {extracted_num} meets requirement of {comp} {threshold}."
            }
        else:
            return {
                "status": "Not Eligible",
                "reason": f"Value {extracted_num} fails requirement of {comp} {threshold}."
            }
            
    # 4. If value found and no threshold, they pass this criterion
    return {
        "status": "Eligible",
        "reason": "Requirement satisfied based on extracted evidence."
    }
