"""Phase 2: Generate Jupyter notebooks from analysis data."""

import json
import logging
import re
from pathlib import Path
from typing import Literal, cast

import nbformat
from nbformat.v4 import new_code_cell

from .llm import get_provider
from .llm.models import LLMMessage
from .models import LectureAnalysis, Section

logger = logging.getLogger(__name__)


def _load_prompt_fragment(fragment_name: str) -> str:
    """
    Load a prompt fragment from the prompts/fragments directory.

    Args:
        fragment_name: Name of the fragment file (without .md extension)

    Returns:
        Content of the fragment file
    """
    current = Path(__file__)
    project_root = current.parent.parent.parent
    fragment_path = project_root / "prompts" / "fragments" / f"{fragment_name}.md"

    if not fragment_path.exists():
        raise FileNotFoundError(f"Prompt fragment not found: {fragment_path}")

    return fragment_path.read_text()


def _build_section_context(section: Section, all_sections: list[Section]) -> str:
    """
    Build context string for a section including its dependencies.

    Args:
        section: The section to build context for
        all_sections: All sections in the analysis

    Returns:
        Formatted context string with section details and dependencies
    """
    context_parts = [
        f"## Section: {section.title}",
        f"Section ID: {section.section_id}",
        f"Priority: {section.priority}",
        f"Pages: {section.pages}",
    ]

    # Add dependencies context
    if section.dependencies:
        context_parts.append("\n### Dependencies:")
        section_map = {s.section_id: s for s in all_sections}
        for dep_id in section.dependencies:
            if dep_id in section_map:
                dep = section_map[dep_id]
                context_parts.append(f"- {dep.title} (builds on this concept)")

    # Add code snippets
    if section.code_snippets:
        context_parts.append("\n### Code Snippets:")
        for i, snippet in enumerate(section.code_snippets, 1):
            context_parts.append(f"\nSnippet {i} ({snippet.language}):")
            context_parts.append(f"```{snippet.language}")
            context_parts.append(snippet.code)
            context_parts.append("```")

    # Add equations
    if section.equations:
        context_parts.append("\n### Equations:")
        for eq in section.equations:
            latex = f"${eq.latex}$"
            if eq.description:
                context_parts.append(f"- {latex}: {eq.description}")
            else:
                context_parts.append(f"- {latex}")

    # Add concepts
    if section.concepts:
        context_parts.append(f"\n### Key Concepts: {', '.join(section.concepts)}")

    return "\n".join(context_parts)


def generate_notebook_for_section(
    section: Section,
    all_sections: list[Section],
    notebook_type: Literal["instructor", "student"],
    provider: str = "google",
    model: str | None = None,
) -> str:
    """
    Generate notebook cells for a single section using an LLM.

    Args:
        section: The section to generate cells for
        all_sections: All sections (for dependency context)
        notebook_type: Type of notebook to generate
        provider: LLM provider to use
        model: Model name (uses provider default if None)

    Returns:
        Percent-formatted Python string with notebook cells

    Raises:
        ValueError: If LLM returns invalid format
    """
    logger.info(f"Generating {notebook_type} cells for: {section.title}")

    # Load prompt fragments
    generation_instructions = _load_prompt_fragment("generation_instructions")
    output_format = _load_prompt_fragment("output_format")

    # Get notebook type-specific instructions
    if notebook_type == "instructor":
        type_specific = _load_prompt_fragment("instructor")
    else:
        type_specific = _load_prompt_fragment("student")

    # Build section context
    section_context = _build_section_context(section, all_sections)

    # Build the complete prompt
    prompt = f"""You are generating cells for a Jupyter notebook.

{generation_instructions}

{type_specific}

{output_format}

---

{section_context}

---

Generate ONLY the cells for this section using the percent format.
Include both markdown and code cells as appropriate.
"""

    # Get provider instance
    provider_literal = cast(
        Literal["anthropic", "google", "openai", "openrouter"], provider
    )
    llm = get_provider(provider_literal, api_key=None)

    # Determine model to use
    if model is None:
        default_models = {
            "google": "gemini-2.0-flash-exp",
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4o",
            "openrouter": "anthropic/claude-3.5-sonnet",
        }
        model = default_models.get(provider, "")
        logger.info(f"Using default model for {provider}: {model}")

    # Create message
    messages = [LLMMessage(role="user", content=prompt)]

    # Call LLM
    logger.info(f"Calling {provider} LLM with model {model}...")
    response = llm.generate(
        messages=messages,
        model=model,
        max_tokens=4000,  # Enough for complete section
        temperature=0.3,
    )

    # Extract response
    notebook_cells = response.content.strip()

    # Remove markdown code blocks if present
    if "```python" in notebook_cells:
        start = notebook_cells.find("```python") + 9
        end = notebook_cells.rfind("```")
        if end > start:
            notebook_cells = notebook_cells[start:end].strip()
    elif "```" in notebook_cells:
        start = notebook_cells.find("```") + 3
        end = notebook_cells.rfind("```")
        if end > start:
            notebook_cells = notebook_cells[start:end].strip()

    logger.info(f"  Generated {len(notebook_cells)} characters")
    return notebook_cells


def _consolidate_imports(notebook: nbformat.NotebookNode) -> nbformat.NotebookNode:
    """
    Finds all import statements in a notebook, consolidates them into a
    single cell at the beginning, and removes them from their original cells.
    """
    collected_imports = set()
    first_code_cell_idx = -1

    for i, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            if first_code_cell_idx == -1:
                first_code_cell_idx = i

            lines = cell.source.split("\n")
            remaining_lines = []
            for line in lines:
                if re.match(r"^\s*(import|from)\s+", line):
                    collected_imports.add(line)
                else:
                    remaining_lines.append(line)

            cell.source = "\n".join(remaining_lines)

    # If imports were found, create a new cell and insert it
    if collected_imports and first_code_cell_idx != -1:
        # Sort imports for consistency
        sorted_imports = sorted(collected_imports)
        imports_cell_source = "\n".join(sorted_imports)
        imports_cell = new_code_cell(source=imports_cell_source)  # type: ignore[no-untyped-call]

        # Insert the new cell at the position of the first code cell
        notebook.cells.insert(first_code_cell_idx, imports_cell)

    # Clean up any cells that are now empty or just whitespace
    notebook.cells = [cell for cell in notebook.cells if cell.source.strip()]

    return notebook


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

    return cast(nbformat.NotebookNode, nb)


def generate_notebook_from_analysis(
    analysis: LectureAnalysis,
    output_path: Path,
    notebook_type: Literal["instructor", "student"],
    min_priority: int = 5,
    provider: str = "google",
    model: str | None = None,
) -> None:
    """
    Generate a complete Jupyter notebook from analysis data.

    Args:
        analysis: The lecture analysis containing sections
        output_path: Path where notebook should be saved
        notebook_type: Type of notebook to generate
        min_priority: Minimum section priority to include (default: 5)
        provider: LLM provider for generation
        model: Model name (uses provider default if None)

    Raises:
        ValueError: If no code sections found or generation fails
    """
    logger.info(f"Generating {notebook_type} notebook: {output_path.name}")
    logger.info(f"  Analysis: {analysis.lecture_title}")
    logger.info(f"  Provider: {provider}, Model: {model or 'default'}")
    logger.info(f"  Min priority: {min_priority}")

    # Get code sections in dependency order
    code_sections = analysis.get_code_sections(min_priority=min_priority)
    ordered_sections = [
        s for s in analysis.get_dependency_order() if s in code_sections
    ]

    if not ordered_sections:
        raise ValueError(
            f"No code sections found with priority >= {min_priority}. "
            f"Try lowering min_priority or check the analysis."
        )

    logger.info(f"  Generating cells for {len(ordered_sections)} sections")

    # Generate cells for each section
    all_cells_text = []

    # Add title cell
    title_cell = f"""# %% [markdown]
# # {analysis.lecture_title}
#
# This notebook contains code-focused examples from the lecture.
# Run each cell in order to explore the concepts.
"""
    all_cells_text.append(title_cell)

    # Generate cells for each section
    for i, section in enumerate(ordered_sections, 1):
        try:
            section_cells = generate_notebook_for_section(
                section=section,
                all_sections=analysis.sections,
                notebook_type=notebook_type,
                provider=provider,
                model=model,
            )
            all_cells_text.append(section_cells)
            logger.info(f"  [{i}/{len(ordered_sections)}] Generated: {section.title}")
        except Exception as e:
            logger.error(f"Failed to generate section '{section.title}': {e}")
            # Continue with other sections
            continue

    # Combine all cells
    complete_notebook_text = "\n\n".join(all_cells_text)

    # Parse into notebook format
    notebook = _parse_llm_response_to_notebook(complete_notebook_text, notebook_type)

    # Consolidate imports for instructor notebooks
    if notebook_type == "instructor":
        logger.info("Consolidating imports for instructor notebook...")
        notebook = _consolidate_imports(notebook)

    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        nbformat.write(notebook, f)  # type: ignore[no-untyped-call]

    logger.info(f"Saved {notebook_type} notebook to: {output_path}")
    logger.info(f"  Total cells: {len(notebook.cells)}")


def load_analysis_from_file(analysis_path: Path) -> LectureAnalysis:
    """
    Load and validate analysis from JSON file.

    Args:
        analysis_path: Path to analysis.json file

    Returns:
        Validated LectureAnalysis object

    Raises:
        FileNotFoundError: If analysis file doesn't exist
        ValueError: If analysis data is invalid
    """
    if not analysis_path.exists():
        raise FileNotFoundError(f"Analysis file not found: {analysis_path}")

    logger.info(f"Loading analysis from: {analysis_path.name}")

    with open(analysis_path) as f:
        data = json.load(f)

    # Validate with Pydantic
    analysis = LectureAnalysis(**data)

    logger.info(f"  Lecture: {analysis.lecture_title}")
    logger.info(f"  Total sections: {len(analysis.sections)}")
    logger.info(f"  Code sections: {len(analysis.get_code_sections())}")

    return analysis
