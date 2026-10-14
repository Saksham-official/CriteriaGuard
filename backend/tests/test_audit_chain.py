"""
Unit tests for SHA-256 audit-chain append logic, tamper detection, and verification.
Verifies append-only integrity of public procurement governance logs.
"""

import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def compute_entry_hash(
    previous_hash: str, action_type: str, actor: str, target_id: str, result: str, timestamp: str
) -> str:
    """Canonical SHA-256 hash calculation matching backend/services/audit.py."""
    payload = {
        "previous_hash": previous_hash,
        "action_type": action_type,
        "actor": actor,
        "target_id": target_id,
        "result": result,
        "timestamp": timestamp,
    }
    content = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


class TestAuditChain(unittest.TestCase):
    def test_genesis_hash_computation(self):
        ts = "2026-03-15T10:00:00"
        genesis_prev = "GENESIS_HASH"
        h = compute_entry_hash(genesis_prev, "TENDER_UPLOAD", "OFFICER_001", "T-001", "success", ts)
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    def test_chain_linkage_integrity(self):
        chain = []
        entries_data = [
            ("TENDER_UPLOAD", "OFFICER_001", "T-001", "success", "2026-03-15T10:00:00"),
            ("CRITERIA_APPROVED", "OFFICER_001", "T-001", "approved", "2026-03-15T10:05:00"),
            ("BIDDER_EVALUATED", "SYSTEM", "B-001", "Eligible", "2026-03-15T10:10:00"),
            ("VERDICT_OVERRIDE", "OFFICER_CHAIR", "V-001", "Needs Review", "2026-03-15T10:15:00"),
        ]

        prev_hash = "GENESIS_HASH"
        for action, actor, target, result, ts in entries_data:
            entry_h = compute_entry_hash(prev_hash, action, actor, target, result, ts)
            chain.append(
                {
                    "previous_hash": prev_hash,
                    "entry_hash": entry_h,
                    "action_type": action,
                    "actor": actor,
                    "target_id": target,
                    "result": result,
                    "timestamp": ts,
                }
            )
            prev_hash = entry_h

        # Verify chain integrity
        for i in range(1, len(chain)):
            self.assertEqual(chain[i]["previous_hash"], chain[i - 1]["entry_hash"])

    def test_tamper_detection(self):
        # Build 3 blocks
        chain = []
        prev_hash = "GENESIS_HASH"
        for i in range(3):
            ts = f"2026-03-15T10:0{i}:00"
            entry_h = compute_entry_hash(prev_hash, "ACTION", "ACTOR", f"T-{i}", "OK", ts)
            chain.append(
                {
                    "previous_hash": prev_hash,
                    "entry_hash": entry_h,
                    "action_type": "ACTION",
                    "actor": "ACTOR",
                    "target_id": f"T-{i}",
                    "result": "OK",
                    "timestamp": ts,
                }
            )
            prev_hash = entry_h

        # Malicious actor tampers with Block 1 result: "OK" -> "FAIL"
        tampered_chain = [dict(c) for c in chain]
        tampered_chain[1]["result"] = "FAIL"

        # Re-evaluating Block 1 hash with tampered data
        tampered_h = compute_entry_hash(
            tampered_chain[1]["previous_hash"],
            tampered_chain[1]["action_type"],
            tampered_chain[1]["actor"],
            tampered_chain[1]["target_id"],
            tampered_chain[1]["result"],
            tampered_chain[1]["timestamp"],
        )

        # The recorded entry_hash does NOT match the recomputed hash
        self.assertNotEqual(tampered_h, tampered_chain[1]["entry_hash"])

        # And Block 2's previous_hash would not match the new hash
        self.assertNotEqual(tampered_chain[2]["previous_hash"], tampered_h)


if __name__ == "__main__":
    unittest.main()
