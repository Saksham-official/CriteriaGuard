"""
Unit and integration tests for CriteriaGuard Mock / Contributor Mode.
Verifies that all core API endpoints, fixtures, and audit trails function
flawlessly without requiring Groq or Supabase API keys.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app


class TestMockPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["MOCK_LLM"] = "true"
        os.environ["USE_SAMPLE_DATA"] = "true"
        cls.client = TestClient(app)

    def test_health_check_returns_ok_in_mock_mode(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["mode"], "mock")

    def test_get_seeded_tender_criteria(self):
        response = self.client.get("/api/tenders/t-2026-giep-001/criteria")
        self.assertEqual(response.status_code, 200)
        criteria = response.json()
        self.assertIsInstance(criteria, list)
        self.assertGreaterEqual(len(criteria), 6)

        # Check criterion C001
        c001 = next((c for c in criteria if c.get("criterion_code") == "C001"), None)
        self.assertIsNotNone(c001)
        self.assertEqual(c001["mandatory"], True)
        self.assertEqual(c001["threshold_value"], 50000000.0)

    def test_get_seeded_tender_verdicts(self):
        response = self.client.get("/api/verdicts/tender/t-2026-giep-001")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("bidders", data)
        self.assertIn("verdicts", data)
        self.assertIn("extractions", data)
        self.assertGreaterEqual(len(data["bidders"]), 3)

    def test_audit_trail_endpoint_with_valid_hash_chain(self):
        response = self.client.get("/api/audit/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("logs", data)
        self.assertIn("is_chain_valid", data)
        self.assertTrue(data["is_chain_valid"])
        self.assertGreaterEqual(len(data["logs"]), 5)

    def test_ambiguity_resolver_deterministic_in_mock_mode(self):
        response = self.client.post(
            "/api/tenders/resolve-ambiguity",
            json={
                "text": "The contractor shall provide safety equipment.",
                "source_clause": "Clause 12.1 Mandatory HSE compliance.",
            },
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["likely_mandatory"])
        self.assertIn("mandatory", result["recommendation"])


if __name__ == "__main__":
    unittest.main()
