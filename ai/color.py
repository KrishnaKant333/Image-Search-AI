"""
Color Detection Module - Extract dominant colors from images
Maps RGB values to human-readable color names
"""

from PIL import Image
from collections import Counter
import math


# Human-readable color mapping
# Each color has RGB ranges for matching
COLOR_MAP = {
    'red': [(150, 0, 0), (255, 100, 100)],
    'orange': [(200, 100, 0), (255, 180, 100)],
    'yellow': [(200, 200, 0), (255, 255, 150)],
    'green': [(0, 100, 0), (150, 255, 150)],
    'blue': [(0, 0, 150), (150, 150, 255)],
    'purple': [(100, 0, 100), (200, 100, 200)],
    'pink': [(200, 100, 150), (255, 200, 220)],
    'brown': [(100, 50, 0), (180, 120, 80)],
    'black': [(0, 0, 0), (60, 60, 60)],
    'white': [(200, 200, 200), (255, 255, 255)],
    'gray': [(80, 80, 80), (180, 180, 180)],
    'grey': [(80, 80, 80), (180, 180, 180)],
    'cyan': [(0, 150, 150), (150, 255, 255)],
    'teal': [(0, 100, 100), (100, 180, 180)],
}


def rgb_to_color_name(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to the closest human-readable color name.

    Args:
        r, g, b: RGB color values (0-255)

    Returns:
        Human-readable color name
    """
    min_distance = float('inf')
    closest_color = 'unknown'

    for color_name, (low, high) in COLOR_MAP.items():
        # Calculate center of the color range
        center_r = (low[0] + high[0]) / 2
        center_g = (low[1] + high[1]) / 2
        center_b = (low[2] + high[2]) / 2

        # Calculate Euclidean distance
        distance = math.sqrt(
            (r - center_r) ** 2 +
            (g - center_g) ** 2 +
            (b - center_b) ** 2
        )

        if distance < min_distance:
            min_distance = distance
            closest_color = color_name

    return closest_color


def extract_dominant_colors(image_path: str, num_colors: int = 3) -> list:
    """
    Extract the dominant colors from an image.

    Args:
        image_path: Path to the image file
        num_colors: Number of dominant colors to return

    Returns:
        List of human-readable color names
    """
    try:
        # Open and resize image for faster processing
        image = Image.open(image_path)

        # Convert to RGB
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        # Resize for faster processing (sample the image)
        image = image.resize((100, 100))

        # Get all pixels
        pixels = list(image.getdata())



        # Quantize colors to reduce noise (round to nearest 20)
        quantized = []
        for r, g, b in pixels:
            quantized.append((
                (r // 30) * 30,
                (g // 30) * 30,
                (b // 30) * 30
            ))

        # Count occurrences
        color_counts = Counter(quantized)

        # Get most common colors
        most_common = color_counts.most_common(num_colors * 2)

        # Convert to color names, removing duplicates
        color_names = []
        seen = set()

        for (r, g, b), count in most_common:
            color_name = rgb_to_color_name(r, g, b)
            if color_name not in seen and color_name != 'unknown':
                color_names.append(color_name)
                seen.add(color_name)
                if len(color_names) >= num_colors:
                    break

        return color_names
    except Exception as e:
        print(f"Color extraction error for {image_path}: {e}")
        return []


def get_primary_color(image_path: str) -> str:
    """
    Get the single most dominant color in an image.

    Args:
        image_path: Path to the image file

    Returns:
        Primary color name
    """
    colors = extract_dominant_colors(image_path, num_colors=1)
    return colors[0] if colors else "unknown"
