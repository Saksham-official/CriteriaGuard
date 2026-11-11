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

from engines.ambiguity_resolver import resolve_ambiguity
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


class TestDeonticModalClassification(unittest.TestCase):
    """
    Tests for mandatory vs optional clause classification based on deontic
    modal markers ("shall"/"must" = binding obligation vs "should"/"may" =
    advisory preference), exercised through the deterministic offline path
    of resolve_ambiguity (MOCK_LLM=true, no API key needed).
    """

    def setUp(self):
        self._old_mock = os.environ.get("MOCK_LLM")
        os.environ["MOCK_LLM"] = "true"

    def tearDown(self):
        if self._old_mock is None:
            os.environ.pop("MOCK_LLM", None)
        else:
            os.environ["MOCK_LLM"] = self._old_mock

    # --- Obligation phrasing: binding requirements ---

    def test_shall_clause_is_mandatory(self):
        result = resolve_ambiguity(
            "The bidder shall submit audited financial statements for the last three years.",
            "Clause 4.1",
        )
        self.assertTrue(result["likely_mandatory"])
        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["recommendation"], "recommend confirming as mandatory")

    def test_must_clause_is_mandatory(self):
        result = resolve_ambiguity(
            "The contractor must possess a valid ISO 9001:2015 certification.",
            "Clause 4.3",
        )
        self.assertTrue(result["likely_mandatory"])
        self.assertEqual(result["confidence"], "high")

    def test_strictly_required_clause_is_mandatory(self):
        result = resolve_ambiguity(
            "A performance bank guarantee is strictly required at the time of signing.",
            "Clause 7.2",
        )
        self.assertTrue(result["likely_mandatory"])
        self.assertEqual(result["recommendation"], "recommend confirming as mandatory")

    def test_required_clause_is_mandatory(self):
        result = resolve_ambiguity(
            "The bidder is required to provide earnest money deposit with the bid.",
            "Clause 5.1",
        )
        self.assertTrue(result["likely_mandatory"])

    def test_shall_not_prohibition_is_mandatory(self):
        result = resolve_ambiguity(
            "The vendor shall not subcontract any portion of the work without written approval.",
            "Clause 9.4",
        )
        self.assertTrue(result["likely_mandatory"])
        self.assertEqual(result["confidence"], "high")

    # --- Preference phrasing: advisory, not binding ---

    def test_should_clause_is_not_mandatory(self):
        result = resolve_ambiguity(
            "The bidder should preferably have completed similar government projects.",
            "Clause 3.6",
        )
        self.assertFalse(result["likely_mandatory"])
        self.assertEqual(result["recommendation"], "recommend confirming as optional")

    def test_desirable_clause_is_not_mandatory(self):
        result = resolve_ambiguity(
            "Prior experience with municipal contracts is desirable but not essential.",
            "Clause 3.7",
        )
        self.assertFalse(result["likely_mandatory"])

    def test_preferred_clause_is_not_mandatory(self):
        result = resolve_ambiguity(
            "It is preferred that the bidder maintain a local service office.",
            "Clause 3.8",
        )
        self.assertFalse(result["likely_mandatory"])
        self.assertEqual(result["confidence"], "medium")

    def test_may_clause_is_not_mandatory(self):
        result = resolve_ambiguity(
            "The bidder may submit additional supporting documents with the proposal.",
            "Clause 2.9",
        )
        self.assertFalse(result["likely_mandatory"])
        self.assertEqual(result["recommendation"], "recommend confirming as optional")

    def test_should_clause_confidence_is_not_high(self):
        result = resolve_ambiguity(
            "Bidders should demonstrate familiarity with the regional market.",
            "Clause 3.9",
        )
        self.assertFalse(result["likely_mandatory"])
        self.assertNotEqual(result["confidence"], "high")

    # --- Ambiguous clauses default to human officer review ---

    def test_clause_without_deontic_marker_is_not_high_confidence(self):
        result = resolve_ambiguity(
            "The bidder has completed two projects of comparable scale in the region.",
            "Clause 3.10",
        )
        self.assertNotEqual(result["confidence"], "high")

    def test_ambiguous_mandatory_criterion_defaults_to_needs_review(self):
        # A clause whose mandatory status could not be classified with high
        # confidence is stored with mandatory_confidence="ambiguous"; when
        # its value is missing the verdict must go to a human officer.
        criterion = {"id": "d1", "mandatory": True, "mandatory_confidence": "ambiguous"}
        extraction = {"value_found": False, "extraction_confidence": 0.90, "ocr_quality": "high"}

        result = compute_verdict(criterion, extraction)
        self.assertEqual(result["status"], "Needs Review")
        self.assertEqual(result["review_sub_reason"], "AMBIGUOUS_CRITERION")


if __name__ == "__main__":
    unittest.main()
