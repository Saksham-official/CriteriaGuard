import pdfplumber
import fitz  # PyMuPDF
from typing import List
import os

class DocPage:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text

def extract_text_from_pdf(file_path: str) -> List[DocPage]:
    pages = []
    try:
        # We primarily use pdfplumber for reliable text extraction
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages.append(DocPage(page_number=i + 1, text=text))
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")
        # Fallback to PyMuPDF
        try:
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                text = page.get_text()
                if text:
                    pages.append(DocPage(page_number=i + 1, text=text))
            doc.close()
        except Exception as e2:
            print(f"PyMuPDF fallback failed: {e2}")
    
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
