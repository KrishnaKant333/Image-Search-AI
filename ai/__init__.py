"""
AI Processing Package
Contains modules for OCR, color detection, and image classification
Optimized for web application usage with enhanced error handling and performance
"""

from .ocr import (
    extract_text,
    extract_text_with_positions,
    get_text_confidence,
    batch_extract_text,
    contains_text,
    search_text_in_image
)

from .color import (
    extract_dominant_colors,
    extract_dominant_colors_with_hex,
    get_primary_color,
    get_average_color,
    rgb_to_color_name,
    rgb_to_hex,
    hex_to_rgb,
    has_color,
    batch_extract_colors,
    is_monochrome
)

from .vision import (
    classify_image_type,
    get_image_metadata,
    detect_content_keywords,
    is_likely_meme,
    get_quality_score,
    batch_classify_images
)

__all__ = [
    # OCR functions
    'extract_text',
    'extract_text_with_positions',
    'get_text_confidence',
    'batch_extract_text',
    'contains_text',
    'search_text_in_image',

    # Color functions
    'extract_dominant_colors',
    'extract_dominant_colors_with_hex',
    'get_primary_color',
    'get_average_color',
    'rgb_to_color_name',
    'rgb_to_hex',
    'hex_to_rgb',
    'has_color',
    'batch_extract_colors',
    'is_monochrome',

    # Vision functions
    'classify_image_type',
    'get_image_metadata',
    'detect_content_keywords',
    'is_likely_meme',
    'get_quality_score',
    'batch_classify_images',
]

__version__ = '2.0.0'
