"""Utility functions for processing lectures and generating notebooks."""

from pathlib import Path


def process_lecture(input_file: Path, output_dir: Path) -> dict[str, Path]:
    """Process a lecture file and generate two Jupyter notebooks.

    Args:
        input_file: Path to the PDF or PowerPoint file
        output_dir: Directory where notebooks will be saved

    Returns:
        Dictionary with paths to the generated notebooks

    Raises:
        ValueError: If the input file format is not supported
    """
    # Validate file extension
    supported_extensions = {".pdf", ".ppt", ".pptx"}
    if input_file.suffix.lower() not in supported_extensions:
        raise ValueError(
            f"Unsupported file format: {input_file.suffix}. "
            f"Supported formats: {', '.join(supported_extensions)}"
        )

    # TODO: Implement lecture processing logic
    # This is a placeholder implementation
    base_name = input_file.stem
    notebook1_path = output_dir / f"{base_name}_part1.ipynb"
    notebook2_path = output_dir / f"{base_name}_part2.ipynb"

    # Placeholder: Create empty notebooks
    # In the actual implementation, this would:
    # 1. Extract content from PDF/PowerPoint
    # 2. Process the content using prompts
    # 3. Generate two Jupyter notebooks

    return {
        "notebook1": notebook1_path,
        "notebook2": notebook2_path,
    }


def extract_pdf_content(pdf_path: Path) -> str:
    """Extract text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text content from all pages, separated by page breaks

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If the file is not a valid PDF
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not pdf_path.suffix.lower() == ".pdf":
        raise ValueError(f"File must be a PDF, got: {pdf_path.suffix}")

    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        pages_text = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text.strip():  # Only include non-empty pages
                pages_text.append(f"--- Page {page_num} ---\n{text}")

        if not pages_text:
            return ""

        return "\n\n".join(pages_text)

    except Exception as e:
        raise ValueError(f"Error reading PDF file {pdf_path}: {e}") from e


def extract_powerpoint_content(pptx_path: Path) -> str:
    """Extract content from a PowerPoint file.

    Args:
        pptx_path: Path to the PowerPoint file

    Returns:
        Extracted text content from all slides, separated by slide breaks

    Raises:
        FileNotFoundError: If the PowerPoint file doesn't exist
        ValueError: If the file is not a valid PowerPoint
    """
    if not pptx_path.exists():
        raise FileNotFoundError(f"PowerPoint file not found: {pptx_path}")

    if pptx_path.suffix.lower() not in {".ppt", ".pptx"}:
        raise ValueError(
            f"File must be a PowerPoint file (.ppt or .pptx), got: {pptx_path.suffix}"
        )

    try:
        from pptx import Presentation

        prs = Presentation(str(pptx_path))
        slides_text = []

        for slide_num, slide in enumerate(prs.slides, start=1):
            slide_text = []
            slide_text.append(f"--- Slide {slide_num} ---")

            # Extract text from all shapes
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())

            if len(slide_text) > 1:  # More than just the header
                slides_text.append("\n".join(slide_text))

        if not slides_text:
            return ""

        return "\n\n".join(slides_text)

    except Exception as e:
        raise ValueError(
            f"Error reading PowerPoint file {pptx_path}: {e}"
        ) from e


def generate_notebook(content: str, output_path: Path, prompt_template: str) -> None:
    """Generate a Jupyter notebook from processed content.

    Args:
        content: Processed lecture content
        output_path: Path where the notebook should be saved
        prompt_template: Template for generating notebook content
    """
    # TODO: Implement notebook generation
    raise NotImplementedError("Notebook generation not yet implemented")
