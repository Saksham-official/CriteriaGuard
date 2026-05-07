from PIL import Image, ImageEnhance, ImageFilter
import os
from utils.logger import logger

def preprocess_image(image_path: str, output_path: str) -> str:
    """
    Basic preprocessing using Pillow:
    1. Convert to grayscale
    2. Enhance contrast
    3. Apply mild sharpening
    In a full production setup, deskewing and adaptive thresholding would be added.
    """
    try:
        with Image.open(image_path) as img:
            # 1. Convert to grayscale
            img = img.convert('L')
            
            # 2. Contrast Enhancement
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # 3. Sharpening to remove blur and noise
            img = img.filter(ImageFilter.SHARPEN)
            
            # Save the processed image
            img.save(output_path, format="PNG")
            
        return output_path
    except Exception as e:
        logger.error(f"Error in image preprocessing: {e}", exc_info=True)
        # If preprocessing fails, return original path
        return image_path
