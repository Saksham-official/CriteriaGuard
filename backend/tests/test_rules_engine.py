"""
Unit tests for CriteriaGuard RulesEngine, custom rule registration, and fixture-based evaluation.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rules import (
    EligibilityRule,
    MandatoryDocumentRule,
    RuleResult,
    RulesEngine,
    default_engine,
)


class CustomConsortiumRule(EligibilityRule):
    """Example custom rule contributed by an open-source contributor."""

    rule_id = "consortium_limit"
    name = "Consortium Member Limit Rule"
    description = "Checks that joint venture consortium has at most 3 members."

    def applies_to(self, criterion, evidence):
        return "consortium" in str(criterion.get("text", "")).lower()

    def evaluate(self, criterion, evidence):
        members = evidence.get("extracted_value_numeric", 0)
        if members > 3:
            return RuleResult(
                status="Not Eligible",
                reason=f"Consortium has {members} members, exceeding maximum allowed limit of 3.",
            )
        return RuleResult(
            status="Eligible", reason=f"Consortium has {members} members (within limit <= 3)."
        )


class TestRulesEngine(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        with open(os.path.join(self.fixtures_dir, "sample_tender.json"), encoding="utf-8") as f:
            self.sample_tender = json.load(f)
        with open(
            os.path.join(self.fixtures_dir, "sample_bidder_submission.json"), encoding="utf-8"
        ) as f:
            self.sample_bidders = json.load(f)

    def test_fixture_loading(self):
        self.assertEqual(self.sample_tender["tender_id"], "T-2026-GIEP-001")
        self.assertEqual(len(self.sample_tender["criteria"]), 6)
        self.assertEqual(len(self.sample_bidders["submissions"]), 4)

    def test_custom_rule_registration(self):
        engine = RulesEngine()
        custom_rule = CustomConsortiumRule()
        engine.register_rule(custom_rule)

        criterion = {"text": "Consortium / Joint Venture must have no more than 3 members."}
        evidence_fail = {"value_found": True, "extracted_value_numeric": 4}
        evidence_pass = {"value_found": True, "extracted_value_numeric": 2}

        res_fail = engine.evaluate(criterion, evidence_fail)
        self.assertEqual(res_fail.status, "Not Eligible")
        self.assertIn("exceeding maximum allowed limit", res_fail.reason)

        res_pass = engine.evaluate(criterion, evidence_pass)
        self.assertEqual(res_pass.status, "Eligible")

    def test_mandatory_document_rule(self):
        rule = MandatoryDocumentRule()

        # Missing mandatory document
        c_mand = {"mandatory": True, "mandatory_confidence": "high", "category": "compliance"}
        e_missing = {"value_found": False}
        res = rule.evaluate(c_mand, e_missing)
        self.assertEqual(res.status, "Not Eligible")

        # Missing optional document
        c_opt = {"mandatory": False, "category": "compliance"}
        res_opt = rule.evaluate(c_opt, e_missing)
        self.assertEqual(res_opt.status, "Eligible")

    def test_fixture_end_to_end_evaluation(self):
        # Test Builders Corp C001 (Turnover $52M vs $50M)
        c001 = next(c for c in self.sample_tender["criteria"] if c["id"] == "C001")
        b1_ext = self.sample_bidders["submissions"][0]["extractions"]["C001"]

        # Note: 52.166M is within 10% of 50M -> Borderline Needs Review
        res_b1 = default_engine.evaluate(c001, b1_ext)
        self.assertEqual(res_b1.status, "Needs Review")
        self.assertEqual(res_b1.review_sub_reason, "BORDERLINE_VALUE")

        # Test SkyBound C001 (Turnover $35M vs $50M -> Not Eligible)
        b2_ext = self.sample_bidders["submissions"][1]["extractions"]["C001"]
        res_b2 = default_engine.evaluate(c001, b2_ext)
        self.assertEqual(res_b2.status, "Not Eligible")


if __name__ == "__main__":
    unittest.main()
