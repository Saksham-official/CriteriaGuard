import fitz  # PyMuPDF
from typing import List, Optional
import os
import uuid
from services.ocr import extract_text_from_image
from utils.logger import logger

# Maximum pages to extract — government tenders rarely need more than this;
# going beyond causes Groq rate-limit timeouts during criteria extraction.
MAX_PDF_PAGES = 40

# Minimum character count below which a page is considered a scanned image.
# Raised from 50 → 30 to avoid firing OCR for pages with short-but-real text.
SCAN_THRESHOLD = 30

class DocPage:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text

def extract_text_from_pdf(file_path: str, enable_ocr: bool = True) -> List[DocPage]:
    """
    Extract text from a PDF.

    Args:
        file_path: Path to the PDF file.
        enable_ocr: If True (default), attempt Groq Vision OCR for scanned pages.
                    Set to False to skip OCR and return only natively-extracted text,
                    which is much faster for large PDFs.
    """
    pages = []
    try:
        doc = fitz.open(file_path)
        total = min(doc.page_count, MAX_PDF_PAGES)
        if doc.page_count > MAX_PDF_PAGES:
            logger.warning(
                f"PDF has {doc.page_count} pages — truncating to first {MAX_PDF_PAGES} "
                "pages to stay within LLM token limits."
            )

        for i in range(total):
            page = doc.load_page(i)
            text = str(page.get_text()).strip()

            # Only OCR if text is truly absent (scanned page) and OCR is enabled
            if enable_ocr and (not text or len(text) < SCAN_THRESHOLD):
                logger.info(f"Page {i+1} appears to be a scan — triggering OCR...")
                temp_image = f"temp_{uuid.uuid4()}.png"
                try:
                    pix = page.get_pixmap(dpi=150)  # lower DPI = faster, still readable
                    pix.save(temp_image)
                    ocr_res = extract_text_from_image(temp_image)
                    if ocr_res.text:
                        text = ocr_res.text
                except Exception as ocr_err:
                    logger.warning(f"OCR failed for page {i+1}: {ocr_err}")
                finally:
                    if os.path.exists(temp_image):
                        os.remove(temp_image)

            if text:
                pages.append(DocPage(page_number=i + 1, text=text))

        doc.close()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}", exc_info=True)

    return pages

def format_pages_for_prompt(pages: List[DocPage], max_pages: Optional[int] = None) -> str:
    """Combine pages into a single text block for the LLM prompt."""
    if max_pages is not None and len(pages) > max_pages:
        pages = pages[:max_pages]

    formatted = []
    for page in pages:
        formatted.append(f"--- Page {page.page_number} ---\n{page.text}")
    return "\n\n".join(formatted)
