"""
Image preprocessing utilities for the vision pipeline.
Handles validation, format conversion, DICOM support, and thumbnail generation.
"""
import io
import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageOps

from backend.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_FORMATS = {"image/jpeg", "image/png", "image/webp"}
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_DIMENSION = 4096  # Max width/height before downscaling


def validate_image(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate image file for analysis pipeline.
    Returns (is_valid, error_message).
    """
    if not file_path.exists():
        return False, "Image file does not exist"

    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported image format '{suffix}'. Use: {', '.join(SUPPORTED_EXTENSIONS)}"

    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        return False, f"Image too large ({size_mb:.1f}MB). Maximum: {settings.MAX_UPLOAD_SIZE_MB}MB"

    # Verify it's a real image
    try:
        with Image.open(file_path) as img:
            img.verify()
    except Exception:
        return False, "File is not a valid image"

    return True, None


def prepare_for_analysis(file_path: Path) -> Path:
    """
    Prepare image for the ML pipeline:
    1. Convert to RGB (handles grayscale, RGBA, palette)
    2. Auto-orient based on EXIF
    3. Downscale if too large
    4. Save as PNG to temp directory
    Returns path to the prepared image.
    """
    import os
    output_path = Path(settings.TEMP_DIR) / f"prepared_{os.urandom(8).hex()}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(file_path) as img:
        # Auto-orient from EXIF
        img = ImageOps.exif_transpose(img)

        # Convert to RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Downscale if too large (preserve aspect ratio)
        if max(img.size) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
            logger.debug(f"Downscaled image to {img.size}")

        img.save(output_path, format="PNG", optimize=True)

    return output_path


def generate_thumbnail(file_path: Path, size: Tuple[int, int] = (256, 256)) -> bytes:
    """
    Generate a thumbnail for frontend preview display.
    Returns PNG bytes.
    """
    with Image.open(file_path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail(size, Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()


def get_image_metadata(file_path: Path) -> dict:
    """Extract basic metadata from an image file."""
    try:
        with Image.open(file_path) as img:
            return {
                "width": img.size[0],
                "height": img.size[1],
                "mode": img.mode,
                "format": img.format,
                "size_bytes": file_path.stat().st_size,
            }
    except Exception as e:
        return {"error": str(e)}


def cleanup_image_temp(file_path: Path):
    """Remove temporary image file."""
    try:
        if str(settings.TEMP_DIR) in str(file_path) and file_path.exists():
            file_path.unlink()
    except OSError:
        pass
