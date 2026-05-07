import hashlib
import json
from typing import Any
from datetime import datetime, timezone
from db.database import supabase
from utils.logger import logger

def log_audit_action(action_type: str, actor: str, target_type: str, target_id: str, result: str, metadata: dict):
    if supabase is None:
        logger.warning(f"Skipping audit log (Supabase not initialized): {action_type} for {target_id}")
        return

    # Fetch previous hash
    last_log_res = supabase.table("audit_log").select("entry_hash").order("sequence", desc=True).limit(1).execute()

    previous_hash = "GENESIS_HASH"
    if last_log_res.data and len(last_log_res.data) > 0:
        last_row: dict[str, Any] = last_log_res.data[0]  # type: ignore[assignment]
        previous_hash = last_row["entry_hash"]

    timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')

    # Canonical JSON for deterministic hashing
    payload = {
        "previous_hash": previous_hash,
        "action_type": action_type,
        "actor": actor,
        "target_id": target_id,
        "result": result,
        "timestamp": timestamp
    }
    content_to_hash = json.dumps(payload, sort_keys=True)
    new_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()

    supabase.table("audit_log").insert({
        "action_type": action_type,
        "actor": actor,
        "target_type": target_type,
        "target_id": target_id,
        "result": result,
        "metadata": metadata,
        "timestamp": timestamp,
        "entry_hash": new_hash,
        "previous_hash": previous_hash
    }).execute()
