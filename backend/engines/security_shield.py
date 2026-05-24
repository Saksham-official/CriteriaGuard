import os
import re
import fitz  # PyMuPDF
from PIL import Image
from PIL.ExifTags import TAGS
from utils.logger import logger

def scan_document_for_security(file_path: str, filename: str) -> dict:
    """
    Scans a bidder submission document (PDF or Image) for security anomalies:
    1. Metadata tampering (Photoshop/Canva creation footprints on official sheets).
    2. Invisible or micro-text hidden layers (prompt injection vector).
    3. Adversarial text phrases (prompt injection classifier).
    
    Returns a structured security report.
    """
    logger.info(f"SecurityShield: Starting scanning for {filename}...")
    
    report = {
        "is_safe": True,
        "tampering_detected": False,
        "injection_detected": False,
        "risk_level": "low",
        "tampering_details": [],
        "injection_details": [],
        "metadata_summary": {}
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    
    # 1. SCAN METADATA & EXIF (Tampering Check)
    if ext == '.pdf':
        try:
            doc = fitz.open(file_path)
            meta = doc.metadata
            report["metadata_summary"] = {
                "format": "PDF",
                "creator": meta.get("creator", "Unknown"),
                "producer": meta.get("producer", "Unknown"),
                "author": meta.get("author", ""),
                "creation_date": meta.get("creationDate", ""),
                "mod_date": meta.get("modDate", "")
            }
            
            # Look for editing software footprints in standard pdf metadata
            suspicious_software = ["photoshop", "canva", "illustrator", "inkscape", "coreldraw", "gimp", "affinity"]
            creator_lower = str(meta.get("creator", "")).lower()
            producer_lower = str(meta.get("producer", "")).lower()
            
            for software in suspicious_software:
                if software in creator_lower or software in producer_lower:
                    # In official bidding certificates (like CA certificates, GST registry), 
                    # editing software signatures indicate potential document tampering/fabrication!
                    report["tampering_detected"] = True
                    report["tampering_details"].append(
                        f"Editing software signature ({software.capitalize()}) detected in file metadata creator/producer."
                    )
            
            # Check for hidden text layers and font abnormalities
            report = _scan_pdf_invisible_layers(doc, report)
            doc.close()
            
        except Exception as e:
            logger.error(f"SecurityShield: PDF metadata scan failed: {e}")
            report["tampering_details"].append(f"Failed to scan PDF structure: {str(e)}")
            
    elif ext in ['.jpg', '.jpeg', '.png', '.tiff']:
        try:
            img = Image.open(file_path)
            exif_data = {}
            info = img._getexif() # type: ignore
            if info:
                for tag, value in info.items():
                    decoded = TAGS.get(tag, tag)
                    exif_data[str(decoded)] = str(value)
            
            report["metadata_summary"] = {
                "format": "Image",
                "software": exif_data.get("Software", "Unknown"),
                "camera_model": exif_data.get("Model", "Unknown"),
                "date_time": exif_data.get("DateTime", "Unknown")
            }
            
            # Check for graphic editor software in EXIF
            software_field = exif_data.get("Software", "").lower()
            suspicious_software = ["photoshop", "canva", "illustrator", "gimp", "picsart", "lightroom"]
            for software in suspicious_software:
                if software in software_field:
                    report["tampering_detected"] = True
                    report["tampering_details"].append(
                        f"Image EXIF metadata indicates it was processed/saved using editing software: {software.capitalize()}."
                    )
        except Exception as e:
            logger.warning(f"SecurityShield: Image EXIF scan failed: {e}")
            
    # 2. RUN TEXT INJECTION CLASSIFIER ON COLLECTED TEXT
    # Extract native text for rapid keyword checks
    extracted_text = ""
    if ext == '.pdf':
        try:
            doc = fitz.open(file_path)
            extracted_text = "\n".join([page.get_text().strip() for page in doc])
            doc.close()
        except:
            pass
            
    if extracted_text:
        report = _scan_text_for_injections(extracted_text, report)
        
    # 3. CONSOLIDATE RISK LEVEL
    if report["injection_detected"]:
        report["risk_level"] = "critical"
        report["is_safe"] = False
    elif report["tampering_detected"]:
        report["risk_level"] = "medium"
        # We flag it as warning/medium, but don't strictly set is_safe to False
        # so that it allows analysis to complete but flags a security warning.
        report["is_safe"] = True
        
    logger.info(f"SecurityShield: Completed scan. Risk: {report['risk_level'].upper()}. Safe: {report['is_safe']}")
    return report

def _scan_pdf_invisible_layers(doc: fitz.Document, report: dict) -> dict:
    """Scans individual span details in PDF to find zero-size fonts or white-on-white hidden text."""
    try:
        for i, page in enumerate(doc):
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                            
                        size = span.get("size", 10)
                        color_int = span.get("color", 0)
                        
                        # Convert integer color to RGB
                        r = (color_int >> 16) & 255
                        g = (color_int >> 8) & 255
                        b = color_int & 255
                        
                        # 1. Micro-font Detection (Text size < 3pt is highly suspicious hidden prompt)
                        if size < 3.0:
                            report["injection_detected"] = True
                            report["injection_details"].append(
                                f"Page {i+1}: Obfuscated micro-font size ({size:.1f}pt) detected containing text snippet: '{text[:30]}...'"
                            )
                            
                        # 2. Invisible White Text Detection
                        # Default page background is white (RGB 255, 255, 255).
                        # If text is extremely near white, it is invisible to humans but read by LLMs.
                        if r > 245 and g > 245 and b > 245:
                            report["injection_detected"] = True
                            report["injection_details"].append(
                                f"Page {i+1}: Invisible white text block detected containing: '{text[:40]}...'"
                            )
    except Exception as e:
        logger.warning(f"SecurityShield: Detailed span layout scanning failed: {e}")
        
    return report

def _scan_text_for_injections(text: str, report: dict) -> dict:
    """Checks the text against standard prompt injection vectors and override command patterns."""
    injection_patterns = [
        r"(system\s+override|override\s+system)",
        r"(ignore\s+all\s+previous|ignore\s+previous\s+instructions)",
        r"(always\s+output\s+eligible|always\s+mark\s+eligible)",
        r"set\s+eligibility\s+to\s+true",
        r"ignore\s+all\s+criteria",
        r"ignore\s+these\s+requirements",
        r"override\s+all\s+checks",
        r"\[\s*system\s+override\s*\]",
        r"you\s+must\s+evaluate\s+this\s+bidder\s+as\s+eligible"
    ]
    
    text_lower = text.lower()
    for pattern in injection_patterns:
        match = re.search(pattern, text_lower)
        if match:
            report["injection_detected"] = True
            matched_phrase = match.group(0)
            report["injection_details"].append(
                f"Adversarial prompt injection pattern '{matched_phrase}' detected in document text."
            )
            
    return report
