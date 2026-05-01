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
        
        for i in range(len(logs)):
            log = logs[i]
            
            content_to_hash = f"{log['previous_hash']}{log['action_type']}{log['actor']}{log['target_id']}{log['result']}{log['timestamp']}"
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
