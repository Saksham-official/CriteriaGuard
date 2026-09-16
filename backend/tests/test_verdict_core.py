"""
Unit tests for CriteriaGuard VerdictCore deterministic evaluation engine.
Verifies that verdicts are computed with zero LLM hallucination, adhere to strict
threshold comparisons, and trigger human-in-the-loop review for borderline or tampered documents.
"""

import os
import sys
import unittest

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.verdict_core import compute_verdict


class TestVerdictCore(unittest.TestCase):
    def test_tampered_source_triggers_needs_review(self):
        criterion = {"id": "c1", "mandatory": True}
        extraction = {"value_found": True, "extraction_confidence": 0.95, "ocr_quality": "high"}

        result = compute_verdict(criterion, extraction, is_tampered_source=True)
        self.assertEqual(result["status"], "Needs Review")
        self.assertEqual(result["review_sub_reason"], "TAMPERING_WARNING")
        self.assertIn("CRITICAL RISK", result["reason"])

    def test_low_confidence_triggers_needs_review(self):
        criterion = {"id": "c2", "mandatory": True}
        extraction = {"value_found": True, "extraction_confidence": 0.65, "ocr_quality": "high"}

        result = compute_verdict(criterion, extraction)
        self.assertEqual(result["status"], "Needs Review")
        self.assertEqual(result["review_sub_reason"], "LOW_CONFIDENCE")

    def test_low_ocr_quality_triggers_needs_review(self):
        criterion = {"id": "c3", "mandatory": True}
        extraction = {"value_found": True, "extraction_confidence": 0.90, "ocr_quality": "low"}

        result = compute_verdict(criterion, extraction)
        self.assertEqual(result["status"], "Needs Review")
        self.assertEqual(result["review_sub_reason"], "LOW_OCR")

    def test_missing_mandatory_value_fails_eligibility(self):
        criterion = {"id": "c4", "mandatory": True, "mandatory_confidence": "high"}
        extraction = {"value_found": False, "extraction_confidence": 0.90, "ocr_quality": "high"}

        result = compute_verdict(criterion, extraction)
        self.assertEqual(result["status"], "Not Eligible")
        self.assertIn("Mandatory criterion value not found", result["reason"])

    def test_missing_ambiguous_mandatory_value_triggers_review(self):
        criterion = {"id": "c5", "mandatory": True, "mandatory_confidence": "ambiguous"}
        extraction = {"value_found": False, "extraction_confidence": 0.90, "ocr_quality": "high"}

        result = compute_verdict(criterion, extraction)
        self.assertEqual(result["status"], "Needs Review")
        self.assertEqual(result["review_sub_reason"], "AMBIGUOUS_CRITERION")

    def test_missing_optional_value_passes(self):
        criterion = {"id": "c6", "mandatory": False}
        extraction = {"value_found": False, "extraction_confidence": 0.90, "ocr_quality": "high"}

        result = compute_verdict(criterion, extraction)
        self.assertEqual(result["status"], "Eligible")

    def test_borderline_numeric_value_triggers_review(self):
        # 4.8 is within 10% of 5.0 (|4.8 - 5.0| / 5.0 = 0.04 < 0.10)
        criterion = {
            "id": "c7",
            "mandatory": True,
            "threshold_value": 5.0,
            "threshold_comparison": "greater_than_equal",
        }
        extraction = {
            "value_found": True,
            "extraction_confidence": 0.95,
            "ocr_quality": "high",
            "extracted_value_numeric": 4.8,
        }

        result = compute_verdict(criterion, extraction)
        self.assertEqual(result["status"], "Needs Review")
        self.assertEqual(result["review_sub_reason"], "BORDERLINE_VALUE")

    def test_numeric_threshold_passes_when_exceeding(self):
        # 8.5 clearly exceeds 5.0 (> 10% margin)
        criterion = {
            "id": "c8",
            "mandatory": True,
            "threshold_value": 5.0,
            "threshold_comparison": "greater_than_equal",
        }
        extraction = {
            "value_found": True,
            "extraction_confidence": 0.95,
            "ocr_quality": "high",
            "extracted_value_numeric": 8.5,
        }

        result = compute_verdict(criterion, extraction)
        self.assertEqual(result["status"], "Eligible")
        self.assertIn("meets requirement", result["reason"])

    def test_numeric_threshold_fails_when_below(self):
        # 2.0 is well below 5.0 (|2.0 - 5.0| / 5.0 = 0.60 >= 0.10)
        criterion = {
            "id": "c9",
            "mandatory": True,
            "threshold_value": 5.0,
            "threshold_comparison": "greater_than_equal",
        }
        extraction = {
            "value_found": True,
            "extraction_confidence": 0.95,
            "ocr_quality": "high",
            "extracted_value_numeric": 2.0,
        }

        result = compute_verdict(criterion, extraction)
        self.assertEqual(result["status"], "Not Eligible")
        self.assertIn("fails requirement", result["reason"])


if __name__ == "__main__":
    unittest.main()
