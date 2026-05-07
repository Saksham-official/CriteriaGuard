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
from utils.logger import logger
from db.database import get_db
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
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {', '.join(allowed_extensions)}"
        )

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Insert into Supabase 'tenders' table
    db = get_db()
    try:
        tender_res = db.table("tenders").insert({
            "title": filename,
            "file_path": file_path,
            "status": "processing",
            "created_by": officer_id
        }).execute()
        tender_row: dict[str, Any] = tender_res.data[0]  # type: ignore[assignment]
        tender_id = str(tender_row["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Log to Audit
    log_audit_action(
        action_type="TENDER_UPLOAD",
        actor=officer_id,
        target_type="tender",
        target_id=tender_id,
        result="success",
        metadata={"filename": filename}
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

    # Guard: if the entire extracted text is too short the LLM won't find anything.
    if len(tender_text.strip()) < 200:
        db.table("tenders").update({"status": "failed"}).eq("id", tender_id).execute()
        raise HTTPException(
            status_code=422,
            detail=(
                "Extracted text is too short to contain eligibility criteria. "
                "The PDF may be a scanned image without OCR support, password-protected, "
                "or contain no machine-readable text."
            )
        )

    logger.info(f"Tender {tender_id}: extracted {len(pages)} pages, {len(tender_text)} chars.")

    # 3. Extract criteria using LLM
    try:
        criteria_list = extract_criteria_from_text(tender_text)
        logger.info(f"Extracted {len(criteria_list)} criteria from tender {tender_id}")
    except Exception as e:
        logger.error(f"LLM extraction exception for tender {tender_id}: {e}", exc_info=True)
        db.table("tenders").update({"status": "failed"}).eq("id", tender_id).execute()
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {str(e)}")

    # 4. Save extracted criteria to DB
    criteria_inserts = []
    for i, criterion in enumerate(criteria_list):
        crit_dict = criterion.model_dump()

        db_record: dict[str, Any] = {
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

    if not criteria_inserts:
        db.table("tenders").update({"status": "failed"}).eq("id", tender_id).execute()
        logger.error(
            f"No criteria extracted for tender {tender_id}. "
            f"Text length: {len(tender_text)} chars, pages: {len(pages)}. "
            "Check logs above for LLM raw output to diagnose the issue."
        )
        raise HTTPException(
            status_code=422,
            detail=(
                "No eligibility criteria could be extracted. Possible causes: "
                "(1) Groq API rate limit hit — wait 60s and retry, "
                "(2) Document has no eligibility/qualification section, "
                "(3) GROQ_API_KEY is invalid or quota exhausted. "
                "Check server logs for the exact LLM response."
            )
        )

    db.table("criteria").insert(criteria_inserts).execute()

    # Update tender status
    db.table("tenders").update({"status": "criteria_review"}).eq("id", tender_id).execute()

    return {"message": "Tender processed successfully", "tender_id": tender_id}

@router.get("/{tender_id}/criteria")
async def get_criteria(tender_id: str):
    res = get_db().table("criteria").select("*").eq("tender_id", tender_id).execute()
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
    res = get_db().table("criteria").update(data).eq("id", criterion_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Criterion not found")

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
    res = get_db().table("criteria").delete().eq("id", criterion_id).execute()
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
    res = get_db().table("criteria").insert(db_record).execute()

    if res.data:
        new_row: dict[str, Any] = res.data[0]  # type: ignore[assignment]
        log_audit_action(
            action_type="CRITERION_ADD",
            actor=officer_id,
            target_type="criterion",
            target_id=str(new_row["id"]),
            result="created",
            metadata={"tender_id": tender_id, "code": criterion.criterion_code}
        )
        return new_row
    raise HTTPException(status_code=500, detail="Failed to add criterion")
