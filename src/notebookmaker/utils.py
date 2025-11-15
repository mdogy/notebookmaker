"""Utility functions for processing lectures and generating notebooks."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import nbformat


def process_lecture(
    input_file: Path,
    output_dir: Path,
    provider: str = "anthropic",
    model: str | None = None,
) -> dict[str, Path]:
    """Process a lecture file and generate two Jupyter notebooks.

    Args:
        input_file: Path to the PDF or PowerPoint file
        output_dir: Directory where notebooks will be saved
        provider: LLM provider to use (default: "anthropic")
        model: Optional model name (uses provider default if None)

    Returns:
        Dictionary with paths to the generated notebooks:
            - "instructor": Path to instructor notebook
            - "student": Path to student notebook

    Raises:
        ValueError: If the input file format is not supported
        FileNotFoundError: If the input file doesn't exist
    """
    # Validate file exists
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Validate file extension
    supported_extensions = {".pdf", ".ppt", ".pptx"}
    if input_file.suffix.lower() not in supported_extensions:
        raise ValueError(
            f"Unsupported file format: {input_file.suffix}. "
            f"Supported formats: {', '.join(supported_extensions)}"
        )

    # Step 1: Extract content from PDF/PowerPoint
    if input_file.suffix.lower() == ".pdf":
        content = extract_pdf_content(input_file)
    else:  # .ppt or .pptx
        content = extract_powerpoint_content(input_file)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate base filename, checking for existing files
    base_name = input_file.stem

    # Helper function to generate unique filename
    def get_unique_path(base: str, suffix: str) -> Path:
        """Generate unique filename by adding numbers if file exists."""
        path = output_dir / f"{base}_{suffix}.ipynb"
        if not path.exists():
            return path

        # File exists, find next available number
        counter = 1
        while True:
            path = output_dir / f"{base}_{suffix}{counter}.ipynb"
            if not path.exists():
                return path
            counter += 1

    # Generate unique paths for both notebooks
    instructor_path = get_unique_path(base_name, "instructor")
    student_path = get_unique_path(base_name, "student")

    # Step 2: Generate instructor notebook
    generate_notebook(
        content=content,
        output_path=instructor_path,
        notebook_type="instructor",
        provider=provider,
        model=model,
    )

    # Step 3: Generate student notebook
    generate_notebook(
        content=content,
        output_path=student_path,
        notebook_type="student",
        provider=provider,
        model=model,
    )

    return {
        "instructor": instructor_path,
        "student": student_path,
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


def generate_notebook(
    content: str,
    output_path: Path,
    notebook_type: str = "student",
    provider: str = "anthropic",  # Will be validated at runtime
    model: str | None = None,
) -> None:
    """Generate a Jupyter notebook from lecture content using an LLM.

    Args:
        content: Extracted lecture content (from PDF/PowerPoint)
        output_path: Path where the notebook should be saved
        notebook_type: Type of notebook ("student" or "instructor")
        provider: LLM provider to use (default: "anthropic")
        model: Optional model name (uses provider default if None)

    Raises:
        ValueError: If notebook_type is invalid or content is empty
    """
    if notebook_type not in {"student", "instructor"}:
        raise ValueError(
            f"notebook_type must be 'student' or 'instructor', got: {notebook_type}"
        )

    if not content.strip():
        raise ValueError("Content cannot be empty")

    from typing import Literal, cast

    import nbformat

    from notebookmaker.llm import get_llm_config, get_provider

    # Validate provider at runtime
    valid_providers = {"anthropic", "google", "openai", "openrouter"}
    if provider not in valid_providers:
        provider_list = ", ".join(valid_providers)
        raise ValueError(
            f"Invalid provider: {provider}. Must be one of: {provider_list}"
        )

    # Get LLM configuration
    llm_config = get_llm_config()
    if not model:
        model = llm_config.get("model") if llm_config else None
    if not model:
        # Default models by provider
        defaults = {
            "anthropic": "claude-3-5-sonnet-20241022",
            "google": "gemini-2.0-flash-exp",
            "openai": "gpt-4o-mini",
            "openrouter": "anthropic/claude-3-5-sonnet",
        }
        model = defaults.get(provider, "claude-3-5-sonnet-20241022")

    # Create prompt for the LLM
    prompt = _create_notebook_prompt(content, notebook_type)

    # Get LLM provider (safe cast after validation)
    provider_literal = cast(
        Literal["anthropic", "google", "openai", "openrouter"], provider
    )
    llm = get_provider(provider_literal)

    # Generate notebook content from LLM
    from notebookmaker.llm import LLMMessage

    response = llm.generate(
        messages=[LLMMessage(role="user", content=prompt)],
        model=model,
        temperature=0.3,
        max_tokens=4000,
    )

    # Parse LLM response and create notebook
    nb = _parse_llm_response_to_notebook(response.content, notebook_type)

    # Save notebook
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)  # type: ignore[no-untyped-call]


def _load_prompt_fragment(fragment_name: str) -> str:
    """Load a prompt fragment from the prompts/fragments directory.

    Args:
        fragment_name: Name of the fragment file (without .md extension)

    Returns:
        Content of the fragment file
    """
    from pathlib import Path

    # Get the project root (assuming this file is in src/notebookmaker/)
    project_root = Path(__file__).parent.parent.parent
    fragment_path = project_root / "prompts" / "fragments" / f"{fragment_name}.md"

    if not fragment_path.exists():
        raise FileNotFoundError(f"Prompt fragment not found: {fragment_path}")

    with open(fragment_path, encoding="utf-8") as f:
        content = f.read()

    # Remove the markdown header if present (e.g., "# Role")
    lines = content.strip().split("\n")
    if lines and lines[0].startswith("#"):
        # Skip header and blank line after it
        content = "\n".join(lines[2:] if len(lines) > 2 else lines[1:])

    return content.strip()


def _create_notebook_prompt(content: str, notebook_type: str) -> str:
    """Create a prompt for the LLM to generate notebook content.

    Args:
        content: Extracted lecture content
        notebook_type: Type of notebook ("student" or "instructor")

    Returns:
        Formatted prompt for the LLM
    """
    from pathlib import Path

    # Get the project root
    project_root = Path(__file__).parent.parent.parent

    # Load the appropriate template
    if notebook_type == "student":
        template_path = project_root / "prompts" / "student_notebook_template.md"
    else:
        template_path = project_root / "prompts" / "instructor_notebook_template.md"

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    # Load all fragments
    fragments = {
        "role": _load_prompt_fragment("role"),
        "notebook_structure": _load_prompt_fragment("notebook_structure"),
        "student_version": _load_prompt_fragment("student_version"),
        "instructor_version": _load_prompt_fragment("instructor_version"),
        "tone": _load_prompt_fragment("tone"),
        "output_format": _load_prompt_fragment("output_format"),
        "content": content,
    }

    # Replace all placeholders in template
    prompt = template
    for key, value in fragments.items():
        prompt = prompt.replace(f"{{{key}}}", value)

    return prompt


def _parse_llm_response_to_notebook(
    llm_response: str, notebook_type: str
) -> nbformat.NotebookNode:
    """Parse LLM percent-formatted Python response into a Jupyter notebook.

    Args:
        llm_response: Percent-formatted Python from LLM (with # %% markers)
        notebook_type: Type of notebook

    Returns:
        NotebookNode object
    """
    import re

    from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

    # Extract Python code if wrapped in markdown code block
    content = llm_response.strip()
    code_block_match = re.search(r"```(?:python)?\s*\n(.*?)\n```", content, re.DOTALL)
    if code_block_match:
        content = code_block_match.group(1).strip()

    # Split by cell markers
    lines = content.split("\n")
    cells: list[nbformat.NotebookNode] = []
    current_cell_type: str | None = None
    current_cell_lines: list[str] = []

    def save_current_cell() -> None:
        """Save accumulated lines as a cell."""
        if current_cell_type is None or not current_cell_lines:
            return

        if current_cell_type == "markdown":
            # Remove '# ' prefix from each line
            markdown_lines = []
            for line in current_cell_lines:
                if line.startswith("# "):
                    markdown_lines.append(line[2:])
                elif line.startswith("#"):
                    # Just '#' with nothing after it
                    markdown_lines.append("")
                else:
                    # Line without '# ' prefix (shouldn't happen but handle it)
                    markdown_lines.append(line)
            cell_content = "\n".join(markdown_lines)
            cells.append(new_markdown_cell(cell_content))  # type: ignore[no-untyped-call]
        else:  # code
            cell_content = "\n".join(current_cell_lines)
            cells.append(new_code_cell(cell_content))  # type: ignore[no-untyped-call]

    for line in lines:
        # Check for cell markers
        if line.strip() == "# %% [markdown]":
            save_current_cell()
            current_cell_type = "markdown"
            current_cell_lines = []
        elif line.strip() == "# %%":
            save_current_cell()
            current_cell_type = "code"
            current_cell_lines = []
        else:
            # Add line to current cell
            if current_cell_type is not None:
                current_cell_lines.append(line)

    # Save the last cell
    save_current_cell()

    # If no cells were created, create an error cell
    if not cells:
        error_msg = (
            "# Error\n\n"
            "Failed to parse notebook content.\n\n"
            "Expected percent-formatted Python with `# %%` markers."
        )
        cells.append(new_markdown_cell(error_msg))  # type: ignore[no-untyped-call]

    # Create notebook
    nb = new_notebook(cells=cells)  # type: ignore[no-untyped-call]

    # Add metadata
    nb.metadata.update(
        {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11.0",
            },
        }
    )

    return nb  # type: ignore[no-any-return]
