from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import shutil
import os
import uuid

from services.pdf_extractor import extract_text_from_pdf, format_pages_for_prompt
from engines.criteria_lens import extract_criteria_from_text
from engines.ambiguity_resolver import resolve_ambiguity
from services.audit import log_audit_action
from db.database import supabase
from models.criterion import CriterionSchema

router = APIRouter(prefix="/api/tenders", tags=["tenders"])

class AmbiguityRequest(BaseModel):
    text: str
    source_clause: str

@router.post("/resolve-ambiguity")
async def get_ambiguity_suggestion(request: AmbiguityRequest):
    try:
        suggestion = resolve_ambiguity(request.text, request.source_clause)
        return suggestion
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

UPLOAD_DIR = "uploads/tenders"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_tender(file: UploadFile = File(...), officer_id: str = Form("SYSTEM_OR_OFFICER")):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 1. Insert into Supabase 'tenders' table
    try:
        tender_res = supabase.table("tenders").insert({
            "title": file.filename,
            "file_path": file_path,
            "status": "processing",
            "created_by": officer_id
        }).execute()
        tender_id = tender_res.data[0]["id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Log to Audit
    log_audit_action(
        action_type="TENDER_UPLOAD",
        actor=officer_id,
        target_type="tender",
        target_id=tender_id,
        result="success",
        metadata={"filename": file.filename}
    )

    # 2. Extract text from PDF
    pages = extract_text_from_pdf(file_path)
    if not pages:
        raise HTTPException(status_code=400, detail="Could not extract text from the provided PDF")
        
    tender_text = format_pages_for_prompt(pages)
    
    # 3. Extract criteria using Claude
    try:
        criteria_list = extract_criteria_from_text(tender_text)
    except Exception as e:
        # Update tender status to failed
        supabase.table("tenders").update({"status": "failed"}).eq("id", tender_id).execute()
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {str(e)}")
        
    # 4. Save extracted criteria to DB
    criteria_inserts = []
    for i, criterion in enumerate(criteria_list):
        # Convert Pydantic model to dict, exclude None for threshold if needed
        crit_dict = criterion.model_dump()
        
        db_record = {
            "tender_id": tender_id,
            "criterion_code": crit_dict["id"],
            "text": crit_dict["text"],
            "category": crit_dict["category"],
            "mandatory": crit_dict["mandatory"],
            "mandatory_confidence": crit_dict["mandatory_confidence"],
            "evidence_documents": crit_dict["evidence_documents"],
            "source_clause": crit_dict["source_clause"]
        }
        
        if crit_dict.get("threshold"):
            t = crit_dict["threshold"]
            db_record.update({
                "threshold_value": t.get("value"),
                "threshold_unit": t.get("unit"),
                "threshold_period": t.get("period"),
                "threshold_comparison": t.get("comparison")
            })
            
        criteria_inserts.append(db_record)
        
    if criteria_inserts:
        supabase.table("criteria").insert(criteria_inserts).execute()
        
    # Update tender status
    supabase.table("tenders").update({"status": "criteria_review"}).eq("id", tender_id).execute()
    
    return {"message": "Tender processed successfully", "tender_id": tender_id}

@router.get("/{tender_id}/criteria")
async def get_criteria(tender_id: str):
    res = supabase.table("criteria").select("*").eq("tender_id", tender_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="No criteria found for this tender")
    return res.data

class CriterionUpdate(BaseModel):
    text: str
    mandatory: bool
    mandatory_confidence: str
    # other fields as needed

@router.patch("/{tender_id}/criteria/{criterion_id}")
async def update_criterion(tender_id: str, criterion_id: str, update_data: CriterionUpdate):
    res = supabase.table("criteria").update(update_data.model_dump(exclude_unset=True)).eq("id", criterion_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Criterion not found")
    return res.data
