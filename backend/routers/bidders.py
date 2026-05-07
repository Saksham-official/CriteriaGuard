from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Any
import os
import shutil
import uuid

from db.database import get_db
from services.pdf_extractor import extract_text_from_pdf
from services.docx_extractor import extract_text_from_docx
from services.image_preprocessor import preprocess_image
from services.ocr import extract_text_from_image
from engines.doc_probe import extract_value_for_criterion
from engines.verdict_core import compute_verdict
from services.audit import log_audit_action
from utils.logger import logger

router = APIRouter(prefix="/api/bidders", tags=["bidders"])

UPLOAD_DIR = "uploads/bidders"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_bidder_documents(tender_id: str, bidder_id: str, file_paths: List[str], file_names: List[str]):
    try:
        db = get_db()
        # 1. Fetch APPROVED criteria for this tender
        criteria_res = db.table("criteria").select("*").eq("tender_id", tender_id).not_.is_("approved_at", "null").execute()
        criteria = criteria_res.data

        # 2. Extract text from all documents
        all_docs_text = []
        temp_files_to_cleanup = []

        for fpath, fname in zip(file_paths, file_names):
            ext = os.path.splitext(fpath)[1].lower()
            if ext not in ['.pdf', '.docx', '.jpg', '.jpeg', '.png', '.tiff']:
                logger.warning(f"Skipping unsupported file: {fname}")
                continue

            try:
                if ext == '.pdf':
                    pages = extract_text_from_pdf(fpath)
                    for page in pages:
                        all_docs_text.append({
                            "label": f"[{fname}, PAGE_{page.page_number}]",
                            "text": page.text,
                            "filename": fname
                        })
                elif ext == '.docx':
                    pages = extract_text_from_docx(fpath)
                    for page in pages:
                        all_docs_text.append({
                            "label": f"[{fname}, PAGE_{page.page_number}]",
                            "text": page.text,
                            "filename": fname
                        })
                elif ext in ['.jpg', '.jpeg', '.png', '.tiff']:
                    prep_name = f"{fpath}_prep.png"
                    preprocessed_path = preprocess_image(fpath, prep_name)
                    temp_files_to_cleanup.append(prep_name)
                    ocr_result = extract_text_from_image(preprocessed_path)
                    if ocr_result.text:
                        all_docs_text.append({
                            "label": f"[{fname}, PAGE_1]",
                            "text": ocr_result.text,
                            "filename": fname
                        })
            except Exception as e:
                logger.error(f"Failed to parse document {fname}: {e}", exc_info=True)
                continue

        # 3. For each criterion, run DocProbe
        total_criteria = len(criteria)
        db.table("bidders").update({"total_count": total_criteria, "processed_count": 0}).eq("id", bidder_id).execute()

        for i, raw_criterion in enumerate(criteria):
            criterion: dict[str, Any] = raw_criterion  # type: ignore[assignment]
            try:
                current_label = criterion.get('category', 'Criterion')
                db.table("bidders").update({"current_step": f"Analyzing {current_label}..."}).eq("id", bidder_id).execute()

                # Context Filtering Logic
                keywords = {
                    "financial": ["balance", "turnover", "audit", "sheet", "profit", "loss", "ca ", "account", "net", "worth"],
                    "technical": ["completion", "work", "experience", "performance", "certificate", "technical", "engineer"],
                    "compliance": ["gst", "pan", "registration", "epfo", "esic", "msme", "udyam", "iso"],
                    "certification": ["iso", "license", "authority", "quality", "standard"]
                }

                cat = criterion.get("category", "").lower()
                relevant_keywords = keywords.get(cat, [])

                prioritized_text = []
                other_text = []

                for doc in all_docs_text:
                    is_relevant = any(k in doc["filename"].lower() or k in doc["text"].lower()[:500] for k in relevant_keywords)
                    if is_relevant:
                        prioritized_text.append(f"{doc['label']}\n{doc['text']}\n")
                    else:
                        other_text.append(f"{doc['label']}\n{doc['text']}\n")

                final_context = "\n".join(prioritized_text)
                if len(final_context) < 20000:
                    for text in other_text:
                        if len(final_context) + len(text) < 25000:
                            final_context += text
                        else:
                            break

                extraction = extract_value_for_criterion(dict(criterion), final_context)

                # Save extraction to DB
                ext_res = db.table("extractions").insert({
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

                if ext_res.data and len(ext_res.data) > 0:
                    extraction_dict: dict[str, Any] = ext_res.data[0]  # type: ignore[assignment]
                    extraction_id = str(extraction_dict["id"])

                    # 4. Compute Verdict
                    verdict = compute_verdict(dict(criterion), dict(extraction_dict))

                    db.table("verdicts").insert({
                        "criterion_id": criterion["id"],
                        "bidder_id": bidder_id,
                        "extraction_id": extraction_id,
                        "status": verdict["status"],
                        "reason": verdict["reason"],
                        "review_sub_reason": verdict.get("review_sub_reason")
                    }).execute()
                else:
                    logger.error(f"Failed to save extraction for criterion {criterion['id']}")

                # Update progress
                db.table("bidders").update({"processed_count": i + 1}).eq("id", bidder_id).execute()

            except Exception as e:
                logger.error(f"Error extracting for criterion {criterion['id']}: {e}", exc_info=True)

        # Cleanup temp files and original uploads
        for f in temp_files_to_cleanup:
            if os.path.exists(f):
                os.remove(f)

        for f in file_paths:
            if os.path.exists(f):
                os.remove(f)

        # Update bidder status
        db.table("bidders").update({
            "status": "complete",
            "current_step": "Processing finished"
        }).eq("id", bidder_id).execute()

    except Exception as global_e:
        logger.error(f"Global processing failure: {global_e}", exc_info=True)
        try:
            get_db().table("bidders").update({
                "status": "failed",
                "current_step": f"Error: {str(global_e)}"
            }).eq("id", bidder_id).execute()
        except Exception:
            pass


@router.post("/upload")
async def upload_bidder_documents(
    tender_id: str = Form(...),
    bidder_name: str = Form(...),
    officer_id: str = Form("SYSTEM_OR_OFFICER"),
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # 1. Validate files
    allowed_extensions = {'.pdf', '.docx', '.jpg', '.jpeg', '.png', '.tiff'}
    for file in files:
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File {filename} has unsupported format.")

    # 2. Create Bidder
    db = get_db()
    try:
        bidder_res = db.table("bidders").insert({
            "tender_id": tender_id,
            "name": bidder_name,
            "status": "processing",
            "created_by": officer_id
        }).execute()
        bidder_row: dict[str, Any] = bidder_res.data[0]  # type: ignore[assignment]
        bidder_id = str(bidder_row["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Log to Audit
    log_audit_action(
        action_type="BIDDER_UPLOAD",
        actor=officer_id,
        target_type="bidder",
        target_id=bidder_id,
        result="success",
        metadata={"bidder_name": bidder_name, "files_count": len(files)}
    )

    # 3. Save Files
    saved_paths = []
    file_names = []
    for file in files:
        file_id = str(uuid.uuid4())
        filename = file.filename or f"upload_{file_id}"
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved_paths.append(file_path)
        file_names.append(filename)

    # 4. Start processing in background
    background_tasks.add_task(process_bidder_documents, tender_id, bidder_id, saved_paths, file_names)

    return {"message": "Documents uploaded. Processing started.", "bidder_id": bidder_id}

@router.get("/{bidder_id}/extractions")
async def get_bidder_extractions(bidder_id: str):
    res = get_db().table("extractions").select("*").eq("bidder_id", bidder_id).execute()
    return res.data
