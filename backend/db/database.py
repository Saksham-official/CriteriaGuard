import os
import json
import uuid
import socket
from urllib.parse import urlparse
from typing import Optional, Any, List, Dict
from supabase import create_client, Client
from fastapi import HTTPException
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

LOCAL_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_db.json")

def is_supabase_online(url: str) -> bool:
    """Performs a lightweight socket DNS/connect check to verify internet/database status."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return False
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        # 1-second short timeout to prevent startup hangs
        socket.setdefaulttimeout(1.0)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

# Local mock DB implementation
class MockResponse:
    def __init__(self, data):
        self.data = data

class MockQueryBuilder:
    def __init__(self, table_name: str, db_client: 'MockSupabaseClient'):
        self.table_name = table_name
        self.db_client = db_client
        self.filters: List[tuple] = []
        self.update_payload = None
        self.insert_payload = None
        self.delete_request = False

    def select(self, columns: str = "*"):
        return self

    def insert(self, payload: Any):
        self.insert_payload = payload
        return self

    def update(self, payload: Any):
        self.update_payload = payload
        return self

    def delete(self):
        self.delete_request = True
        return self

    def eq(self, column: str, value: Any):
        self.filters.append(("eq", column, value))
        return self

    def in_(self, column: str, values: List[Any]):
        self.filters.append(("in", column, values))
        return self

    def limit(self, value: int):
        self.filters.append(("limit", None, value))
        return self

    @property
    def not_(self):
        class NotHelper:
            def __init__(self, builder: 'MockQueryBuilder'):
                self.builder = builder
            def is_(self, column: str, val: str):
                self.builder.filters.append(("not_is", column, val))
                return self.builder
        return NotHelper(self)

    def execute(self) -> MockResponse:
        return self.db_client._run_query(self)

class MockSupabaseClient:
    def __init__(self):
        self.filepath = LOCAL_DB_FILE
        self._init_local_store()

    def _init_local_store(self):
        if not os.path.exists(self.filepath):
            # Seed default schema structure
            default_data = {
                "tenders": [],
                "criteria": [],
                "bidders": [],
                "extractions": [],
                "verdicts": [],
                "audit_log": []
            }
            with open(self.filepath, "w") as f:
                json.dump(default_data, f, indent=2)
            logger.info(f"MockSupabaseClient: Seeding initial JSON database in {self.filepath}")

    def _load_data(self) -> Dict[str, List[Dict[str, Any]]]:
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except Exception:
            return {"tenders": [], "criteria": [], "bidders": [], "extractions": [], "verdicts": [], "audit_log": []}

    def _save_data(self, data: dict):
        try:
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"MockSupabaseClient: Failed to save JSON database: {e}")

    def table(self, name: str) -> MockQueryBuilder:
        return MockQueryBuilder(name, self)

    def _run_query(self, builder: MockQueryBuilder) -> MockResponse:
        db_data = self._load_data()
        table_name = builder.table_name
        
        if table_name not in db_data:
            db_data[table_name] = []
            
        rows = db_data[table_name]

        # 1. INSERT OPERATION
        if builder.insert_payload is not None:
            inserts = builder.insert_payload
            if isinstance(inserts, dict):
                inserts = [inserts]
                
            inserted_rows = []
            for item in inserts:
                new_row = dict(item)
                if "id" not in new_row:
                    new_row["id"] = str(uuid.uuid4())
                rows.append(new_row)
                inserted_rows.append(new_row)
                
            self._save_data(db_data)
            return MockResponse(inserted_rows)

        # 2. FILTERING FOR SELECT/UPDATE/DELETE
        matched_indices = []
        for idx, row in enumerate(rows):
            match = True
            for op, col, val in builder.filters:
                if op == "eq":
                    if str(row.get(col)) != str(val):
                        match = False
                elif op == "in":
                    # Convert values to strings to handle stringified uuid lists easily
                    str_vals = [str(v) for v in val]
                    if str(row.get(col)) not in str_vals:
                        match = False
                elif op == "not_is":
                    # For not_.is_("approved_at", "null")
                    actual_val = row.get(col)
                    if val == "null":
                        if actual_val is None or actual_val == "":
                            match = False
            if match:
                matched_indices.append(idx)

        # 3. UPDATE OPERATION
        if builder.update_payload is not None:
            updated_rows = []
            for idx in matched_indices:
                rows[idx].update(builder.update_payload)
                updated_rows.append(rows[idx])
            self._save_data(db_data)
            return MockResponse(updated_rows)

        # 4. DELETE OPERATION
        if builder.delete_request:
            # Reconstruct table leaving out matching rows
            remaining = [row for idx, row in enumerate(rows) if idx not in matched_indices]
            db_data[table_name] = remaining
            self._save_data(db_data)
            return MockResponse([])

        # 5. SELECT OPERATION
        results = [rows[idx] for idx in matched_indices]
        
        # Handle limit
        for op, _, val in builder.filters:
            if op == "limit":
                results = results[:int(val)]
                
        return MockResponse(results)


# Decide client dynamically based on live connectivity
supabase_online = False
supabase: Any = None

if SUPABASE_URL and SUPABASE_KEY:
    if is_supabase_online(SUPABASE_URL):
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            supabase_online = True
            logger.info("CriteriaGuard DB: Database is ONLINE. Supabase Client successfully initialized.")
        except Exception as e:
            logger.warning(f"CriteriaGuard DB: Failed to connect to Supabase: {e}. Falling back to OFFLINE mode.")
    else:
        logger.warning("CriteriaGuard DB: Supabase endpoint is UNREACHABLE. Switching to OFFLINE RESILIENCY mode.")

if not supabase_online:
    supabase = MockSupabaseClient()
    logger.info("CriteriaGuard DB: OFFLINE RESILIENCY mode active. Local JSON file-backed database loaded.")


def get_db() -> Client:
    """Return the Supabase/Mock client, falling back dynamically to MockSupabaseClient."""
    return supabase
