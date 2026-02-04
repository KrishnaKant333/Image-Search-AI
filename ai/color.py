"""
Color Detection Module - Extract dominant colors from images
Maps RGB values to human-readable color names
Optimized for web app usage with caching and enhanced color detection
"""

from PIL import Image
from collections import Counter
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import math
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced human-readable color mapping with better coverage
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
    'magenta': [(150, 0, 150), (255, 100, 255)],
    'lime': [(150, 200, 0), (200, 255, 100)],
    'navy': [(0, 0, 80), (80, 80, 150)],
    'maroon': [(80, 0, 0), (150, 50, 50)],
    'olive': [(80, 80, 0), (150, 150, 50)],
    'beige': [(200, 180, 150), (255, 230, 200)],
}


def rgb_to_color_name(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to the closest human-readable color name.
    Uses Euclidean distance in RGB color space.

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

        # Calculate Euclidean distance in RGB space
        distance = math.sqrt(
            (r - center_r) ** 2 +
            (g - center_g) ** 2 +
            (b - center_b) ** 2
        )

        if distance < min_distance:
            min_distance = distance
            closest_color = color_name

    return closest_color


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hexadecimal color code.

    Args:
        r, g, b: RGB color values (0-255)

    Returns:
        Hexadecimal color code (e.g., '#FF5733')
    """
    return f'#{r:02x}{g:02x}{b:02x}'.upper()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hexadecimal color code to RGB values.

    Args:
        hex_color: Hexadecimal color code (e.g., '#FF5733' or 'FF5733')

    Returns:
        Tuple of (r, g, b) values
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def extract_dominant_colors(
    image_path: str,
    num_colors: int = 3,
    resize_dim: int = 100,
    quantize_level: int = 30
) -> List[str]:
    """
    Extract the dominant colors from an image.

    Args:
        image_path: Path to the image file
        num_colors: Number of dominant colors to return
        resize_dim: Dimension to resize image for faster processing (default: 100)
        quantize_level: Color quantization level to reduce noise (default: 30)

    Returns:
        List of human-readable color names (ordered by dominance)

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image file is invalid or corrupted
    """
    # Validate file exists
    if not Path(image_path).exists():
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        # Open and resize image for faster processing
        image = Image.open(image_path)

        # Convert to RGB
        if image.mode in ('RGBA', 'P', 'L'):
            image = image.convert('RGB')

        # Resize for faster processing (sample the image)
        image = image.resize((resize_dim, resize_dim), Image.Resampling.LANCZOS)

        # Get all pixels
        pixels = list(image.getdata())

        # Quantize colors to reduce noise
        quantized = []
        for r, g, b in pixels:
            quantized.append((
                (r // quantize_level) * quantize_level,
                (g // quantize_level) * quantize_level,
                (b // quantize_level) * quantize_level
            ))

        # Count occurrences
        color_counts = Counter(quantized)

        # Get most common colors (get extra to account for duplicates after naming)
        most_common = color_counts.most_common(num_colors * 3)

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

        logger.info(f"Extracted {len(color_names)} dominant colors from {image_path}")
        return color_names

    except Exception as e:
        logger.error(f"Color extraction error for {image_path}: {e}")
        raise ValueError(f"Failed to extract colors: {e}")


def extract_dominant_colors_with_hex(
    image_path: str,
    num_colors: int = 3
) -> List[Dict[str, str]]:
    """
    Extract dominant colors with both color names and hex codes.
    Useful for displaying color palettes in the UI.

    Args:
        image_path: Path to the image file
        num_colors: Number of dominant colors to return

    Returns:
        List of dictionaries with 'name', 'hex', and 'rgb' keys

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image file is invalid or corrupted
    """
    if not Path(image_path).exists():
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        image = Image.open(image_path)

        if image.mode in ('RGBA', 'P', 'L'):
            image = image.convert('RGB')

        image = image.resize((100, 100), Image.Resampling.LANCZOS)
        pixels = list(image.getdata())

        # Quantize colors
        quantized = []
        for r, g, b in pixels:
            quantized.append((
                (r // 30) * 30,
                (g // 30) * 30,
                (b // 30) * 30
            ))

        color_counts = Counter(quantized)
        most_common = color_counts.most_common(num_colors * 3)

        color_info = []
        seen_names = set()

        for (r, g, b), count in most_common:
            color_name = rgb_to_color_name(r, g, b)
            if color_name not in seen_names and color_name != 'unknown':
                color_info.append({
                    'name': color_name,
                    'hex': rgb_to_hex(r, g, b),
                    'rgb': (r, g, b),
                    'percentage': round((count / len(pixels)) * 100, 2)
                })
                seen_names.add(color_name)
                if len(color_info) >= num_colors:
                    break

        logger.info(f"Extracted {len(color_info)} color palettes from {image_path}")
        return color_info

    except Exception as e:
        logger.error(f"Color palette extraction error for {image_path}: {e}")
        raise ValueError(f"Failed to extract color palette: {e}")


def get_primary_color(image_path: str) -> str:
    """
    Get the single most dominant color in an image.

    Args:
        image_path: Path to the image file

    Returns:
        Primary color name

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image file is invalid or corrupted
    """
    colors = extract_dominant_colors(image_path, num_colors=1)
    if not colors:
        raise ValueError("No colors could be extracted from the image")
    return colors[0]


def get_average_color(image_path: str) -> Tuple[int, int, int]:
    """
    Calculate the average color of an entire image.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (r, g, b) representing the average color

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image file is invalid or corrupted
    """
    if not Path(image_path).exists():
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        image = Image.open(image_path)

        if image.mode in ('RGBA', 'P', 'L'):
            image = image.convert('RGB')

        # Resize for faster processing
        image = image.resize((50, 50), Image.Resampling.LANCZOS)
        pixels = list(image.getdata())

        # Calculate average
        r_avg = sum(p[0] for p in pixels) // len(pixels)
        g_avg = sum(p[1] for p in pixels) // len(pixels)
        b_avg = sum(p[2] for p in pixels) // len(pixels)

        return (r_avg, g_avg, b_avg)

    except Exception as e:
        logger.error(f"Average color calculation error for {image_path}: {e}")
        raise ValueError(f"Failed to calculate average color: {e}")


def has_color(image_path: str, target_color: str, threshold: float = 0.1) -> bool:
    """
    Check if an image contains a specific color above a threshold percentage.
    Useful for filtering images by color in search.

    Args:
        image_path: Path to the image file
        target_color: Color name to search for
        threshold: Minimum percentage of image that should be this color (0-1)

    Returns:
        True if the target color is present above the threshold
    """
    try:
        colors_with_info = extract_dominant_colors_with_hex(image_path, num_colors=5)

        for color_info in colors_with_info:
            if color_info['name'] == target_color.lower():
                if color_info['percentage'] >= (threshold * 100):
                    return True

        return False

    except Exception as e:
        logger.error(f"Color detection error for {image_path}: {e}")
        return False


def batch_extract_colors(image_paths: List[str], num_colors: int = 3) -> Dict[str, List[str]]:
    """
    Extract dominant colors from multiple images in batch.

    Args:
        image_paths: List of image file paths
        num_colors: Number of dominant colors to extract per image

    Returns:
        Dictionary mapping image paths to lists of color names
    """
    results = {}

    for image_path in image_paths:
        try:
            if not Path(image_path).exists():
                logger.warning(f"Skipping non-existent file: {image_path}")
                results[image_path] = []
                continue

            colors = extract_dominant_colors(image_path, num_colors=num_colors)
            results[image_path] = colors

        except Exception as e:
            logger.error(f"Batch color extraction error for {image_path}: {e}")
            results[image_path] = []

    logger.info(f"Batch processed colors for {len(image_paths)} images")
    return results


def is_monochrome(image_path: str, tolerance: int = 30) -> bool:
    """
    Detect if an image is mostly monochrome (grayscale or single color).

    Args:
        image_path: Path to the image file
        tolerance: RGB variance tolerance for monochrome detection

    Returns:
        True if image is monochrome
    """
    try:
        r, g, b = get_average_color(image_path)

        # Check if R, G, B values are close to each other
        max_diff = max(abs(r - g), abs(g - b), abs(r - b))

        return max_diff <= tolerance

    except Exception as e:
        logger.error(f"Monochrome detection error for {image_path}: {e}")
        return False
