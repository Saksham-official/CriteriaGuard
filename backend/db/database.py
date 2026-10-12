import os
from typing import Any

from dotenv import load_dotenv

from db.mock_db import get_mock_db

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

IS_MOCK = (
    os.getenv("MOCK_LLM", "").lower() in ("true", "1")
    or os.getenv("USE_SAMPLE_DATA", "").lower() in ("true", "1")
    or not (SUPABASE_URL and SUPABASE_KEY)
)

supabase: Any = None

if not IS_MOCK and SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        # Fallback to mock DB if Supabase client creation fails
        supabase = get_mock_db()
else:
    # Use mock in-memory DB for contributor offline mode
    supabase = get_mock_db()


def get_db() -> Any:
    """
    Return the active database client.
    In contributor/mock mode (or when Supabase credentials are not provided),
    returns the in-memory MockDatabaseClient seeded with realistic procurement data.
    """
    global supabase
    if supabase is None:
        supabase = get_mock_db()
    return supabase
