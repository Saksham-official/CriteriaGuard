from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from datetime import datetime, timezone
from db.database import supabase
from services.audit import log_audit_action

router = APIRouter(prefix="/api/verdicts", tags=["verdicts"])

class OverrideRequest(BaseModel):
    officer_id: str
    new_status: str
    reason: str

@router.get("/tender/{tender_id}")
async def get_tender_verdicts(tender_id: str):
    # Fetch bidders for tender
    bidders_res = supabase.table("bidders").select("*").eq("tender_id", tender_id).execute()
    bidders = bidders_res.data
    
    bidder_ids = [b["id"] for b in bidders]
    if not bidder_ids:
        return {"bidders": [], "extractions": [], "verdicts": []}
        
    # Fetch extractions and verdicts
    extractions_res = supabase.table("extractions").select("*, criteria(*)").in_("bidder_id", bidder_ids).execute()
    verdicts_res = supabase.table("verdicts").select("*").in_("bidder_id", bidder_ids).execute()
    
    return {
        "bidders": bidders,
        "extractions": extractions_res.data,
        "verdicts": verdicts_res.data
    }

@router.post("/{verdict_id}/override")
async def override_verdict(verdict_id: str, req: OverrideRequest):
    try:
        # Fetch existing verdict
        v_res = supabase.table("verdicts").select("*").eq("id", verdict_id).execute()
        if not v_res.data:
            raise HTTPException(status_code=404, detail="Verdict not found")
        
        verdict = v_res.data[0]
        
        # Update
        supabase.table("verdicts").update({
            "status": req.new_status,
            "overridden_by": req.officer_id,
            "override_action": "manual_override",
            "override_reason": req.reason,
            "overridden_at": datetime.now(timezone.utc).isoformat(timespec='seconds')
        }).eq("id", verdict_id).execute()
        
        # Log to Audit
        log_audit_action(
            action_type="VERDICT_OVERRIDE",
            actor=req.officer_id,
            target_type="verdict",
            target_id=verdict_id,
            result=req.new_status,
            metadata={"old_status": verdict["status"], "reason": req.reason}
        )
        
        return {"message": "Verdict overridden successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
