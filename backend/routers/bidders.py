from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List
import os
import shutil
import uuid

from db.database import supabase
from services.pdf_extractor import extract_text_from_pdf
from services.docx_extractor import extract_text_from_docx
from services.image_preprocessor import preprocess_image
from services.ocr import extract_text_from_image
from engines.doc_probe import extract_value_for_criterion
from engines.verdict_core import compute_verdict

router = APIRouter(prefix="/api/bidders", tags=["bidders"])

UPLOAD_DIR = "uploads/bidders"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_bidder_documents(tender_id: str, bidder_id: str, file_paths: List[str], file_names: List[str]):
    # 1. Fetch criteria for this tender
    criteria_res = supabase.table("criteria").select("*").eq("tender_id", tender_id).execute()
    criteria = criteria_res.data
    
    # 2. Extract text from all documents
    all_docs_text = []
    for fpath, fname in zip(file_paths, file_names):
        ext = os.path.splitext(fpath)[1].lower()
        if ext == '.pdf':
            pages = extract_text_from_pdf(fpath)
            for page in pages:
                all_docs_text.append(f"[{fname}, PAGE_{page.page_number}]\n{page.text}\n")
        elif ext == '.docx':
            pages = extract_text_from_docx(fpath)
            for page in pages:
                all_docs_text.append(f"[{fname}, PAGE_{page.page_number}]\n{page.text}\n")
        elif ext in ['.jpg', '.jpeg', '.png']:
            preprocessed_path = preprocess_image(fpath, f"{fpath}_prep.png")
            ocr_result = extract_text_from_image(preprocessed_path)
            all_docs_text.append(f"[{fname}, PAGE_1]\n{ocr_result.text}\n")
            
    documents_context = "\n".join(all_docs_text)
    
    # 3. For each criterion, run DocProbe
    total_criteria = len(criteria)
    supabase.table("bidders").update({"total_count": total_criteria, "processed_count": 0}).eq("id", bidder_id).execute()
    
    for i, criterion in enumerate(criteria):
        try:
            current_label = criterion.get('category', 'Criterion')
            supabase.table("bidders").update({"current_step": f"Analyzing {current_label}..."}).eq("id", bidder_id).execute()
            
            extraction = extract_value_for_criterion(criterion, documents_context)
            
            # Save extraction to DB
            ext_res = supabase.table("extractions").insert({
                "criterion_id": criterion["id"],
                "bidder_id": bidder_id,
                "value_found": extraction.value_found,
                "not_found_reason": extraction.not_found_reason,
                "extracted_value": extraction.extracted_value,
                "extracted_value_numeric": extraction.extracted_value_numeric,
                "source_document": extraction.source_document,
                "source_page": extraction.source_page,
                "source_excerpt": extraction.source_excerpt,
                "ocr_quality": extraction.ocr_quality,
                "extraction_confidence": extraction.alignment_score * 0.5 + extraction.authenticity_score * 0.5
            }).execute()
            
            extraction_id = ext_res.data[0]["id"]
            
            # 4. Compute Verdict
            extraction_dict = ext_res.data[0]
            verdict = compute_verdict(criterion, extraction_dict)
            
            supabase.table("verdicts").insert({
                "criterion_id": criterion["id"],
                "bidder_id": bidder_id,
                "extraction_id": extraction_id,
                "status": verdict["status"],
                "reason": verdict["reason"],
                "review_sub_reason": verdict.get("review_sub_reason")
            }).execute()
            
            # Update progress
            supabase.table("bidders").update({"processed_count": i + 1}).eq("id", bidder_id).execute()
            
        except Exception as e:
            print(f"Error extracting for criterion {criterion['id']}: {e}")
            
    # Update bidder status
    supabase.table("bidders").update({
        "status": "complete",
        "current_step": "Processing finished"
    }).eq("id", bidder_id).execute()


@router.post("/upload")
async def upload_bidder_documents(
    tender_id: str = Form(...),
    bidder_name: str = Form(...),
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # 1. Create Bidder
    try:
        bidder_res = supabase.table("bidders").insert({
            "tender_id": tender_id,
            "name": bidder_name,
            "status": "processing"
        }).execute()
        bidder_id = bidder_res.data[0]["id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # 2. Save Files
    saved_paths = []
    file_names = []
    for file in files:
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        saved_paths.append(file_path)
        file_names.append(file.filename)
        
    # 3. Start processing in background
    background_tasks.add_task(process_bidder_documents, tender_id, bidder_id, saved_paths, file_names)
    
    return {"message": "Documents uploaded. Processing started.", "bidder_id": bidder_id}

@router.get("/{bidder_id}/extractions")
async def get_bidder_extractions(bidder_id: str):
    res = supabase.table("extractions").select("*").eq("bidder_id", bidder_id).execute()
    return res.data
