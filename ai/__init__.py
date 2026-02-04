"""
AI Processing Package
Contains modules for OCR, color detection, and image classification
"""

from .ocr import extract_text, get_text_confidence
from .color import extract_dominant_colors, get_primary_color
from .vision import classify_image_type, get_image_metadata, detect_content_keywords

__all__ = [
    'extract_text',
    'get_text_confidence',
    'extract_dominant_colors',
    'get_primary_color',
    'classify_image_type',
    'get_image_metadata',
    'detect_content_keywords'
]
