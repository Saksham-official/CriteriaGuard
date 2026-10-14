import base64
import os

from groq import Groq

from utils.logger import logger


class OCRResult:
    def __init__(self, text: str, confidence: float, quality: str):
        self.text = text
        self.confidence = confidence
        self.quality = quality


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def extract_text_from_image(image_path: str) -> OCRResult:
    """
    Extract text from images using Groq Vision or offline mock engine.
    """
    is_mock = os.getenv("MOCK_LLM", "").lower() in ("true", "1") or not os.getenv("GROQ_API_KEY")
    if is_mock:
        logger.info("OCR running in mock offline mode.")
        return OCRResult(
            text="[MOCK OCR TEXT] Audited Financial Statements and ISO 9001:2015 Certificate.",
            confidence=0.95,
            quality="high",
        )

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        base64_image = encode_image(image_path)

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all the text from this image exactly as written. Do not add any conversational text or formatting, just return the raw text found in the image.",
                        },
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
