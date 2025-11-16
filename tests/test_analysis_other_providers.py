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
        return LLMResponse(
            content=json.dumps(
                {
                    "lecture_title": "Test",
                    "sections": [],
                }
            ),
            model=model,
            usage=LLMUsage(prompt_tokens=5, completion_tokens=5, total_tokens=10),
            metadata={},
        )


def test_analyze_pdf_chunk_anthropic(monkeypatch: Any) -> None:
    fake_provider = _FakeProvider()

    def fake_get_provider(provider: str, api_key: str | None = None) -> _FakeProvider:
        assert provider == "anthropic"
        assert api_key is None
        return fake_provider

    monkeypatch.setattr("notebookmaker.analysis.get_provider", fake_get_provider)
    monkeypatch.setattr(
        "notebookmaker.analysis._load_prompt_fragment", lambda _: "fragment"
    )
    monkeypatch.setattr(
        "notebookmaker.analysis.resize_image_if_needed", lambda img, **_: img
    )

    captured_images: list[Image.Image] = []

    def fake_encode_image_base64(image: Image.Image, format: str = "PNG") -> str:
        captured_images.append(image)
        return "YmFzZTY0"

    monkeypatch.setattr(
        "notebookmaker.analysis.encode_image_base64", fake_encode_image_base64
    )

    images = [Image.new("RGB", (16, 16), color="white")]

    analyze_pdf_chunk(
        images=images,
        chunk_index=0,
        total_chunks=1,
        provider="anthropic",
        model=None,
    )

    assert fake_provider.recorded_model == "claude-3-5-sonnet-20241022"
    assert captured_images, "encode_image_base64 should be called"

    assert fake_provider.recorded_messages
    payload = fake_provider.recorded_messages[0].content
    assert isinstance(payload, list)
    assert payload[0]["type"] == "text"
    assert payload[1]["type"] == "image"
    assert payload[1]["source"]["data"] == "YmFzZTY0"


def test_analyze_pdf_chunk_openai(monkeypatch: Any) -> None:
    fake_provider = _FakeProvider()

    def fake_get_provider(provider: str, api_key: str | None = None) -> _FakeProvider:
        assert provider == "openai"
        return fake_provider

    monkeypatch.setattr("notebookmaker.analysis.get_provider", fake_get_provider)
    monkeypatch.setattr(
        "notebookmaker.analysis._load_prompt_fragment", lambda _: "fragment"
    )
    monkeypatch.setattr(
        "notebookmaker.analysis.resize_image_if_needed", lambda img, **_: img
    )

    def fake_encode_image_base64(image: Image.Image, format: str = "PNG") -> str:
        return "ZmFrZS1kYXRh"

    monkeypatch.setattr(
        "notebookmaker.analysis.encode_image_base64", fake_encode_image_base64
    )

    images = [Image.new("RGB", (8, 8), color="white")]

    analyze_pdf_chunk(
        images=images,
        chunk_index=1,
        total_chunks=2,
        provider="openai",
        model=None,
    )

    assert fake_provider.recorded_model == "gpt-4o"
    content = fake_provider.recorded_messages[0].content
    assert isinstance(content, list)
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
