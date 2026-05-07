from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import shutil
import os
import uuid

from services.pdf_extractor import extract_text_from_pdf, format_pages_for_prompt, DocPage
from services.docx_extractor import extract_text_from_docx
from services.ocr import extract_text_from_image
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
    allowed_extensions = {'.pdf', '.docx', '.jpg', '.jpeg', '.png', '.tiff'}
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Supported: {', '.join(allowed_extensions)}"
        )
        
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

    # 2. Extract text based on file type
    pages = []
    if ext == '.pdf':
        pages = extract_text_from_pdf(file_path)
    elif ext == '.docx':
        pages = extract_text_from_docx(file_path)
    elif ext in {'.jpg', '.jpeg', '.png', '.tiff'}:
        ocr_res = extract_text_from_image(file_path)
        if ocr_res.text:
            pages = [DocPage(page_number=1, text=ocr_res.text)]
            
    if not pages:
        raise HTTPException(status_code=400, detail="Could not extract text from the provided document")
        
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
            "source_clause": crit_dict["source_clause"],
            "source_page": crit_dict.get("source_page", 1)
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
    text: Optional[str] = None
    mandatory: Optional[bool] = None
    mandatory_confidence: Optional[str] = None
    category: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    reason: Optional[str] = None

@router.patch("/{tender_id}/criteria/{criterion_id}")
async def update_criterion(tender_id: str, criterion_id: str, update_data: CriterionUpdate):
    data = update_data.model_dump(exclude_unset=True)
    res = supabase.table("criteria").update(data).eq("id", criterion_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Criterion not found")
        
    # Log to Audit if this is an approval or a major edit
    if update_data.approved_by:
        log_audit_action(
            action_type="CRITERION_APPROVE",
            actor=update_data.approved_by,
            target_type="criterion",
            target_id=criterion_id,
            result="approved",
            metadata={"tender_id": tender_id}
        )
    return res.data

@router.delete("/{tender_id}/criteria/{criterion_id}")
async def delete_criterion(tender_id: str, criterion_id: str):
    res = supabase.table("criteria").delete().eq("id", criterion_id).execute()
    return {"message": "Criterion deleted"}

class CriterionCreate(BaseModel):
    criterion_code: str
    text: str
    category: str
    mandatory: bool
    source_clause: str

@router.post("/{tender_id}/criteria")
async def add_criterion(tender_id: str, criterion: CriterionCreate, officer_id: str = "SYSTEM_OR_OFFICER"):
    db_record = criterion.model_dump()
    db_record["tender_id"] = tender_id
    res = supabase.table("criteria").insert(db_record).execute()
    
    if res.data:
        log_audit_action(
            action_type="CRITERION_ADD",
            actor=officer_id,
            target_type="criterion",
            target_id=res.data[0]["id"],
            result="created",
            metadata={"tender_id": tender_id, "code": criterion.criterion_code}
        )
    return res.data[0]
