"""
Extract dominant colors from images and map to base color palette.
Maps similar shades to base colors for better search UX.
"""

from PIL import Image
import numpy as np
from typing import List, Tuple
from collections import Counter


# Base color palette - only these colors are returned
BASE_COLORS = [
    "red", "blue", "green", "yellow", 
    "black", "white", "gray", "brown", "purple"
]


# RGB ranges for base colors (center point and tolerance)
COLOR_DEFINITIONS = {
    "red": {
        "ranges": [
            ((200, 0, 0), (255, 100, 100)),    # Pure red
            ((150, 0, 0), (255, 50, 50)),      # Dark red/maroon
            ((255, 100, 150), (255, 200, 220)), # Pink
        ]
    },
    "blue": {
        "ranges": [
            ((0, 0, 150), (100, 100, 255)),    # Pure blue
            ((0, 100, 150), (100, 200, 255)),  # Cyan/teal
            ((0, 50, 100), (80, 150, 200)),    # Dark blue
        ]
    },
    "green": {
        "ranges": [
            ((0, 150, 0), (100, 255, 100)),    # Pure green
            ((0, 100, 0), (80, 180, 80)),      # Dark green
            ((100, 200, 100), (200, 255, 200)), # Light green
        ]
    },
    "yellow": {
        "ranges": [
            ((200, 200, 0), (255, 255, 100)),  # Pure yellow
            ((180, 180, 0), (255, 255, 150)),  # Gold/mustard
        ]
    },
    "purple": {
        "ranges": [
            ((128, 0, 128), (200, 100, 200)),  # Purple/violet
            ((100, 0, 150), (180, 80, 255)),   # Deep purple
        ]
    },
    "brown": {
        "ranges": [
            ((100, 50, 0), (180, 120, 80)),    # Brown
            ((80, 40, 0), (150, 100, 50)),     # Dark brown
        ]
    },
    "black": {
        "ranges": [
            ((0, 0, 0), (50, 50, 50)),         # True black
        ]
    },
    "white": {
        "ranges": [
            ((200, 200, 200), (255, 255, 255)), # White/very light
        ]
    },
    "gray": {
        "ranges": [
            ((50, 50, 50), (200, 200, 200)),   # Gray range
        ]
    },
}


def extract_colors(image_path: str, max_colors: int = 3) -> List[str]:
    """
    Extract dominant base colors from an image.
    
    Returns only base colors from the simplified palette.
    Maps similar shades (pink→red, cyan→blue, etc.) automatically.
    
    Args:
        image_path: Path to the image file
        max_colors: Maximum number of colors to return (default 3)
        
    Returns:
        List of base color names, ordered by dominance
    """
    try:
        img = Image.open(image_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize for performance (analyze smaller version)
        # This also helps focus on dominant colors vs. noise
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        # Get pixel data
        pixels = np.array(img).reshape(-1, 3)
        
        # Map each pixel to its closest base color
        color_counts = _map_pixels_to_base_colors(pixels)
        
        # Sort by frequency and return top N
        sorted_colors = [color for color, count in color_counts.most_common(max_colors)]
        
        # Always return at least one color
        if not sorted_colors:
            sorted_colors = ["gray"]  # Neutral fallback
        
        return sorted_colors
        
    except Exception as e:
        print(f"Error extracting colors from {image_path}: {e}")
        return ["gray"]  # Safe fallback


def _map_pixels_to_base_colors(pixels: np.ndarray) -> Counter:
    """
    Map each pixel to its closest base color.
    
    Uses RGB distance calculation to determine which base color
    each pixel belongs to. This automatically handles shade mapping
    (pink→red, maroon→red, cyan→blue, etc.)
    
    Returns:
        Counter object with base color frequencies
    """
    color_counts = Counter()
    
    # Sample pixels for large images (performance optimization)
    if len(pixels) > 5000:
        sample_indices = np.random.choice(len(pixels), 5000, replace=False)
        pixels = pixels[sample_indices]
    
    for pixel in pixels:
        r, g, b = pixel
        
        # Skip very transparent or invalid pixels
        if np.isnan(r) or np.isnan(g) or np.isnan(b):
            continue
        
        # Find closest base color
        closest_color = _classify_pixel_color(r, g, b)
        color_counts[closest_color] += 1
    
    return color_counts


def _classify_pixel_color(r: int, g: int, b: int) -> str:
    """
    Classify a single pixel RGB value to a base color.
    
    Strategy:
    1. Check if pixel falls within defined color ranges
    2. If not, use RGB-based heuristics
    3. Fallback to grayscale detection
    
    This handles shade mapping automatically:
    - Pink (255, 192, 203) → red (high R, moderate G/B)
    - Maroon (128, 0, 0) → red (dominant R)
    - Cyan (0, 255, 255) → blue (high G+B, low R)
    - Teal (0, 128, 128) → blue (moderate G+B, low R)
    """
    
    # First, check defined ranges for exact matches
    for color_name, definition in COLOR_DEFINITIONS.items():
        for min_rgb, max_rgb in definition["ranges"]:
            if (_in_range(r, min_rgb[0], max_rgb[0]) and
                _in_range(g, min_rgb[1], max_rgb[1]) and
                _in_range(b, min_rgb[2], max_rgb[2])):
                return color_name
    
    # If no exact match, use heuristic rules
    
    # Grayscale detection (R≈G≈B)
    if max(r, g, b) - min(r, g, b) < 30:
        if max(r, g, b) < 60:
            return "black"
        elif min(r, g, b) > 180:
            return "white"
        else:
            return "gray"
    
    # Find dominant channel
    max_channel = max(r, g, b)
    
    # RED family (includes pink, maroon, crimson)
    if r == max_channel and r > 100:
        # Pink detection: high red + moderate green/blue
        if g > 100 and b > 100:
            return "red"  # Pink → red
        # Maroon/dark red: dominant red
        return "red"
    
    # BLUE family (includes cyan, teal, navy)
    if b == max_channel and b > 100:
        # Cyan detection: high blue + high green, low red
        if g > 150 and r < 100:
            return "blue"  # Cyan → blue
        # Teal: moderate blue + green
        if g > 80:
            return "blue"  # Teal → blue
        return "blue"
    
    # GREEN family
    if g == max_channel and g > 100:
        # Yellow detection: high green + high red
        if r > 150 and b < 100:
            return "yellow"
        return "green"
    
    # PURPLE family (red + blue, low green)
    if r > 80 and b > 80 and g < min(r, b) - 30:
        return "purple"
    
    # BROWN family (moderate red + lower green)
    if r > 80 and g > 40 and g < r - 30 and b < g:
        return "brown"
    
    # Default fallback
    return "gray"


def _in_range(value: int, min_val: int, max_val: int) -> bool:
    """Check if value is within range (inclusive)."""
    return min_val <= value <= max_val


def get_color_variations(base_color: str) -> List[str]:
    """
    Get all color variations that map to a base color.
    
    This is used for search: when user searches "red",
    we want to match images tagged with red (including pink, maroon, etc.)
    
    Args:
        base_color: Base color name (e.g., "red")
        
    Returns:
        List containing the base color (for backward compatibility)
    """
    # Since we now only store base colors, just return the input
    # This function exists for backward compatibility with existing code
    if base_color in BASE_COLORS:
        return [base_color]
    
    # Handle legacy color names that might still exist in old data
    legacy_mapping = {
        "pink": "red",
        "maroon": "red",
        "crimson": "red",
        "cyan": "blue",
        "teal": "blue",
        "navy": "blue",
        "lime": "green",
        "olive": "green",
        "gold": "yellow",
        "orange": "yellow",  # Orange is close to yellow
        "tan": "brown",
        "beige": "brown",
        "violet": "purple",
        "magenta": "purple",
    }
    
    return [legacy_mapping.get(base_color.lower(), "gray")]
