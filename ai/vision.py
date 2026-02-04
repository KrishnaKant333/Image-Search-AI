"""
Vision Module - Classify image types and detect basic content
Identifies if an image is a photo, screenshot, document, etc.
Optimized for web app usage with improved classification and content detection
"""

from PIL import Image
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def classify_image_type(image_path: str) -> str:
    """
    Classify an image into categories: photo, screenshot, document, graphic, or other.
    Uses heuristics based on image properties and content.

    Args:
        image_path: Path to the image file

    Returns:
        Image type: 'photo', 'screenshot', 'document', 'graphic', or 'other'

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image file is invalid or corrupted
    """
    # Validate file exists
    if not Path(image_path).exists():
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        image = Image.open(image_path)
        width, height = image.size

        # Get image format info
        format_type = image.format or ''
        filename = os.path.basename(image_path).lower()

        # Check aspect ratio
        aspect_ratio = width / height if height > 0 else 1

        # Convert to RGB for analysis
        if image.mode in ('RGBA', 'P'):
            rgb_image = image.convert('RGB')
        else:
            rgb_image = image

        # Sample pixels for analysis (optimize performance)
        rgb_image = rgb_image.resize((50, 50), Image.Resampling.LANCZOS)
        pixels = list(rgb_image.getdata())

        # Calculate color statistics
        r_vals = [p[0] for p in pixels]
        g_vals = [p[1] for p in pixels]
        b_vals = [p[2] for p in pixels]

        def variance(vals):
            if not vals:
                return 0
            mean = sum(vals) / len(vals)
            return sum((x - mean) ** 2 for x in vals) / len(vals)

        avg_variance = (variance(r_vals) + variance(g_vals) + variance(b_vals)) / 3

        # Calculate average brightness
        avg_brightness = sum(sum(p) / 3 for p in pixels) / len(pixels)

        # Calculate color diversity
        unique_colors = len(set(pixels))
        color_diversity = unique_colors / len(pixels)

        # Detect edges (simplified edge detection)
        def detect_sharp_edges():
            edges = 0
            for i in range(len(pixels) - 1):
                r_diff = abs(pixels[i][0] - pixels[i+1][0])
                g_diff = abs(pixels[i][1] - pixels[i+1][1])
                b_diff = abs(pixels[i][2] - pixels[i+1][2])
                avg_diff = (r_diff + g_diff + b_diff) / 3
                if avg_diff > 50:
                    edges += 1
            return edges / len(pixels)

        edge_density = detect_sharp_edges()

        # Classification heuristics

        # Documents typically have:
        # - Very high brightness (paper white)
        # - Portrait orientation or A4-like aspect ratio
        # - Very low variance (mostly text on white)
        # - Low color diversity
        if (avg_brightness > 220 and
            avg_variance < 1500 and
            color_diversity < 0.3 and
            (aspect_ratio < 0.8 or 1.3 < aspect_ratio < 1.5)):
            logger.info(f"Classified {image_path} as document")
            return 'document'

        # Screenshots often have:
        # - High brightness (white backgrounds common in UIs)
        # - Low to medium color variance (flat UI colors)
        # - Common screen aspect ratios (16:9, 16:10)
        # - Sharp edges (UI elements)
        common_screen_ratios = [16/9, 16/10, 4/3, 3/2]
        is_screen_ratio = any(abs(aspect_ratio - ratio) < 0.1 for ratio in common_screen_ratios)

        if (avg_brightness > 180 and
            avg_variance < 3000 and
            edge_density > 0.15 and
            is_screen_ratio):
            logger.info(f"Classified {image_path} as screenshot")
            return 'screenshot'

        # Graphics/illustrations typically have:
        # - Low to medium variance
        # - Flat colors
        # - Low color diversity (limited palette)
        if avg_variance < 2500 and color_diversity < 0.4:
            logger.info(f"Classified {image_path} as graphic")
            return 'graphic'

        # Photos typically have:
        # - Higher color variance (natural scenes)
        # - Higher color diversity
        # - Common photo aspect ratios
        common_photo_ratios = [4/3, 3/2, 16/9]
        is_photo_ratio = any(abs(aspect_ratio - ratio) < 0.1 for ratio in common_photo_ratios)

        if avg_variance > 3000 and color_diversity > 0.4:
            logger.info(f"Classified {image_path} as photo")
            return 'photo'

        # Check filename hints as fallback
        filename_hints = {
            'screenshot': ['screenshot', 'screen', 'capture', 'snap'],
            'document': ['doc', 'scan', 'pdf', 'page'],
            'photo': ['img', 'photo', 'pic', 'dsc', 'jpg', 'jpeg', 'camera'],
            'graphic': ['icon', 'logo', 'graphic', 'illustration', 'vector']
        }

        for img_type, hints in filename_hints.items():
            if any(hint in filename for hint in hints):
                logger.info(f"Classified {image_path} as {img_type} (filename hint)")
                return img_type

        logger.info(f"Classified {image_path} as other (no match)")
        return 'other'

    except Exception as e:
        logger.error(f"Classification error for {image_path}: {e}")
        raise ValueError(f"Failed to classify image: {e}")


def get_image_metadata(image_path: str) -> Dict:
    """
    Extract comprehensive metadata from an image.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with image metadata including dimensions, format, mode, etc.

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image file is invalid or corrupted
    """
    if not Path(image_path).exists():
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        image = Image.open(image_path)
        file_stats = Path(image_path).stat()

        metadata = {
            'filename': os.path.basename(image_path),
            'width': image.size[0],
            'height': image.size[1],
            'format': image.format or 'unknown',
            'mode': image.mode,
            'aspect_ratio': round(image.size[0] / image.size[1], 2) if image.size[1] > 0 else 1,
            'file_size_bytes': file_stats.st_size,
            'file_size_mb': round(file_stats.st_size / (1024 * 1024), 2),
            'megapixels': round((image.size[0] * image.size[1]) / 1_000_000, 2),
            'orientation': 'portrait' if image.size[1] > image.size[0] else 'landscape' if image.size[0] > image.size[1] else 'square'
        }

        # Add EXIF data if available
        if hasattr(image, '_getexif') and image._getexif():
            exif_data = image._getexif()
            if exif_data:
                metadata['has_exif'] = True
                # Add common EXIF tags if present
                common_tags = {
                    271: 'camera_make',
                    272: 'camera_model',
                    306: 'datetime',
                    36867: 'datetime_original',
                }
                for tag_id, tag_name in common_tags.items():
                    if tag_id in exif_data:
                        metadata[tag_name] = exif_data[tag_id]
        else:
            metadata['has_exif'] = False

        logger.info(f"Extracted metadata from {image_path}")
        return metadata

    except Exception as e:
        logger.error(f"Metadata extraction error for {image_path}: {e}")
        raise ValueError(f"Failed to extract metadata: {e}")


def detect_content_keywords(image_path: str, ocr_text: str = "") -> List[str]:
    """
    Generate content keywords based on image analysis and OCR text.
    Enhanced with more comprehensive pattern detection.

    Args:
        image_path: Path to the image file
        ocr_text: Previously extracted OCR text (optional)

    Returns:
        List of detected content keywords (deduplicated)

    Raises:
        FileNotFoundError: If image file doesn't exist
    """
    if not Path(image_path).exists():
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    keywords = []

    # Get image type
    try:
        image_type = classify_image_type(image_path)
        keywords.append(image_type)
    except Exception as e:
        logger.warning(f"Could not classify image type: {e}")

    # Add keywords from OCR text analysis
    ocr_lower = ocr_text.lower()

    # Define keyword patterns
    keyword_patterns = {
        'payment': ['upi', 'payment', 'transaction', 'paid', 'rupee', 'rs', 'inr', '₹', 'paytm', 'gpay', 'phonepe'],
        'bill': ['invoice', 'bill', 'receipt', 'order', 'purchase'],
        'id_card': ['id', 'card', 'identity', 'college', 'university', 'student', 'employee'],
        'ticket': ['ticket', 'booking', 'flight', 'train', 'bus', 'reservation', 'pnr'],
        'email': ['email', 'mail', 'inbox', 'subject', 'from:', 'to:', 'gmail', 'outlook'],
        'chat': ['chat', 'message', 'whatsapp', 'telegram', 'messenger', 'conversation'],
        'social_media': ['instagram', 'facebook', 'twitter', 'linkedin', 'post', 'tweet', 'story'],
        'code': ['def ', 'function', 'import', 'class ', 'const ', 'var ', 'let ', '#!/'],
        'calendar': ['calendar', 'meeting', 'appointment', 'schedule', 'event', 'reminder'],
        'map': ['map', 'location', 'address', 'directions', 'route', 'navigation'],
        'weather': ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloudy'],
        'news': ['news', 'article', 'breaking', 'headline', 'press', 'report'],
        'shopping': ['cart', 'checkout', 'add to cart', 'buy now', 'price', 'product'],
        'education': ['assignment', 'homework', 'lecture', 'course', 'exam', 'quiz', 'grade'],
        'medical': ['prescription', 'doctor', 'patient', 'hospital', 'clinic', 'diagnosis', 'medicine'],
        'financial': ['bank', 'account', 'balance', 'statement', 'credit', 'debit', 'loan'],
        'travel': ['passport', 'visa', 'boarding', 'departure', 'arrival', 'hotel', 'itinerary'],
        'food': ['menu', 'order', 'delivery', 'restaurant', 'food', 'recipe', 'ingredients'],
    }

    # Check for pattern matches
    for category, patterns in keyword_patterns.items():
        if any(pattern in ocr_lower for pattern in patterns):
            keywords.append(category)

    # Get image orientation
    try:
        metadata = get_image_metadata(image_path)
        keywords.append(metadata['orientation'])
    except Exception as e:
        logger.warning(f"Could not get orientation: {e}")

    # Detect QR codes or barcodes (heuristic)
    if 'qr' in ocr_lower or 'barcode' in ocr_lower or 'scan' in ocr_lower:
        keywords.append('qr_code')
        keywords.append('scannable')

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            unique_keywords.append(keyword)
            seen.add(keyword)

    logger.info(f"Detected {len(unique_keywords)} keywords for {image_path}")
    return unique_keywords


def is_likely_meme(image_path: str, ocr_text: str = "") -> bool:
    """
    Detect if an image is likely a meme based on characteristics.

    Args:
        image_path: Path to the image file
        ocr_text: Previously extracted OCR text

    Returns:
        True if image appears to be a meme
    """
    try:
        # Memes often have text overlaid on images
        if not ocr_text or len(ocr_text.strip()) < 5:
            return False

        # Get image properties
        image = Image.open(image_path)
        width, height = image.size

        # Common meme formats are typically square or near-square
        aspect_ratio = width / height if height > 0 else 1
        is_square_ish = 0.8 < aspect_ratio < 1.2

        # Memes are often low resolution
        is_low_res = width < 800 and height < 800

        # Check for meme-like text patterns
        text_lower = ocr_text.lower()
        meme_indicators = [
            'when', 'me:', 'nobody:', 'everyone:', 'literally',
            'expectation vs reality', 'vs', 'be like'
        ]
        has_meme_text = any(indicator in text_lower for indicator in meme_indicators)

        # Memes often have impact font or text at top/bottom
        return (is_square_ish or is_low_res) and (has_meme_text or len(ocr_text.split()) < 20)

    except Exception as e:
        logger.error(f"Meme detection error for {image_path}: {e}")
        return False


def get_quality_score(image_path: str) -> float:
    """
    Calculate a quality score for the image based on resolution and sharpness.

    Args:
        image_path: Path to the image file

    Returns:
        Quality score from 0-100
    """
    try:
        image = Image.open(image_path)
        width, height = image.size

        # Resolution score (based on megapixels)
        megapixels = (width * height) / 1_000_000
        resolution_score = min(megapixels * 10, 50)  # Max 50 points

        # Sharpness score (basic edge detection)
        if image.mode in ('RGBA', 'P'):
            rgb_image = image.convert('RGB')
        else:
            rgb_image = image

        rgb_image = rgb_image.resize((100, 100), Image.Resampling.LANCZOS)
        pixels = list(rgb_image.getdata())

        # Calculate edge contrast
        edges = 0
        for i in range(len(pixels) - 1):
            r_diff = abs(pixels[i][0] - pixels[i+1][0])
            g_diff = abs(pixels[i][1] - pixels[i+1][1])
            b_diff = abs(pixels[i][2] - pixels[i+1][2])
            avg_diff = (r_diff + g_diff + b_diff) / 3
            if avg_diff > 30:
                edges += 1

        sharpness_score = min((edges / len(pixels)) * 500, 50)  # Max 50 points

        total_score = resolution_score + sharpness_score

        logger.info(f"Quality score for {image_path}: {total_score:.2f}")
        return round(total_score, 2)

    except Exception as e:
        logger.error(f"Quality score calculation error for {image_path}: {e}")
        return 0.0


def batch_classify_images(image_paths: List[str]) -> Dict[str, str]:
    """
    Classify multiple images in batch.

    Args:
        image_paths: List of image file paths

    Returns:
        Dictionary mapping image paths to their classifications
    """
    results = {}

    for image_path in image_paths:
        try:
            if not Path(image_path).exists():
                logger.warning(f"Skipping non-existent file: {image_path}")
                results[image_path] = 'unknown'
                continue

            classification = classify_image_type(image_path)
            results[image_path] = classification

        except Exception as e:
            logger.error(f"Batch classification error for {image_path}: {e}")
            results[image_path] = 'error'

    logger.info(f"Batch classified {len(image_paths)} images")
    return results
