"""Data models for NotebookMaker analysis and generation phases."""

from typing import Any

from pydantic import BaseModel, Field


class CodeSnippet(BaseModel):
    """A code snippet extracted from lecture materials."""

    code: str = Field(description="The complete code snippet")
    language: str = Field(
        default="python", description="Programming language (default: python)"
    )
    line_number: int | None = Field(
        default=None, description="Approximate line/position in source material"
    )


class Equation(BaseModel):
    """A mathematical equation in LaTeX format."""

    latex: str = Field(description="LaTeX representation of the equation")
    description: str | None = Field(
        default=None, description="Brief description of what the equation represents"
    )


class Section(BaseModel):
    """A section of lecture content identified in Phase 1 analysis."""

    section_id: str = Field(
        description="Unique identifier for this section (snake_case)"
    )
    title: str = Field(description="Human-readable section title")
    pages: list[int] = Field(
        description="Page numbers where this section appears (1-indexed)"
    )
    has_code: bool = Field(
        description="True if section contains executable code examples"
    )
    code_snippets: list[CodeSnippet] = Field(
        default_factory=list, description="Code snippets found in this section"
    )
    equations: list[Equation] = Field(
        default_factory=list,
        description="Mathematical equations found in this section (LaTeX)",
    )
    concepts: list[str] = Field(
        default_factory=list,
        description="Key concepts covered (for context, not for narrative)",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Section IDs that should come before this section",
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Priority for inclusion (1=low, 10=critical). "
        "Higher for core concepts with executable code.",
    )


class LectureAnalysis(BaseModel):
    """Complete analysis output from Phase 1 (vision LLM processing)."""

    lecture_title: str = Field(description="Title of the lecture")
    total_pages: int = Field(description="Total number of pages processed")
    sections: list[Section] = Field(
        description="All sections identified in the lecture"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (author, date, course, etc.)",
    )

    def get_code_sections(self, min_priority: int = 5) -> list[Section]:
        """
        Get sections that have executable code and meet minimum priority.

        Args:
            min_priority: Minimum priority threshold (1-10, default 5)

        Returns:
            List of sections sorted by page order, filtered for code-heavy content
        """
        code_sections = [
            section
            for section in self.sections
            if section.has_code and section.priority >= min_priority
        ]
        # Sort by first page number for logical flow
        return sorted(code_sections, key=lambda s: s.pages[0] if s.pages else 0)

    def get_dependency_order(self) -> list[Section]:
        """
        Get code sections in dependency-respecting order.

        Returns:
            List of sections ordered to respect dependencies
        """
        code_sections = self.get_code_sections()
        section_dict = {s.section_id: s for s in code_sections}

        # Topological sort based on dependencies
        ordered: list[Section] = []
        visited: set[str] = set()

        def visit(section_id: str) -> None:
            if section_id in visited or section_id not in section_dict:
                return
            visited.add(section_id)

            section = section_dict[section_id]
            # Visit dependencies first
            for dep_id in section.dependencies:
                visit(dep_id)

            ordered.append(section)

        # Visit all sections
        for section in code_sections:
            visit(section.section_id)

        return ordered
