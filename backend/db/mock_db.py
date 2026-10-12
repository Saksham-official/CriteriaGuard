"""
In-memory Mock Database for CriteriaGuard contributor offline mode.
Mimics Supabase PostgREST client chaining so the frontend and API can be
tested end-to-end without any remote database or credentials.
"""

import copy
import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any


class MockResponse:
    def __init__(self, data: Any):
        self.data = data


class MockFilterNot:
    def __init__(self, query: "MockTableQuery"):
        self.query = query

    def is_(self, column: str, value: Any) -> "MockTableQuery":
        self.query.filters.append(("not_is", column, value))
        return self.query


class MockTableQuery:
    def __init__(self, store: "MockDatabaseClient", table_name: str):
        self.store = store
        self.table_name = table_name
        self.operation = "select"
        self.select_columns = "*"
        self.insert_data: Any = None
        self.update_data: Any = None
        self.filters: list[tuple[str, str, Any]] = []
        self.order_by: tuple[str, bool] | None = None
        self.limit_val: int | None = None
        self.not_ = MockFilterNot(self)

    def select(self, columns: str = "*") -> "MockTableQuery":
        self.operation = "select"
        self.select_columns = columns
        return self

    def insert(self, data: Any) -> "MockTableQuery":
        self.operation = "insert"
        self.insert_data = data
        return self

    def update(self, data: Any) -> "MockTableQuery":
        self.operation = "update"
        self.update_data = data
        return self

    def upsert(self, data: Any) -> "MockTableQuery":
        self.operation = "upsert"
        self.insert_data = data
        return self

    def delete(self) -> "MockTableQuery":
        self.operation = "delete"
        return self

    def eq(self, column: str, value: Any) -> "MockTableQuery":
        self.filters.append(("eq", column, value))
        return self

    def neq(self, column: str, value: Any) -> "MockTableQuery":
        self.filters.append(("neq", column, value))
        return self

    def in_(self, column: str, values: list[Any]) -> "MockTableQuery":
        self.filters.append(("in", column, values))
        return self

    def is_(self, column: str, value: Any) -> "MockTableQuery":
        self.filters.append(("is", column, value))
        return self

    def order(self, column: str, desc: bool = False) -> "MockTableQuery":
        self.order_by = (column, desc)
        return self

    def limit(self, count: int) -> "MockTableQuery":
        self.limit_val = count
        return self

    def _matches_filters(self, row: dict[str, Any]) -> bool:
        for ftype, col, val in self.filters:
            row_val = row.get(col)
            if ftype == "eq":
                if str(row_val) != str(val):
                    return False
            elif ftype == "neq":
                if str(row_val) == str(val):
                    return False
            elif ftype == "in":
                str_values = [str(v) for v in val]
                if str(row_val) not in str_values:
                    return False
            elif ftype == "is":
                if val == "null" or val is None:
                    if row_val is not None:
                        return False
                elif row_val != val:
                    return False
            elif ftype == "not_is":
                if val == "null" or val is None:
                    if row_val is None:
                        return False
                elif row_val == val:
                    return False
        return True

    def execute(self) -> MockResponse:
        rows = self.store.tables.setdefault(self.table_name, [])

        if self.operation == "insert":
            to_insert = self.insert_data
            if isinstance(to_insert, dict):
                to_insert = [to_insert]
            inserted_rows = []
            for item in to_insert:
                row = copy.deepcopy(item)
                if "id" not in row:
                    row["id"] = str(uuid.uuid4())
                if self.table_name == "audit_log" and "sequence" not in row:
                    row["sequence"] = len(rows) + 1
                rows.append(row)
                inserted_rows.append(row)
            return MockResponse(inserted_rows)

        elif self.operation == "upsert":
            to_upsert = self.insert_data
            if isinstance(to_upsert, dict):
                to_upsert = [to_upsert]
            upserted = []
            for item in to_upsert:
                row = copy.deepcopy(item)
                # Check for existing by id or criterion_id + bidder_id
                matched_idx = None
                for idx, existing in enumerate(rows):
                    if "id" in row and existing.get("id") == row["id"]:
                        matched_idx = idx
                        break
                    if "bidder_id" in row and "criterion_id" in row:
                        if (
                            existing.get("bidder_id") == row["bidder_id"]
                            and existing.get("criterion_id") == row["criterion_id"]
                        ):
                            matched_idx = idx
                            break
                if matched_idx is not None:
                    rows[matched_idx].update(row)
                    upserted.append(rows[matched_idx])
                else:
                    if "id" not in row:
                        row["id"] = str(uuid.uuid4())
                    rows.append(row)
                    upserted.append(row)
            return MockResponse(upserted)

        elif self.operation == "update":
            updated_rows = []
            for row in rows:
                if self._matches_filters(row):
                    row.update(self.update_data)
                    updated_rows.append(row)
            return MockResponse(updated_rows)

        elif self.operation == "delete":
            kept = [r for r in rows if not self._matches_filters(r)]
            deleted_count = len(rows) - len(kept)
            self.store.tables[self.table_name] = kept
            return MockResponse([{"deleted": deleted_count}])

        elif self.operation == "select":
            matched = [copy.deepcopy(r) for r in rows if self._matches_filters(r)]

            # If selecting criteria join: "*, criteria(*)"
            if "criteria(*)" in self.select_columns:
                criteria_table = self.store.tables.get("criteria", [])
                criteria_map = {str(c.get("id")): c for c in criteria_table}
                for row in matched:
                    c_id = str(row.get("criterion_id"))
                    row["criteria"] = criteria_map.get(c_id, {})

            if self.order_by:
                col, is_desc = self.order_by
                try:
                    matched.sort(key=lambda x: x.get(col, 0) or 0, reverse=is_desc)
                except Exception:
                    pass

            if self.limit_val is not None:
                matched = matched[: self.limit_val]

            return MockResponse(matched)

        return MockResponse([])


class MockDatabaseClient:
    """Mock in-memory Supabase client."""

    def __init__(self):
        self.tables: dict[str, list[dict[str, Any]]] = {}
        self.seed_sample_data()

    def table(self, table_name: str) -> MockTableQuery:
        return MockTableQuery(self, table_name)

    def seed_sample_data(self):
        """Populate database with sample tender, criteria, bidders, and audit entries."""
        tender_id = "t-2026-giep-001"
        now_ts = datetime.now(UTC).isoformat(timespec="seconds")

        # 1. Tender
        self.tables["tenders"] = [
            {
                "id": tender_id,
                "title": "Global Infrastructure Expansion Project 2026",
                "authority": "Ministry of Urban Development",
                "tender_code": "T-2026-GIEP-001",
                "created_at": now_ts,
                "status": "criteria_approved",
                "document_url": "/mock/tender_document.pdf",
            }
        ]

        # 2. Criteria
        self.tables["criteria"] = [
            {
                "id": "c001",
                "tender_id": tender_id,
                "criterion_code": "C001",
                "text": "The bidder shall have an average annual turnover of at least $50,000,000 over the last three financial years.",
                "category": "financial",
                "mandatory": True,
                "mandatory_confidence": "high",
                "threshold_value": 50000000.0,
                "threshold_comparison": "greater_than_equal",
                "evidence_documents": ["Audited Balance Sheets"],
                "source_clause": "Clause 4.1(a)",
                "source_page": 4,
                "approved_at": now_ts,
                "approved_by": "OFFICER_CHAIR",
            },
            {
                "id": "c002",
                "tender_id": tender_id,
                "criterion_code": "C002",
                "text": "The bidder's net worth should be positive in each of the last three financial years.",
                "category": "financial",
                "mandatory": True,
                "mandatory_confidence": "high",
                "threshold_value": None,
                "threshold_comparison": None,
                "evidence_documents": ["CA Net Worth Certificate"],
                "source_clause": "Clause 4.1(b)",
                "source_page": 4,
                "approved_at": now_ts,
                "approved_by": "OFFICER_CHAIR",
            },
            {
                "id": "c003",
                "tender_id": tender_id,
                "criterion_code": "C003",
                "text": "The bidder must have successfully completed at least three infrastructure projects exceeding $20M each.",
                "category": "technical",
                "mandatory": True,
                "mandatory_confidence": "high",
                "threshold_value": 3.0,
                "threshold_comparison": "at_least_count",
                "evidence_documents": ["Client Completion Certificates"],
                "source_clause": "Clause 4.2(a)",
                "source_page": 5,
                "approved_at": now_ts,
                "approved_by": "OFFICER_CHAIR",
            },
            {
                "id": "c004",
                "tender_id": tender_id,
                "criterion_code": "C004",
                "text": "The Project Manager must have at least 15 years of experience in civil engineering.",
                "category": "technical",
                "mandatory": True,
                "mandatory_confidence": "high",
                "threshold_value": 15.0,
                "threshold_comparison": "greater_than_equal",
                "evidence_documents": ["Personnel CV"],
                "source_clause": "Clause 4.2(b)",
                "source_page": 5,
                "approved_at": now_ts,
                "approved_by": "OFFICER_CHAIR",
            },
            {
                "id": "c005",
                "tender_id": tender_id,
                "criterion_code": "C005",
                "text": "The bidder shall possess a valid ISO 9001:2015 certification for Quality Management Systems.",
                "category": "compliance",
                "mandatory": True,
                "mandatory_confidence": "high",
                "threshold_value": None,
                "threshold_comparison": None,
                "evidence_documents": ["ISO Certificate"],
                "source_clause": "Clause 4.3(a)",
                "source_page": 6,
                "approved_at": now_ts,
                "approved_by": "OFFICER_CHAIR",
            },
            {
                "id": "c006",
                "tender_id": tender_id,
                "criterion_code": "C006",
                "text": "Safety record: Zero fatalities in the last 24 months preferred.",
                "category": "compliance",
                "mandatory": False,
                "mandatory_confidence": "ambiguous",
                "threshold_value": None,
                "threshold_comparison": None,
                "evidence_documents": ["Safety Audit Report"],
                "source_clause": "Clause 4.3(b)",
                "source_page": 6,
                "approved_at": now_ts,
                "approved_by": "OFFICER_CHAIR",
            },
        ]

        # 3. Bidders
        b1_id = "bidder-01-builders-corp"
        b2_id = "bidder-02-skybound"
        b3_id = "bidder-03-marginal"

        self.tables["bidders"] = [
            {
                "id": b1_id,
                "tender_id": tender_id,
                "name": "Builders Corp International",
                "status": "completed",
                "overall_verdict": "Eligible",
                "created_at": now_ts,
            },
            {
                "id": b2_id,
                "tender_id": tender_id,
                "name": "SkyBound Drones Pvt. Ltd.",
                "status": "completed",
                "overall_verdict": "Not Eligible",
                "created_at": now_ts,
            },
            {
                "id": b3_id,
                "tender_id": tender_id,
                "name": "Marginal Aviations",
                "status": "completed",
                "overall_verdict": "Needs Review",
                "created_at": now_ts,
            },
        ]

        # 4. Extractions
        self.tables["extractions"] = [
            {
                "id": "ext-b1-c001",
                "bidder_id": b1_id,
                "criterion_id": "c001",
                "value_found": True,
                "extracted_value": "$52,166,667",
                "extracted_value_numeric": 52166667.0,
                "source_document": "Financial_Statements_2025.pdf",
                "source_page": 2,
                "source_excerpt": "Three-year average annual turnover verified at $52,166,667.",
                "ocr_quality": "high",
                "extraction_confidence": 0.98,
            },
            {
                "id": "ext-b2-c001",
                "bidder_id": b2_id,
                "criterion_id": "c001",
                "value_found": True,
                "extracted_value": "$35,000,000",
                "extracted_value_numeric": 35000000.0,
                "source_document": "Financial_Statement_FY25.pdf",
                "source_page": 1,
                "source_excerpt": "Annual turnover: $35M average over the 3 past years.",
                "ocr_quality": "high",
                "extraction_confidence": 0.96,
            },
            {
                "id": "ext-b3-c001",
                "bidder_id": b3_id,
                "criterion_id": "c001",
                "value_found": True,
                "extracted_value": "$49,500,000",
                "extracted_value_numeric": 49500000.0,
                "source_document": "Audited_Turnover.pdf",
                "source_page": 2,
                "source_excerpt": "Audited turnover average across 3 years: $49,500,000.",
                "ocr_quality": "high",
                "extraction_confidence": 0.95,
            },
        ]

        # 5. Verdicts
        self.tables["verdicts"] = [
            {
                "id": "v-b1-c001",
                "bidder_id": b1_id,
                "criterion_id": "c001",
                "status": "Eligible",
                "reason": "Value 52166667.0 meets requirement of greater_than_equal 50000000.0.",
                "review_sub_reason": None,
            },
            {
                "id": "v-b2-c001",
                "bidder_id": b2_id,
                "criterion_id": "c001",
                "status": "Not Eligible",
                "reason": "Value 35000000.0 fails requirement of greater_than_equal 50000000.0.",
                "review_sub_reason": None,
            },
            {
                "id": "v-b3-c001",
                "bidder_id": b3_id,
                "criterion_id": "c001",
                "status": "Needs Review",
                "reason": "Value 49500000.0 is within 10% of threshold 50000000.0. Manual validation required for borderline case.",
                "review_sub_reason": "BORDERLINE_VALUE",
            },
        ]

        # 6. Audit Trail with valid chained SHA-256 hashes
        prev_hash = "GENESIS_HASH"
        audit_entries = [
            ("TENDER_UPLOAD", "SYSTEM", "tender", tender_id, "success"),
            ("CRITERIA_EXTRACTION", "CriteriaLens", "tender", tender_id, "6 criteria extracted"),
            ("CRITERION_APPROVE", "OFFICER_CHAIR", "criterion", "c001", "approved"),
            ("BIDDER_EVALUATION", "VerdictCore", "bidder", b1_id, "Eligible"),
            ("BIDDER_EVALUATION", "VerdictCore", "bidder", b2_id, "Not Eligible"),
            ("BIDDER_EVALUATION", "VerdictCore", "bidder", b3_id, "Needs Review (Borderline)"),
        ]

        self.tables["audit_log"] = []
        for seq, (action, actor, ttype, tid, res) in enumerate(audit_entries, start=1):
            stable_ts = f"2026-03-15T10:{seq:02d}:00"
            payload = {
                "previous_hash": prev_hash,
                "action_type": action,
                "actor": actor,
                "target_id": tid,
                "result": res,
                "timestamp": stable_ts,
            }
            content = json.dumps(payload, sort_keys=True)
            entry_hash = hashlib.sha256(content.encode()).hexdigest()

            self.tables["audit_log"].append(
                {
                    "id": str(uuid.uuid4()),
                    "sequence": seq,
                    "action_type": action,
                    "actor": actor,
                    "target_type": ttype,
                    "target_id": tid,
                    "result": res,
                    "metadata": {"source": "mock_demo_seed"},
                    "timestamp": stable_ts,
                    "previous_hash": prev_hash,
                    "entry_hash": entry_hash,
                }
            )
            prev_hash = entry_hash


_mock_db_instance: MockDatabaseClient | None = None


def get_mock_db() -> MockDatabaseClient:
    global _mock_db_instance
    if _mock_db_instance is None:
        _mock_db_instance = MockDatabaseClient()
    return _mock_db_instance
