from fastapi import APIRouter, HTTPException
import hashlib
from db.database import supabase

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/")
async def get_audit_trail():
    try:
        # Fetch audit log in chronological order
        log_res = supabase.table("audit_log").select("*").order("sequence", desc=False).execute()
        logs = log_res.data
        
        # Verify the chain integrity dynamically
        valid = True
        verification_results = []
        for log in logs:
            import json
            
            # Normalize timestamp for stable verification (YYYY-MM-DDTHH:MM:SS)
            raw_ts = str(log['timestamp'])
            # Replace space with T, remove subseconds and timezone offset
            stable_ts = raw_ts.replace(' ', 'T').split('.')[0].split('+')[0]
            if stable_ts.endswith('Z'): stable_ts = stable_ts[:-1]

            payload = {
                "previous_hash": str(log['previous_hash']),
                "action_type": str(log['action_type']),
                "actor": str(log['actor']),
                "target_id": str(log['target_id']),
                "result": str(log['result']),
                "timestamp": stable_ts
            }
            content_to_hash = json.dumps(payload, sort_keys=True)
            computed_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()
            
            is_intact = computed_hash == log['entry_hash']
            if not is_intact:
                valid = False
                
            verification_results.append({
                "id": log["id"],
                "is_intact": is_intact
            })
            
        return {
            "is_chain_valid": valid,
            "logs": logs,
            "verification": verification_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
