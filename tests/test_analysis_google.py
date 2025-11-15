from __future__ import annotations

import json
from typing import Any

from PIL import Image

from notebookmaker.analysis import analyze_pdf_chunk
from notebookmaker.llm.models import LLMMessage, LLMResponse, LLMUsage


class _FakeProvider:
    def __init__(self) -> None:
        self.recorded_messages: list[LLMMessage] = []
        self.recorded_model: str | None = None

    def generate(
        self,
        *,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        self.recorded_messages = messages
        self.recorded_model = model
        analysis_payload = {
            "lecture_title": "Test Lecture",
            "sections": [
                {
                    "section_id": "intro",
                    "title": "Intro",
                    "pages": [1],
                    "has_code": True,
                    "code_snippets": [],
                    "equations": [],
                    "concepts": [],
                    "dependencies": [],
                    "priority": 5,
                }
            ],
        }
        return LLMResponse(
            content=json.dumps(analysis_payload),
            model=model,
            usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            metadata={},
        )


def test_analyze_pdf_chunk_google(monkeypatch: Any) -> None:
    fake_provider = _FakeProvider()

    def fake_get_provider(provider: str, api_key: str | None = None) -> _FakeProvider:
        assert provider == "google"
        assert api_key is None
        return fake_provider

    def fake_prompt_fragment(_: str) -> str:
        return "fragment"

    monkeypatch.setattr("notebookmaker.analysis.get_provider", fake_get_provider)
    monkeypatch.setattr(
        "notebookmaker.analysis._load_prompt_fragment", fake_prompt_fragment
    )
    monkeypatch.setattr(
        "notebookmaker.analysis.resize_image_if_needed", lambda img, **_: img
    )

    images = [Image.new("RGB", (32, 32), color="white")]

    result = analyze_pdf_chunk(
        images=images,
        chunk_index=0,
        total_chunks=1,
        provider="google",
        model=None,
    )

    assert result["sections"][0]["section_id"] == "intro"
    assert fake_provider.recorded_model == "gemini-2.0-flash-exp"

    assert fake_provider.recorded_messages, "generate() should receive messages"
    message_content = fake_provider.recorded_messages[0].content
    assert isinstance(message_content, list)
    assert isinstance(message_content[0], str)
    for part in message_content[1:]:
        assert isinstance(part, Image.Image), "Google path should pass PIL images"
