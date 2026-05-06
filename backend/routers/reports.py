from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import List

from db.database import supabase
from services.report_gen import generate_tender_report_pdf
from services.audit import log_audit_action

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/export/{tender_id}")
async def export_tender_report(tender_id: str, officer_id: str = "SYSTEM_OR_OFFICER"):
    try:
        # Fetch tender
        t_res = supabase.table("tenders").select("*").eq("id", tender_id).execute()
        if not t_res.data:
            raise HTTPException(status_code=404, detail="Tender not found")
        tender = t_res.data[0]
        
        # Fetch all bidders, extractions, and verdicts
        bidders_res = supabase.table("bidders").select("*").eq("tender_id", tender_id).execute()
        bidders = bidders_res.data
        
        bidders_data = []
        for bidder in bidders:
            ext_res = supabase.table("extractions").select("*, criteria(*)").eq("bidder_id", bidder["id"]).execute()
            verdict_res = supabase.table("verdicts").select("*").eq("bidder_id", bidder["id"]).execute()
            
            # map extractions with their verdicts
            extractions = ext_res.data
            verdicts = verdict_res.data
            
            for ext in extractions:
                ext["verdict"] = next((v for v in verdicts if v["criterion_id"] == ext["criterion_id"]), {"status": "Pending", "reason": "No verdict yet"})
            
            bidders_data.append({
                "id": bidder["id"],
                "name": bidder["name"],
                "status": bidder["status"],
                "extractions": extractions
            })
            
        # Generate PDF
        pdf_bytes = generate_tender_report_pdf(
            tender_id=tender["id"],
            tender_title=tender["title"],
            bidders_data=bidders_data
        )
        
        # Log to Audit
        log_audit_action(
            action_type="REPORT_EXPORT",
            actor=officer_id,
            target_type="tender",
            target_id=tender_id,
            result="success",
            metadata={"bidders_count": len(bidders)}
        )
        
        return Response(content=pdf_bytes, media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="criteriaguard_report_{tender_id[:8]}.pdf"'
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
