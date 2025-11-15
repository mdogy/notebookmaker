from __future__ import annotations

from pathlib import Path

import pytest

from notebookmaker.generation import generate_notebook_from_analysis
from notebookmaker.models import CodeSnippet, LectureAnalysis, Section


def _sample_analysis() -> LectureAnalysis:
    section = Section(
        section_id="intro",
        title="Intro",
        pages=[1],
        has_code=True,
        code_snippets=[CodeSnippet(code="print('hi')", language="python", line_number=1)],
        equations=[],
        concepts=[],
        dependencies=[],
        priority=5,
    )
    return LectureAnalysis(
        lecture_title="Sample Lecture",
        total_pages=1,
        sections=[section],
        metadata={},
    )


def test_generate_notebook_raises_when_no_sections_succeed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    analysis = _sample_analysis()
    output_path = tmp_path / "sample.ipynb"

    def fake_generate_notebook_for_section(*_: object, **__: object) -> str:
        raise RuntimeError("LLM failure")

    monkeypatch.setattr(
        "notebookmaker.generation.generate_notebook_for_section",
        fake_generate_notebook_for_section,
        raising=True,
    )

    with pytest.raises(ValueError, match="Failed to generate any sections"):
        generate_notebook_from_analysis(
            analysis=analysis,
            output_path=output_path,
            notebook_type="instructor",
            min_priority=5,
            provider="google",
            model=None,
        )

    assert not output_path.exists()
