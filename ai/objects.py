"""
Lightweight object/content detection using visual heuristics.
No ML models - uses color analysis, edge detection, and patterns.
"""

from PIL import Image
import numpy as np
from typing import List, Set


# Object/content categories we can detect
DETECTABLE_OBJECTS = [
    "text-heavy",    # Documents, presentations with lots of text
    "people",        # Likely contains people (skin tones)
    "nature",        # Plants, flowers, outdoor scenes
    "animals",       # Animal fur/patterns
]


def detect_objects(image_path: str, ocr_text: str = "") -> List[str]:
    """
    Detect likely objects/content in an image using heuristics.
    
    This provides hints about image content without heavy ML models.
    Uses color patterns, texture analysis, and OCR density.
    
    Args:
        image_path: Path to the image file
        ocr_text: OCR-extracted text (if available) for text density analysis
        
    Returns:
        List of detected object categories (e.g., ["text-heavy", "people"])
    """
    try:
        img = Image.open(image_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        detected = set()
        
        # Resize for performance
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        img_array = np.array(img)
        
        # --- TEXT-HEAVY DETECTION ---
        # High OCR density indicates text-heavy content
        if ocr_text and len(ocr_text) > 100:
            # Lots of text extracted = text-heavy image
            detected.add("text-heavy")
        elif _has_text_pattern(img_array):
            # Visual pattern suggests text even without OCR
            detected.add("text-heavy")
        
        # --- PEOPLE DETECTION ---
        # Look for skin tone colors
        if _has_skin_tones(img_array):
            detected.add("people")
        
        # --- NATURE DETECTION ---
        # Look for organic green patterns and natural color distribution
        if _has_nature_characteristics(img_array):
            detected.add("nature")
        
        # --- ANIMAL DETECTION ---
        # Look for fur/pattern textures and animal-like color patterns
        if _has_animal_characteristics(img_array):
            detected.add("animals")
        
        return sorted(list(detected))
        
    except Exception as e:
        print(f"Error detecting objects in {image_path}: {e}")
        return []


def _has_text_pattern(img_array: np.ndarray) -> bool:
    """
    Detect if image has visual patterns typical of text.
    
    Text images have:
    - High contrast regions (black text on white background)
    - Horizontal line patterns
    - Low color variance (mostly black/white)
    """
    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2).astype(np.uint8)
    else:
        gray = img_array
    
    h, w = gray.shape
    
    # Check for high contrast (bimodal distribution)
    # Text tends to cluster around black (0-50) and white (200-255)
    dark_pixels = np.sum(gray < 80)
    light_pixels = np.sum(gray > 180)
    mid_pixels = np.sum((gray >= 80) & (gray <= 180))
    
    total = h * w
    dark_ratio = dark_pixels / total
    light_ratio = light_pixels / total
    mid_ratio = mid_pixels / total
    
    # Text has high dark + light, low mid (bimodal)
    if dark_ratio > 0.1 and light_ratio > 0.4 and mid_ratio < 0.4:
        return True
    
    # Check for horizontal line patterns (text lines)
    row_variances = np.var(gray, axis=1)
    # Text lines have alternating high/low variance rows
    variance_changes = np.sum(np.abs(np.diff(row_variances)) > 200)
    if variance_changes > h * 0.3:  # Many variance changes = likely text lines
        return True
    
    return False


def _has_skin_tones(img_array: np.ndarray) -> bool:
    """
    Detect presence of human skin tones.
    
    Skin tones have specific RGB characteristics:
    - R > G > B (red channel dominant)
    - Moderate saturation
    - Specific hue range
    """
    # Sample pixels for performance
    h, w = img_array.shape[:2]
    total_pixels = h * w
    
    if total_pixels > 5000:
        flat = img_array.reshape(-1, 3)
        sample_indices = np.random.choice(len(flat), 5000, replace=False)
        pixels = flat[sample_indices]
    else:
        pixels = img_array.reshape(-1, 3)
    
    skin_pixels = 0
    
    for pixel in pixels:
        r, g, b = pixel
        
        # Skin tone characteristics
        # R > G > B pattern
        if not (r > g > b):
            continue
        
        # R-G and R-B differences in specific ranges
        if not (20 < r - g < 100):
            continue
        if not (30 < r - b < 150):
            continue
        
        # Brightness range (not too dark, not too bright)
        brightness = (int(r) + int(g) + int(b)) / 3
        if not (50 < brightness < 230):
            continue
        
        skin_pixels += 1
    
    # If >5% of sampled pixels are skin-toned, likely contains people
    skin_ratio = skin_pixels / len(pixels)
    return skin_ratio > 0.05


def _has_nature_characteristics(img_array: np.ndarray) -> bool:
    """
    Detect natural scenes (plants, flowers, outdoor).
    
    Nature images have:
    - Dominant green (plants)
    - High color variance (organic, not uniform)
    - Specific color distributions (earth tones, sky blues, plant greens)
    """
    h, w = img_array.shape[:2]
    total_pixels = h * w
    
    # Sample for performance
    if total_pixels > 5000:
        flat = img_array.reshape(-1, 3)
        sample_indices = np.random.choice(len(flat), 5000, replace=False)
        pixels = flat[sample_indices]
    else:
        pixels = img_array.reshape(-1, 3)
    
    # Count green-dominant pixels (plants/grass)
    green_pixels = 0
    blue_pixels = 0  # Sky
    brown_pixels = 0  # Earth/wood
    
    for pixel in pixels:
        r, g, b = pixel
        
        # Green-dominant (plants)
        if g > r and g > b and g > 80:
            green_pixels += 1
        
        # Blue-dominant (sky/water)
        if b > r and b > g and b > 100:
            blue_pixels += 1
        
        # Brown/earth tones
        if 60 < r < 150 and 40 < g < 120 and 20 < b < 80:
            if r > g > b:
                brown_pixels += 1
    
    total_sampled = len(pixels)
    green_ratio = green_pixels / total_sampled
    blue_ratio = blue_pixels / total_sampled
    brown_ratio = brown_pixels / total_sampled
    
    # Nature typically has significant green OR (blue + brown/green)
    if green_ratio > 0.25:  # Lots of plants
        return True
    
    if blue_ratio > 0.20 and (green_ratio > 0.10 or brown_ratio > 0.10):
        # Sky + plants/earth = outdoor scene
        return True
    
    # Check for organic color variance (not uniform like graphics)
    color_variance = np.var(pixels, axis=0).mean()
    if green_ratio > 0.15 and color_variance > 1000:
        # Moderate green + high variance = natural scene
        return True
    
    return False


def _has_animal_characteristics(img_array: np.ndarray) -> bool:
    """
    Detect likely presence of animals.
    
    Animals have:
    - Fur/feather textures (specific patterns)
    - Brown/tan colors common
    - Moderate texture variance
    """
    # Convert to grayscale for texture analysis
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2).astype(np.uint8)
    else:
        gray = img_array
    
    # Resize for performance
    small = Image.fromarray(gray).resize((100, 100), Image.Resampling.LANCZOS)
    small_array = np.array(small)
    
    # Analyze texture patterns
    # Fur has medium-frequency patterns (not smooth, not too chaotic)
    # Use local standard deviation as texture measure
    texture_scores = []
    
    h, w = small_array.shape
    window_size = 5
    
    for i in range(window_size, h - window_size, 2):
        for j in range(window_size, w - window_size, 2):
            window = small_array[i-window_size:i+window_size, 
                                j-window_size:j+window_size]
            texture_scores.append(np.std(window))
    
    if not texture_scores:
        return False
    
    avg_texture = np.mean(texture_scores)
    
    # Fur texture has moderate std (15-50 range typically)
    # Too low = smooth/uniform, too high = noisy/chaotic
    has_fur_texture = 15 < avg_texture < 50
    
    # Check for animal colors (browns, tans, blacks, whites)
    h, w = img_array.shape[:2]
    total_pixels = h * w
    
    if total_pixels > 5000:
        flat = img_array.reshape(-1, 3)
        sample_indices = np.random.choice(len(flat), 5000, replace=False)
        pixels = flat[sample_indices]
    else:
        pixels = img_array.reshape(-1, 3)
    
    animal_color_pixels = 0
    
    for pixel in pixels:
        r, g, b = pixel
        
        # Brown/tan (common for many animals)
        if 80 < r < 180 and 60 < g < 140 and 30 < b < 100:
            if r > g > b:
                animal_color_pixels += 1
        
        # Black fur
        if max(r, g, b) < 60:
            animal_color_pixels += 1
        
        # White fur
        if min(r, g, b) > 200:
            animal_color_pixels += 1
        
        # Orange/ginger (cats, foxes)
        if r > 180 and 80 < g < 150 and b < 80:
            animal_color_pixels += 1
    
    animal_color_ratio = animal_color_pixels / len(pixels)
    
    # Combine texture and color signals
    # Need both fur texture AND animal colors
    if has_fur_texture and animal_color_ratio > 0.3:
        return True
    
    return False


def get_object_hints(image_metadata: dict) -> List[str]:
    """
    Helper function to get object hints from existing metadata.
    
    This can be called by the search system to get object tags
    without re-processing the image.
    
    Args:
        image_metadata: Metadata dict containing 'objects' key
        
    Returns:
        List of object tags
    """
    return image_metadata.get('objects', [])
