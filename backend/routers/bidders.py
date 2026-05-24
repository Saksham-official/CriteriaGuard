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
from engines.security_shield import scan_document_for_security
from services.audit import log_audit_action
from utils.logger import logger
from utils.websocket_manager import manager

router = APIRouter(prefix="/api/bidders", tags=["bidders"])

UPLOAD_DIR = "uploads/bidders"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_bidder_documents(tender_id: str, bidder_id: str, file_paths: List[str], file_names: List[str]):
    try:
        db = get_db()
        manager.broadcast(bidder_id, {
            "type": "status_update",
            "status": "processing",
            "current_step": "Fetching approved criteria..."
        })

        # 1. Fetch APPROVED criteria for this tender
        criteria_res = db.table("criteria").select("*").eq("tender_id", tender_id).not_.is_("approved_at", "null").execute()
        criteria = criteria_res.data

        if not criteria:
            logger.error(f"No approved criteria found for tender {tender_id}. Cannot process bidder {bidder_id}.")
            db.table("bidders").update({
                "status": "failed",
                "current_step": "Error: No approved criteria found for this tender. Please approve criteria first."
            }).eq("id", bidder_id).execute()
            manager.broadcast(bidder_id, {
                "type": "status_update",
                "status": "failed",
                "current_step": "Error: No approved criteria found."
            })
            return

        # 2. Extract text from all documents
        all_docs_text = []
        temp_files_to_cleanup = []

        manager.broadcast(bidder_id, {
            "type": "status_update",
            "status": "processing",
            "current_step": "Running security sanitization on documents..."
        })

        # Define aggregate security report
        security_report = {
            "is_safe": True,
            "tampering_detected": False,
            "injection_detected": False,
            "risk_level": "low",
            "tampering_details": [],
            "injection_details": [],
            "scanned_files": []
        }

        for fpath, fname in zip(file_paths, file_names):
            ext = os.path.splitext(fpath)[1].lower()
            if ext not in ['.pdf', '.docx', '.jpg', '.jpeg', '.png', '.tiff']:
                logger.warning(f"Skipping unsupported file: {fname}")
                continue

            # Run Security Scan first
            try:
                manager.broadcast(bidder_id, {
                    "type": "status_update",
                    "status": "processing",
                    "current_step": f"Scanning document security: {fname}..."
                })
                
                scan_res = scan_document_for_security(fpath, fname)
                security_report["scanned_files"].append({
                    "filename": fname,
                    "report": scan_res
                })
                
                if scan_res["tampering_detected"]:
                    security_report["tampering_detected"] = True
                    security_report["tampering_details"].extend(scan_res["tampering_details"])
                    if security_report["risk_level"] != "critical":
                        security_report["risk_level"] = "medium"
                        
                if scan_res["injection_detected"]:
                    security_report["injection_detected"] = True
                    security_report["injection_details"].extend(scan_res["injection_details"])
                    security_report["risk_level"] = "critical"
                    security_report["is_safe"] = False

                # Broadcast the live security scan result for this document
                manager.broadcast(bidder_id, {
                    "type": "security_scan",
                    "filename": fname,
                    "status": "failed" if scan_res["injection_detected"] else ("warning" if scan_res["tampering_detected"] else "passed"),
                    "report": scan_res
                })

                # Handle critical prompt injection block immediately
                if scan_res["injection_detected"]:
                    logger.critical(f"SecurityShield: CRITICAL prompt injection detected in {fname}! Halting pipeline.")
                    try:
                        db.table("bidders").update({
                            "status": "failed",
                            "current_step": "CRITICAL: Prompt Injection Blocked.",
                            "security_report": security_report
                        }).eq("id", bidder_id).execute()
                    except Exception as db_err:
                        logger.warning(f"Failed to update security_report column (schema cache stale?): {db_err}")
                        db.table("bidders").update({
                            "status": "failed",
                            "current_step": "CRITICAL: Prompt Injection Blocked."
                        }).eq("id", bidder_id).execute()
                    
                    manager.broadcast(bidder_id, {
                        "type": "status_update",
                        "status": "failed",
                        "current_step": "CRITICAL: Prompt Injection Blocked."
                    })
                    # Cleanup temp files and original uploads
                    for f in temp_files_to_cleanup:
                         if os.path.exists(f):
                             os.remove(f)
                    for f in file_paths:
                         if os.path.exists(f):
                             os.remove(f)
                    return

            except Exception as sec_e:
                logger.error(f"SecurityShield: Scan failed on {fname}: {sec_e}", exc_info=True)

            # Proceed to text extraction if document is deemed safe
            manager.broadcast(bidder_id, {
                "type": "status_update",
                "status": "processing",
                "current_step": f"Extracting text from {fname}..."
            })

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

        if not all_docs_text:
             logger.error(f"No text extracted from ANY documents for bidder {bidder_id}")
             db.table("bidders").update({
                 "status": "failed",
                 "current_step": "Error: Could not extract text from any uploaded documents."
             }).eq("id", bidder_id).execute()
             manager.broadcast(bidder_id, {
                 "type": "status_update",
                 "status": "failed",
                 "current_step": "Error: Text extraction failed."
             })
             return

        # Cache extracted text and broadcast to active WebSocket connections
        manager.extracted_text_cache[bidder_id] = all_docs_text
        manager.broadcast(bidder_id, {
            "type": "documents_extracted",
            "documents": all_docs_text
        })

        # 3. For each criterion, run DocProbe
        total_criteria = len(criteria)
        db.table("bidders").update({"total_count": total_criteria, "processed_count": 0}).eq("id", bidder_id).execute()

        for i, raw_criterion in enumerate(criteria):
            criterion: dict[str, Any] = raw_criterion  # type: ignore[assignment]
            try:
                current_label = criterion.get('category', 'Criterion')
                db.table("bidders").update({"current_step": f"Analyzing {current_label}..."}).eq("id", bidder_id).execute()

                # Broadcast criterion start event
                manager.broadcast(bidder_id, {
                    "type": "criterion_start",
                    "criterion": criterion
                })

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
                if len(final_context) < 15000:
                    for text in other_text:
                        if len(final_context) + len(text) < 18000:
                            final_context += text
                        else:
                            break

                # Stream callback for Groq delta extraction
                def handle_token(token: str):
                    manager.broadcast(bidder_id, {
                        "type": "llm_token",
                        "criterion_id": criterion["id"],
                        "token": token
                    })

                extraction = extract_value_for_criterion(dict(criterion), final_context, on_token=handle_token)

                # Save extraction to DB
                try:
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
                        source_doc_name = extraction_dict.get("source_document")
                        is_tampered_source = False
                        if source_doc_name:
                            for sf in security_report.get("scanned_files", []):
                                if sf["filename"] == source_doc_name:
                                    is_tampered_source = sf["report"].get("tampering_detected", False)
                                    break

                        verdict = compute_verdict(dict(criterion), dict(extraction_dict), is_tampered_source=is_tampered_source)

                        db.table("verdicts").insert({
                            "criterion_id": criterion["id"],
                            "bidder_id": bidder_id,
                            "extraction_id": extraction_id,
                            "status": verdict["status"],
                            "reason": verdict["reason"],
                            "review_sub_reason": verdict.get("review_sub_reason")
                        }).execute()

                        # Broadcast final extraction and verdict
                        manager.broadcast(bidder_id, {
                            "type": "extraction_result",
                            "criterion_id": criterion["id"],
                            "extraction": extraction_dict,
                            "verdict": verdict
                        })
                    else:
                        logger.error(f"Failed to save extraction for criterion {criterion['id']}")
                except Exception as db_err:
                    logger.error(f"Database error during extraction/verdict save: {db_err}")

            except Exception as e:
                logger.error(f"Error extracting for criterion {criterion['id']}: {e}", exc_info=True)
            finally:
                # IMPORTANT: Always increment processed_count so the UI doesn't hang
                try:
                    db.table("bidders").update({"processed_count": i + 1}).eq("id", bidder_id).execute()
                except Exception as p_err:
                    logger.error(f"Failed to update processed_count: {p_err}")

        # Cleanup temp files and original uploads
        for f in temp_files_to_cleanup:
            if os.path.exists(f):
                os.remove(f)

        for f in file_paths:
            if os.path.exists(f):
                os.remove(f)

        # Cleanup cached documents
        if bidder_id in manager.extracted_text_cache:
            del manager.extracted_text_cache[bidder_id]

        # Update bidder status
        try:
            db.table("bidders").update({
                "status": "complete",
                "current_step": "Processing finished",
                "security_report": security_report
            }).eq("id", bidder_id).execute()
        except Exception as db_err:
            logger.warning(f"Failed to update security_report column (schema cache stale?): {db_err}")
            db.table("bidders").update({
                "status": "complete",
                "current_step": "Processing finished"
            }).eq("id", bidder_id).execute()

        # Broadcast completion
        manager.broadcast(bidder_id, {
            "type": "status_update",
            "status": "complete",
            "current_step": "Processing finished"
        })

    except Exception as global_e:
        logger.error(f"Global processing failure: {global_e}", exc_info=True)
        if bidder_id in manager.extracted_text_cache:
            del manager.extracted_text_cache[bidder_id]
        try:
            get_db().table("bidders").update({
                "status": "failed",
                "current_step": f"Error: {str(global_e)}"
            }).eq("id", bidder_id).execute()
            manager.broadcast(bidder_id, {
                "type": "status_update",
                "status": "failed",
                "current_step": f"Error: {str(global_e)}"
            })
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
