"""Utility functions for processing lectures and generating notebooks."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def process_lecture(
    input_file: Path,
    output_dir: Path,
    analysis_provider: str = "google",
    generation_provider: str | None = None,
    analysis_model: str | None = None,
    generation_model: str | None = None,
    min_priority: int = 5,
    chunk_size: int = 10,
) -> dict[str, Path]:
    """Process a lecture file using two-phase architecture.

    This function implements the complete two-phase workflow:
    - Phase 1: Analyze PDF with vision LLM to extract code sections
    - Phase 2: Generate notebooks from analysis using text/vision LLM

    Args:
        input_file: Path to the PDF file
        output_dir: Directory where notebooks will be saved
        analysis_provider: LLM provider for Phase 1 (default: "google")
        generation_provider: LLM provider for Phase 2 (default: same as analysis)
        analysis_model: Model for Phase 1 (uses provider default if None)
        generation_model: Model for Phase 2 (uses provider default if None)
        min_priority: Minimum section priority to include (default: 5)
        chunk_size: Pages per API call in Phase 1 (default: 10)

    Returns:
        Dictionary with paths to generated files:
            - "analysis": Path to analysis.json
            - "instructor": Path to instructor notebook
            - "student": Path to student notebook

    Raises:
        ValueError: If the input file format is not supported
        FileNotFoundError: If the input file doesn't exist
    """
    from .analysis import analyze_pdf
    from .generation import generate_notebook_from_analysis, load_analysis_from_file

    # Validate file exists
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Only PDFs supported for two-phase workflow
    if input_file.suffix.lower() != ".pdf":
        raise ValueError(
            f"Two-phase workflow only supports PDF files. Got: {input_file.suffix}"
        )

    # Use same provider for generation if not specified
    if generation_provider is None:
        generation_provider = analysis_provider

    logger.info(f"Processing lecture: {input_file.name}")
    logger.info(f"  Analysis provider: {analysis_provider}")
    logger.info(f"  Generation provider: {generation_provider}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: Analyze PDF (or load existing analysis)
    analysis_path = input_file.with_suffix(".analysis.json")

    if analysis_path.exists():
        logger.info(f"Found existing analysis: {analysis_path.name}")
        logger.info("  Loading from file (delete to regenerate)")
        analysis = load_analysis_from_file(analysis_path)
    else:
        logger.info("Running Phase 1: Vision analysis")
        analysis = analyze_pdf(
            pdf_path=input_file,
            output_path=analysis_path,
            chunk_size=chunk_size,
            provider=analysis_provider,  # type: ignore[arg-type]
            model=analysis_model,
        )

    # Phase 2: Generate notebooks from analysis
    logger.info("Running Phase 2: Notebook generation")

    base_name = input_file.stem
    instructor_path = output_dir / f"{base_name}_instructor.ipynb"
    student_path = output_dir / f"{base_name}_student.ipynb"

    # Generate instructor notebook
    generate_notebook_from_analysis(
        analysis=analysis,
        output_path=instructor_path,
        notebook_type="instructor",
        min_priority=min_priority,
        provider=generation_provider,
        model=generation_model,
    )

    # Generate student notebook
    generate_notebook_from_analysis(
        analysis=analysis,
        output_path=student_path,
        notebook_type="student",
        min_priority=min_priority,
        provider=generation_provider,
        model=generation_model,
    )

    return {
        "analysis": analysis_path,
        "instructor": instructor_path,
        "student": student_path,
    }
