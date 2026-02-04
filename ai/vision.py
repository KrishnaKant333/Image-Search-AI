"""
Vision Module - Classify image types and detect basic content
Identifies if an image is a photo, screenshot, document, etc.
"""

from PIL import Image
import os


def classify_image_type(image_path: str) -> str:
    """
    Classify an image into categories: photo, screenshot, document, or other.
    Uses heuristics based on image properties and content.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Image type: 'photo', 'screenshot', 'document', or 'other'
    """
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
        
        # Sample pixels for analysis
        rgb_image = rgb_image.resize((50, 50))
        pixels = list(rgb_image.getdata())
        
        # Calculate color variance
        r_vals = [p[0] for p in pixels]
        g_vals = [p[1] for p in pixels]
        b_vals = [p[2] for p in pixels]
        
        def variance(vals):
            mean = sum(vals) / len(vals)
            return sum((x - mean) ** 2 for x in vals) / len(vals)
        
        avg_variance = (variance(r_vals) + variance(g_vals) + variance(b_vals)) / 3
        
        # Calculate average brightness
        avg_brightness = sum(sum(p) / 3 for p in pixels) / len(pixels)
        
        # Heuristics for classification
        
        # Screenshots often have:
        # - High brightness (white backgrounds)
        # - Low color variance (flat colors)
        # - Common screen aspect ratios
        if avg_brightness > 200 and avg_variance < 2000:
            return 'screenshot'
        
        # Documents typically have:
        # - Very high brightness (paper white)
        # - Portrait orientation
        # - Very low variance
        if avg_brightness > 220 and aspect_ratio < 1 and avg_variance < 1500:
            return 'document'
        
        # Photos typically have:
        # - Higher color variance
        # - Common photo aspect ratios (4:3, 16:9, 3:2)
        if avg_variance > 3000:
            return 'photo'
        
        # Check filename hints
        if any(hint in filename for hint in ['screenshot', 'screen', 'capture']):
            return 'screenshot'
        if any(hint in filename for hint in ['doc', 'scan', 'pdf']):
            return 'document'
        if any(hint in filename for hint in ['img', 'photo', 'pic', 'dsc', 'jpg']):
            return 'photo'
        
        return 'other'
    
    except Exception as e:
        print(f"Classification error for {image_path}: {e}")
        return 'other'


def get_image_metadata(image_path: str) -> dict:
    """
    Extract basic metadata from an image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with image metadata
    """
    try:
        image = Image.open(image_path)
        
        return {
            'width': image.size[0],
            'height': image.size[1],
            'format': image.format or 'unknown',
            'mode': image.mode,
            'aspect_ratio': round(image.size[0] / image.size[1], 2) if image.size[1] > 0 else 1
        }
    except Exception as e:
        print(f"Metadata extraction error for {image_path}: {e}")
        return {}


def detect_content_keywords(image_path: str, ocr_text: str) -> list:
    """
    Generate content keywords based on image analysis and OCR text.
    
    Args:
        image_path: Path to the image file
        ocr_text: Previously extracted OCR text
        
    Returns:
        List of detected content keywords
    """
    keywords = []
    
    # Get image type
    image_type = classify_image_type(image_path)
    keywords.append(image_type)
    
    # Add keywords from OCR text analysis
    ocr_lower = ocr_text.lower()
    
    # Common document patterns
    if any(word in ocr_lower for word in ['upi', 'payment', 'transaction', 'paid', 'rupee', 'rs', 'inr', '₹']):
        keywords.append('payment')
        keywords.append('transaction')
        keywords.append('upi')
    
    if any(word in ocr_lower for word in ['invoice', 'bill', 'receipt', 'order']):
        keywords.append('bill')
        keywords.append('receipt')
    
    if any(word in ocr_lower for word in ['id', 'card', 'identity', 'college', 'university', 'student']):
        keywords.append('id card')
        keywords.append('identity')
    
    if any(word in ocr_lower for word in ['ticket', 'booking', 'flight', 'train', 'bus']):
        keywords.append('ticket')
        keywords.append('booking')
    
    if any(word in ocr_lower for word in ['email', 'mail', 'inbox', 'subject', 'from:', 'to:']):
        keywords.append('email')
    
    if any(word in ocr_lower for word in ['chat', 'message', 'whatsapp', 'telegram']):
        keywords.append('chat')
        keywords.append('message')
    
    return list(set(keywords))  # Remove duplicates
