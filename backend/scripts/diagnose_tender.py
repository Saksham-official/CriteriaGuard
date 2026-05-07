"""
Diagnostic script: run this directly to test what's happening with a PDF.
Usage (from backend/ dir):
    python scripts/diagnose_tender.py <path_to_pdf>
"""
import sys
import os
import json

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.pdf_extractor import extract_text_from_pdf, format_pages_for_prompt
from engines.criteria_lens import extract_criteria_from_text
from utils.logger import setup_logging, logger

setup_logging()

def main():
    if len(sys.argv) < 2:
        # Try to find the most recent upload automatically
        upload_dir = "uploads/tenders"
        if os.path.isdir(upload_dir):
            files = sorted(
                [f for f in os.listdir(upload_dir) if f.endswith(".pdf")],
                key=lambda f: os.path.getmtime(os.path.join(upload_dir, f)),
                reverse=True
            )
            if files:
                pdf_path = os.path.join(upload_dir, files[0])
                print(f"No path given, using most recent upload: {pdf_path}\n")
            else:
                print("Usage: python scripts/diagnose_tender.py <path_to_pdf>")
                sys.exit(1)
        else:
            print("Usage: python scripts/diagnose_tender.py <path_to_pdf>")
            sys.exit(1)
    else:
        pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    print("=" * 60)
    print(f"DIAGNOSING: {pdf_path}")
    print("=" * 60)

    # Step 1: Extract text WITHOUT OCR (fast, baseline check)
    print("\n[STEP 1] Extracting text WITHOUT OCR (native text only)...")
    pages_no_ocr = extract_text_from_pdf(pdf_path, enable_ocr=False)
    print(f"  Pages found (no OCR): {len(pages_no_ocr)}")
    for p in pages_no_ocr[:3]:
        print(f"    Page {p.page_number}: {len(p.text)} chars — first 150: {repr(p.text[:150])}")

    if not pages_no_ocr:
        print("  WARNING: No text extracted at all — PDF is likely fully scanned/image-based.")
    
    # Step 2: Extract with OCR
    print("\n[STEP 2] Extracting text WITH OCR (full pipeline)...")
    pages = extract_text_from_pdf(pdf_path, enable_ocr=True)
    print(f"  Pages found (with OCR): {len(pages)}")
    total_chars = sum(len(p.text) for p in pages)
    print(f"  Total characters: {total_chars}")
    
    if not pages:
        print("  FATAL: PDF extraction returned 0 pages. Check above for errors.")
        sys.exit(1)

    # Step 3: Format for prompt
    tender_text = format_pages_for_prompt(pages)
    print(f"\n[STEP 3] Formatted tender text: {len(tender_text)} chars")
    print(f"  First 500 chars:\n{tender_text[:500]}")
    print()

    if len(tender_text.strip()) < 200:
        print("FATAL: Text too short — LLM will not extract any criteria.")
        sys.exit(1)

    # Step 4: Test LLM extraction on first chunk only
    print("[STEP 4] Testing LLM criteria extraction (first 12000 chars only)...")
    test_text = tender_text[:12000]
    
    try:
        criteria_list = extract_criteria_from_text(test_text)
        print(f"\n  RESULT: {len(criteria_list)} criteria extracted")
        for c in criteria_list[:5]:
            print(f"    [{c.id}] {c.category} | mandatory={c.mandatory} | {c.text[:80]}...")
    except Exception as e:
        print(f"\n  EXCEPTION during extraction: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
