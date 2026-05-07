import docx
from typing import List
from services.pdf_extractor import DocPage
from utils.logger import logger

def extract_text_from_docx(file_path: str) -> List[DocPage]:
    """
    Extracts text from a .docx file. 
    Since .docx doesn't have a strict concept of 'pages' like PDF, 
    we treat the whole document as Page 1.
    """
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        
        combined_text = "\n".join(full_text)
        
        # Return as a list with a single DocPage for consistency with PDF extractor
        return [DocPage(page_number=1, text=combined_text)]
    except Exception as e:
        logger.error(f"Docx extraction failed: {e}", exc_info=True)
        return []
