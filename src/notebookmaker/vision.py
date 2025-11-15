"""Vision and image processing utilities for multimodal LLM analysis."""

import base64
import io
import logging
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)


def extract_pdf_images(
    pdf_path: Path, chunk_size: int = 10, dpi: int = 150
) -> list[list[Image.Image]]:
    """
    Convert PDF pages to images and chunk them for API calls.

    Args:
        pdf_path: Path to the PDF file
        chunk_size: Number of pages per chunk (default: 10)
        dpi: Resolution for image conversion (default: 150)

    Returns:
        List of chunks, where each chunk is a list of PIL Image objects

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If pdf2image conversion fails

    Notes:
        - Requires poppler-utils to be installed on the system
        - Images are returned in RGB format
        - Higher DPI produces better quality but larger images (more tokens)
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    logger.info(f"Converting PDF to images: {pdf_path.name}")
    logger.info(f"  DPI: {dpi}, Chunk size: {chunk_size} pages")

    try:
        # Convert all pages to images
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            fmt="png",
            # Keep in memory (don't save to disk)
        )
        logger.info(f"  Converted {len(images)} pages successfully")

    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise

    # Split into chunks
    chunks: list[list[Image.Image]] = []
    for i in range(0, len(images), chunk_size):
        chunk = images[i : i + chunk_size]
        chunks.append(chunk)
        logger.debug(
            f"  Chunk {len(chunks)}: pages {i + 1}-{i + len(chunk)} "
            f"({len(chunk)} pages)"
        )

    logger.info(f"  Split into {len(chunks)} chunks")
    return chunks


def encode_image_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    Encode PIL Image to base64 string for API transmission.

    Args:
        image: PIL Image object
        format: Image format (PNG, JPEG, etc.)

    Returns:
        Base64-encoded string

    Notes:
        - PNG format preserves quality (recommended for text/equations)
        - JPEG is smaller but lossy (may degrade text readability)
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def resize_image_if_needed(
    image: Image.Image, max_width: int = 2048, max_height: int = 2048
) -> Image.Image:
    """
    Resize image if it exceeds maximum dimensions while preserving aspect ratio.

    Args:
        image: PIL Image to potentially resize
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels

    Returns:
        Resized image (or original if already within limits)

    Notes:
        - Maintains aspect ratio
        - Only resizes if image is too large
        - Helps control token usage
    """
    width, height = image.size

    if width <= max_width and height <= max_height:
        return image

    # Calculate scaling factor
    scale = min(max_width / width, max_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)

    logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
