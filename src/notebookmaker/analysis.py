"""Phase 1: Multimodal analysis of PDF lecture materials."""

import json
import logging
from pathlib import Path
from typing import Any, Literal

from PIL import Image

from .llm import get_provider
from .llm.models import LLMMessage
from .models import LectureAnalysis
from .vision import encode_image_base64, extract_pdf_images, resize_image_if_needed

logger = logging.getLogger(__name__)


def _load_prompt_fragment(fragment_name: str) -> str:
    """
    Load a prompt fragment from the prompts/fragments directory.

    Args:
        fragment_name: Name of the fragment file (without .md extension)

    Returns:
        Content of the fragment file
    """
    # Get the project root (walk up from this file)
    current = Path(__file__)
    project_root = current.parent.parent.parent
    fragment_path = project_root / "prompts" / "fragments" / f"{fragment_name}.md"

    if not fragment_path.exists():
        raise FileNotFoundError(f"Prompt fragment not found: {fragment_path}")

    return fragment_path.read_text()


def analyze_pdf_chunk(
    images: list[Image.Image],
    chunk_index: int,
    total_chunks: int,
    provider: Literal["anthropic", "google", "openai", "openrouter"] = "google",
    model: str | None = None,
) -> dict[str, Any]:
    """
    Analyze a chunk of PDF pages using a vision LLM.

    Args:
        images: List of PIL Image objects for this chunk
        chunk_index: 0-based index of this chunk
        total_chunks: Total number of chunks being processed
        provider: LLM provider to use
        model: Model name (uses provider default if None)

    Returns:
        Dictionary with partial analysis (sections found in this chunk)

    Raises:
        ValueError: If LLM returns invalid JSON
    """
    logger.info(
        f"Analyzing chunk {chunk_index + 1}/{total_chunks} ({len(images)} pages)"
    )

    # Load prompt fragments
    analysis_instructions = _load_prompt_fragment("analysis_instructions")
    analysis_output_format = _load_prompt_fragment("analysis_output_format")

    # Build the prompt
    prompt = (
        "You are analyzing pages from a lecture PDF to extract structured "
        "information about code-worthy content.\n\n"
        f"This is chunk {chunk_index + 1} of {total_chunks}.\n"
        f"Pages in this chunk: approximately {chunk_index * 10 + 1} to "
        f"{chunk_index * 10 + len(images)}\n\n"
        f"{analysis_instructions}\n\n"
        f"{analysis_output_format}\n\n"
        "Analyze the images provided and output ONLY valid JSON matching the "
        "schema above."
    )

    # Get provider instance
    llm = get_provider(provider, api_key=None)

    # Create message with images (provider-specific handling)
    content_parts: list[Any] = []

    if provider == "google":
        # Google expects PIL Image objects directly (or text strings)
        content_parts.append(prompt)  # Text first
        for i, img in enumerate(images):
            # Resize if needed to control token usage
            resized_img = resize_image_if_needed(img, max_width=2048, max_height=2048)
            content_parts.append(resized_img)  # Add PIL Image directly
            logger.debug(f"  Image {i + 1}: {img.size}")
    elif provider == "anthropic":
        # Anthropic uses base64-encoded images
        logger.debug(f"Encoding {len(images)} images for Anthropic...")
        content_parts.append({"type": "text", "text": prompt})
        for i, img in enumerate(images):
            resized_img = resize_image_if_needed(img, max_width=2048, max_height=2048)
            b64_img = encode_image_base64(resized_img, format="PNG")
            content_parts.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": b64_img,
                    },
                }
            )
            logger.debug(f"  Image {i + 1}: {len(b64_img)} bytes (base64)")
    elif provider == "openai":
        # OpenAI uses base64-encoded images with data URL
        logger.debug(f"Encoding {len(images)} images for OpenAI...")
        content_parts.append({"type": "text", "text": prompt})
        for i, img in enumerate(images):
            resized_img = resize_image_if_needed(img, max_width=2048, max_height=2048)
            b64_img = encode_image_base64(resized_img, format="PNG")
            content_parts.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_img}",
                    },
                }
            )
            logger.debug(f"  Image {i + 1}: {len(b64_img)} bytes (base64)")
    else:
        raise ValueError(f"Vision analysis not yet supported for provider: {provider}")

    messages = [LLMMessage(role="user", content=content_parts)]

    # Determine model to use
    if model is None:
        # Use sensible defaults for each provider
        default_models = {
            "google": "gemini-2.0-flash-exp",
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4o",
            "openrouter": "anthropic/claude-3.5-sonnet",
        }
        model = default_models[provider]
        logger.info(f"Using default model for {provider}: {model}")

    # Call LLM
    logger.info(f"Calling {provider} vision LLM with model {model}...")
    response = llm.generate(
        messages=messages,
        model=model,
        max_tokens=2000,  # Compact analysis output
        temperature=0.3,  # Fairly deterministic
    )

    # Parse JSON response
    response_text = response.content.strip()
    logger.debug(f"LLM response ({len(response_text)} chars): {response_text[:200]}...")

    # Try to extract JSON (LLM might wrap it in markdown)
    if "```json" in response_text:
        # Extract from code block
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        response_text = response_text[start:end].strip()
    elif "```" in response_text:
        # Generic code block
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        response_text = response_text[start:end].strip()

    try:
        chunk_analysis: dict[str, Any] = json.loads(response_text)
        logger.info(
            f"  Parsed successfully: found "
            f"{len(chunk_analysis.get('sections', []))} sections"
        )
        return chunk_analysis
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Response was: {response_text}")
        raise ValueError(
            f"LLM returned invalid JSON in chunk {chunk_index + 1}: {e}"
        ) from e


def aggregate_chunk_analyses(
    chunk_results: list[dict[str, Any]], actual_total_pages: int
) -> LectureAnalysis:
    """
    Merge multiple chunk analyses into a single LectureAnalysis.

    Args:
        chunk_results: List of partial analysis dictionaries from chunks
        actual_total_pages: Actual total number of pages in the PDF

    Returns:
        Validated LectureAnalysis combining all chunks

    Notes:
        - Takes lecture_title and metadata from first chunk
        - Merges all sections from all chunks
        - Ensures section_ids are unique
        - Uses actual_total_pages (not summed from chunks)
    """
    if not chunk_results:
        raise ValueError("No chunk results to aggregate")

    logger.info(f"Aggregating {len(chunk_results)} chunk analyses...")

    # Take title and metadata from first chunk
    first_chunk = chunk_results[0]
    lecture_title = first_chunk.get("lecture_title", "Unknown Lecture")
    metadata = first_chunk.get("metadata", {})

    # Collect all sections
    all_sections = []
    seen_ids: set[str] = set()

    for i, chunk_result in enumerate(chunk_results):
        sections = chunk_result.get("sections", [])
        logger.debug(f"  Chunk {i + 1}: {len(sections)} sections")

        for section in sections:
            section_id = section.get("section_id")

            # Check for duplicate IDs
            if section_id in seen_ids:
                logger.warning(
                    f"Duplicate section_id '{section_id}' in chunk {i + 1}, skipping"
                )
                continue

            seen_ids.add(section_id)
            all_sections.append(section)

    # Use actual total pages from PDF (not summed from chunks)
    total_pages = actual_total_pages

    # Build aggregated analysis
    aggregated = {
        "lecture_title": lecture_title,
        "total_pages": total_pages,
        "sections": all_sections,
        "metadata": metadata,
    }

    # Validate with Pydantic
    analysis = LectureAnalysis(**aggregated)
    logger.info(
        f"Aggregation complete: {len(analysis.sections)} total sections, "
        f"{len(analysis.get_code_sections())} with code"
    )

    return analysis


def analyze_pdf(
    pdf_path: Path,
    output_path: Path | None = None,
    chunk_size: int = 10,
    provider: Literal["anthropic", "google", "openai", "openrouter"] = "google",
    model: str | None = None,
) -> LectureAnalysis:
    """
    Phase 1: Analyze a PDF lecture using vision LLM.

    Args:
        pdf_path: Path to PDF file
        output_path: Optional path to save analysis JSON (default: pdf_path with
            .analysis.json)
        chunk_size: Pages per API call (default: 10)
        provider: LLM provider for vision analysis
        model: Model name (uses provider default if None)

    Returns:
        LectureAnalysis object

    Raises:
        FileNotFoundError: If PDF doesn't exist
        ValueError: If analysis fails
    """
    logger.info(f"Starting Phase 1 analysis: {pdf_path.name}")
    logger.info(f"  Provider: {provider}, Model: {model or 'default'}")
    logger.info(f"  Chunk size: {chunk_size} pages")

    # Extract images
    image_chunks = extract_pdf_images(pdf_path, chunk_size=chunk_size)

    # Calculate actual total pages
    actual_total_pages = sum(len(chunk) for chunk in image_chunks)
    logger.info(f"Total pages in PDF: {actual_total_pages}")

    # Analyze each chunk
    chunk_results = []
    for i, images in enumerate(image_chunks):
        try:
            chunk_analysis = analyze_pdf_chunk(
                images,
                chunk_index=i,
                total_chunks=len(image_chunks),
                provider=provider,
                model=model,
            )
            chunk_results.append(chunk_analysis)
        except Exception as e:
            logger.error(f"Failed to analyze chunk {i + 1}: {e}")
            raise

    # Aggregate results
    analysis = aggregate_chunk_analyses(chunk_results, actual_total_pages)

    # Save to file if requested
    if output_path is None:
        output_path = pdf_path.with_suffix(".analysis.json")

    output_path.write_text(
        json.dumps(analysis.model_dump(), indent=2, ensure_ascii=False)
    )
    logger.info(f"Saved analysis to: {output_path}")

    return analysis
