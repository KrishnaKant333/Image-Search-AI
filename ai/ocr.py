"""
OCR Module - Extract text from images using EasyOCR
Handles screenshots, documents, bills, and any text-containing images
"""

import easyocr

# Initialize reader once (important for performance)
reader = easyocr.Reader(['en'], gpu=False)


def extract_text(image_path: str) -> str:
    """
    Extract all readable text from an image using EasyOCR.

    Args:
        image_path: Path to the image file

    Returns:
        Extracted text as a string (lowercase for easier matching)
    """
    try:
        results = reader.readtext(image_path)
        text = " ".join([res[1] for res in results])
        return " ".join(text.split()).lower()
    except Exception as e:
        print(f"OCR error for {image_path}: {e}")
        return ""


def get_text_confidence(image_path: str) -> float:
    """
    Get average confidence score for OCR results.

    Args:
        image_path: Path to the image file

    Returns:
        Average confidence score (0–100)
    """
    try:
        results = reader.readtext(image_path)
        if not results:
            return 0.0

        confidences = [res[2] * 100 for res in results]  # EasyOCR gives 0–1
        return sum(confidences) / len(confidences)
    except Exception as e:
        print(f"Confidence check error for {image_path}: {e}")
        return 0.0
