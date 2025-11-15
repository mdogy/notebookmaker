from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from notebookmaker.models import LectureAnalysis
from notebookmaker.utils import process_lecture


@pytest.fixture()
def sample_analysis(tmp_path: Path) -> Path:
    analysis_path = tmp_path / "lecture.analysis.json"
    analysis_payload = {
        "lecture_title": "Sample Lecture",
        "total_pages": 1,
        "sections": [
            {
                "section_id": "intro",
                "title": "Intro",
                "pages": [1],
                "has_code": True,
                "code_snippets": [
                    {"code": "print('hi')", "language": "python", "line_number": 1}
                ],
                "equations": [],
                "concepts": [],
                "dependencies": [],
                "priority": 5,
            }
        ],
        "metadata": {},
    }
    analysis_path.write_text(json.dumps(analysis_payload))
    return analysis_path


def test_process_lecture_defaults_to_google(
    tmp_path: Path, sample_analysis: Path, monkeypatch: Any
) -> None:
    input_file = tmp_path / "lecture.pdf"
    input_file.write_text("%PDF-1.4")

    output_dir = tmp_path / "outputs"

    generate_calls: list[dict[str, Any]] = []

    def fake_load_analysis_from_file(path: Path) -> LectureAnalysis:
        assert path == sample_analysis
        data = json.loads(sample_analysis.read_text())
        return LectureAnalysis(**data)

    def fake_generate_notebook_from_analysis(
        *,
        analysis: LectureAnalysis,
        output_path: Path,
        notebook_type: str,
        min_priority: int,
        provider: str,
        model: str | None,
    ) -> None:
        generate_calls.append(
            {
                "notebook_type": notebook_type,
                "provider": provider,
                "model": model,
                "min_priority": min_priority,
            }
        )
        output_path.write_text("{}")

    monkeypatch.setattr(
        "notebookmaker.generation.load_analysis_from_file",
        fake_load_analysis_from_file,
        raising=True,
    )
    monkeypatch.setattr(
        "notebookmaker.generation.generate_notebook_from_analysis",
        fake_generate_notebook_from_analysis,
        raising=True,
    )

    result = process_lecture(
        input_file=input_file,
        output_dir=output_dir,
        analysis_provider="google",
        generation_provider=None,
        analysis_model=None,
        generation_model=None,
        min_priority=5,
        chunk_size=10,
    )

    assert result["analysis"] == sample_analysis
    assert (output_dir / "lecture_instructor.ipynb").exists()
    assert (output_dir / "lecture_student.ipynb").exists()

    assert [call["provider"] for call in generate_calls] == [
        "google",
        "google",
    ], "Generation should default to Google when provider is omitted"
