"""Pydantic models for LLM integration."""

from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr


class LLMMessage(BaseModel):
    """Standardized message format for LLM interactions."""

    role: Literal["system", "user", "assistant"] = Field(
        description="The role of the message sender"
    )
    content: str = Field(description="The content of the message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "user",
                    "content": "Extract topics from the following lecture...",
                }
            ]
        }
    }


class LLMUsage(BaseModel):
    """Token usage information from LLM response."""

    prompt_tokens: int = Field(ge=0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(
        ge=0, description="Number of tokens in the completion"
    )
    total_tokens: int = Field(ge=0, description="Total number of tokens used")


class LLMResponse(BaseModel):
    """Standardized response format from LLM providers."""

    content: str = Field(description="The generated text content")
    model: str = Field(description="The model used to generate the response")
    usage: LLMUsage = Field(description="Token usage information")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional provider-specific metadata"
    )


class LLMConfig(BaseModel):
    """Configuration for LLM provider and generation parameters."""

    provider: Literal["anthropic", "google", "openai", "openrouter"] = Field(
        description="The LLM provider to use"
    )
    model: str = Field(description="The specific model to use")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature (0.0 to 2.0)"
    )
    max_tokens: int | None = Field(
        default=None, gt=0, description="Maximum tokens to generate"
    )
    api_key: SecretStr | None = Field(
        default=None, description="API key (will be auto-discovered if not provided)"
    )

    model_config = {
        # Prevent API keys from being exposed in logs/prints
        "json_encoders": {SecretStr: lambda v: "***" if v else None}
    }


class ProviderConfig(BaseModel):
    """Configuration specific to a provider."""

    default_model: str = Field(description="Default model for this provider")
    api_key: SecretStr | None = Field(
        default=None, description="API key for this provider"
    )
    additional_params: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific parameters"
    )

    model_config = {
        "json_encoders": {SecretStr: lambda v: "***" if v else None}
    }
