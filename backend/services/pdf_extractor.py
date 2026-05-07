import pdfplumber
import fitz  # PyMuPDF
from typing import List
import os
from services.ocr import extract_text_from_image
from utils.logger import logger

class DocPage:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text

def extract_text_from_pdf(file_path: str) -> List[DocPage]:
    pages = []
    try:
        doc = fitz.open(file_path)
        for i, page in enumerate(doc):
            text = page.get_text().strip()
            
            # If text is missing or suspiciously short (scanned PDF), use OCR
            if not text or len(text) < 50:
                logger.info(f"Page {i+1} appears to be a scan. Triggering OCR...")
                # Render page to image
                pix = page.get_pixmap()
                temp_image = f"temp_page_{i}.png"
                pix.save(temp_image)
                
                ocr_res = extract_text_from_image(temp_image)
                if ocr_res.text:
                    text = ocr_res.text
                
                # Cleanup temp image
                if os.path.exists(temp_image):
                    os.remove(temp_image)
            
            if text:
                pages.append(DocPage(page_number=i + 1, text=text))
        doc.close()
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
    
    return pages

def format_pages_for_prompt(pages: List[DocPage], max_pages: int = None) -> str:
    """Combine pages into a single text block for the LLM prompt"""
    if max_pages and len(pages) > max_pages:
        # In a real scenario, we might use a summarizer or chunker
        pages = pages[:max_pages]
        
    formatted = []
    for page in pages:
        formatted.append(f"--- Page {page.page_number} ---\n{page.text}")
    return "\n\n".join(formatted)
