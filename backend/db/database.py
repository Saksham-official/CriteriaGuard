import os

from dotenv import load_dotenv
from fastapi import HTTPException
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_db() -> Client:
    """Return the Supabase client, raising HTTP 503 if not configured."""
    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Check SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.",
        )
    return supabase
