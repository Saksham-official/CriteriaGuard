import os
import base64
from groq import Groq
from utils.logger import logger

class OCRResult:
    def __init__(self, text: str, confidence: float, quality: str):
        self.text = text
        self.confidence = confidence
        self.quality = quality

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_text_from_image(image_path: str) -> OCRResult:
    """
    Uses Groq's Llama 3.2 Vision model to extract text from images.
    This is completely free and leverages the existing Groq API key!
    """
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        base64_image = encode_image(image_path)
        
        response = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all the text from this image exactly as written. Do not add any conversational text or formatting, just return the raw text found in the image."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=4000,
        )
        
        text = response.choices[0].message.content or ""
        stripped_text = text.strip()
        confidence = 0.9 if len(stripped_text) > 10 else 0.4
        quality = "high" if len(stripped_text) > 50 else "low"
        
        return OCRResult(text=text, confidence=confidence, quality=quality)
        
    except Exception as e:
        logger.error(f"Groq Vision OCR failed: {e}", exc_info=True)
        return OCRResult(text="", confidence=0.0, quality="low")
