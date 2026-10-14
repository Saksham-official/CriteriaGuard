from PIL import Image, ImageEnhance, ImageFilter

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
        with Image.open(image_path) as raw_img:
            # 1. Convert to grayscale
            processed: Image.Image = raw_img.convert("L")

            # 2. Contrast Enhancement
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(2.0)

            # 3. Sharpening to remove blur and noise
            processed = processed.filter(ImageFilter.SHARPEN)

            # Save the processed image
            processed.save(output_path, format="PNG")

        return output_path
    except Exception as e:
        logger.error(f"Error in image preprocessing: {e}", exc_info=True)
        # If preprocessing fails, return original path
        return image_path
