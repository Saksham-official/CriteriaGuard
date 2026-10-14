"""
Unit tests for NumericThresholdRule.
Verifies pure deterministic threshold comparisons, borderline flags (10%), and parse safety.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rules.numeric_threshold import NumericThresholdRule


class TestNumericThresholdRule(unittest.TestCase):
    def setUp(self):
        self.rule = NumericThresholdRule()

    def test_applies_to_numeric_criterion(self):
        self.assertTrue(self.rule.applies_to({"threshold_value": 50.0}, {}))
        self.assertTrue(self.rule.applies_to({"threshold": {"value": 50.0}}, {}))
        self.assertFalse(self.rule.applies_to({"threshold": None}, {}))
        self.assertFalse(self.rule.applies_to({}, {}))

    def test_exceeds_threshold_is_eligible(self):
        criterion = {"threshold_value": 50000000.0, "threshold_comparison": "greater_than_equal"}
        evidence = {"extracted_value_numeric": 75000000.0, "value_found": True}

        result = self.rule.evaluate(criterion, evidence)
        self.assertEqual(result.status, "Eligible")
        self.assertIn("meets requirement", result.reason)

    def test_below_threshold_is_not_eligible(self):
        criterion = {"threshold_value": 50000000.0, "threshold_comparison": "greater_than_equal"}
        evidence = {"extracted_value_numeric": 35000000.0, "value_found": True}

        result = self.rule.evaluate(criterion, evidence)
        self.assertEqual(result.status, "Not Eligible")
        self.assertIn("fails requirement", result.reason)

    def test_borderline_value_triggers_needs_review(self):
        # 49.5M is within 10% of 50M threshold (1% diff)
        criterion = {"threshold_value": 50000000.0, "threshold_comparison": "greater_than_equal"}
        evidence = {"extracted_value_numeric": 49500000.0, "value_found": True}

        result = self.rule.evaluate(criterion, evidence)
        self.assertEqual(result.status, "Needs Review")
        self.assertEqual(result.review_sub_reason, "BORDERLINE_VALUE")
        self.assertIn("within 10% of threshold", result.reason)

    def test_borderline_upper_triggers_needs_review(self):
        # 52M is within 10% of 50M threshold (4% diff)
        criterion = {"threshold_value": 50000000.0, "threshold_comparison": "greater_than_equal"}
        evidence = {"extracted_value_numeric": 52000000.0, "value_found": True}

        result = self.rule.evaluate(criterion, evidence)
        self.assertEqual(result.status, "Needs Review")
        self.assertEqual(result.review_sub_reason, "BORDERLINE_VALUE")

    def test_unparseable_value_triggers_parse_error(self):
        criterion = {"threshold_value": 50000000.0}
        evidence = {"extracted_value_numeric": None, "value_found": True}

        result = self.rule.evaluate(criterion, evidence)
        self.assertEqual(result.status, "Needs Review")
        self.assertEqual(result.review_sub_reason, "PARSE_ERROR")

    def test_nested_threshold_dict_supported(self):
        criterion = {
            "threshold": {
                "value": 10.0,
                "comparison": "at_least_count",
            }
        }
        evidence = {"extracted_value_numeric": 15.0, "value_found": True}

        result = self.rule.evaluate(criterion, evidence)
        self.assertEqual(result.status, "Eligible")


if __name__ == "__main__":
    unittest.main()
