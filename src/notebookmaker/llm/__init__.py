"""LLM integration layer with secure credential management."""

from typing import Literal

from .credentials import CredentialManager
from .models import LLMConfig, LLMMessage, LLMResponse, LLMUsage, ProviderConfig
from .providers import (
    AnthropicProvider,
    GoogleProvider,
    LLMProvider,
    OpenAIProvider,
    OpenRouterProvider,
)

__all__ = [
    # Main factory function
    "get_provider",
    # Models
    "LLMConfig",
    "LLMMessage",
    "LLMResponse",
    "LLMUsage",
    "ProviderConfig",
    # Provider classes
    "LLMProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    # Credential management
    "CredentialManager",
]


def get_provider(
    provider: Literal["anthropic", "google", "openai", "openrouter"],
    api_key: str | None = None,
) -> LLMProvider:
    """
    Factory function to get an LLM provider instance.

    This is the primary way to create provider instances. It handles
    credential discovery automatically if no API key is provided.

    Args:
        provider: The provider to use ('anthropic', 'google', 'openai', 'openrouter')
        api_key: Optional API key. If None, will auto-discover from:
            - Environment variables
            - CLI credential files (Google Cloud, etc.)
            - .env file

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider is unknown or credentials cannot be found

    Examples:
        >>> # Auto-discover credentials
        >>> provider = get_provider("anthropic")
        >>> response = provider.generate(
        ...     messages=[LLMMessage(role="user", content="Hello!")],
        ...     model="claude-sonnet-4-5-20250929"
        ... )

        >>> # Explicit API key
        >>> provider = get_provider("google", api_key="your-api-key")

        >>> # Use with Google Cloud ADC
        >>> # First run: gcloud auth application-default login
        >>> provider = get_provider("google")
    """
    providers: dict[str, type[LLMProvider]] = {
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
    }

    provider_class = providers.get(provider)
    if provider_class is None:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Available providers: {', '.join(providers.keys())}"
        )

    return provider_class(api_key=api_key)
