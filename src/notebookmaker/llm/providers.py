"""LLM provider implementations with credential auto-discovery."""

import logging
from abc import ABC, abstractmethod

from .credentials import CredentialManager
from .models import LLMMessage, LLMResponse, LLMUsage

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Base class for all LLM providers.

    Provides common interface and credential discovery logic.
    Subclasses must implement provider-specific generation logic.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize LLM provider with optional API key.

        If api_key is not provided, will attempt to auto-discover
        credentials from environment variables, CLI configs, and .env file.

        Args:
            api_key: Optional API key. If None, will auto-discover.

        Raises:
            ValueError: If no API key can be found or discovered.
        """
        if api_key:
            logger.info(f"Using provided API key for {self.__class__.__name__}")
            self.api_key = api_key
        else:
            logger.info(
                f"Auto-discovering credentials for {self.__class__.__name__}"
            )
            discovered_key = self._discover_credentials()
            if not discovered_key:
                raise ValueError(
                    f"No API key found for {self.__class__.__name__}. "
                    f"Set environment variable, add to .env file, "
                    f"or pass api_key parameter."
                )
            self.api_key = discovered_key

        # Security: Log only masked version
        masked = CredentialManager.mask_key(self.api_key)
        logger.info(f"{self.__class__.__name__} initialized with key: {masked}")

    @abstractmethod
    def _discover_credentials(self) -> str | None:
        """
        Discover credentials for this provider.

        Returns:
            API key if found, None otherwise
        """
        pass

    @abstractmethod
    def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate completion from messages.

        Args:
            messages: List of conversation messages
            model: Model identifier to use
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Standardized LLM response

        Raises:
            Exception: Provider-specific errors during generation
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens for cost estimation.

        Args:
            text: Text to count tokens for
            model: Model to use for tokenization

        Returns:
            Number of tokens
        """
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider with credential auto-discovery."""

    def _discover_credentials(self) -> str | None:
        """Discover Anthropic API key from environment or .env file."""
        return CredentialManager.get_anthropic_key()

    def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate completion using Anthropic Claude API.

        Args:
            messages: List of conversation messages
            model: Claude model identifier (e.g., 'claude-sonnet-4-5-20250929')
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate (default: 4096)

        Returns:
            Standardized LLM response
        """
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            ) from e

        client = Anthropic(api_key=self.api_key)

        # Convert our standard format to Anthropic format
        # Anthropic expects system messages separate from conversation
        system_messages = [m for m in messages if m.role == "system"]
        conversation_messages = [m for m in messages if m.role != "system"]

        # Build system prompt
        system_prompt = "\n\n".join(m.content for m in system_messages)

        # Build conversation
        anthropic_messages = [
            {"role": m.role, "content": m.content} for m in conversation_messages
        ]

        # Make API call
        logger.info(
            f"Calling Anthropic API with model={model}, "
            f"temperature={temperature}, max_tokens={max_tokens}"
        )

        # Create message with proper typing
        create_params: dict[str, object] = {
            "model": model,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
            "messages": anthropic_messages,
        }
        if system_prompt:
            create_params["system"] = system_prompt

        response = client.messages.create(**create_params)  # type: ignore

        # Extract content (handle both string and content blocks)
        content = ""
        if hasattr(response.content, "__iter__") and not isinstance(
            response.content, str
        ):
            # Content is a list of content blocks
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text
        else:
            content = str(response.content)

        # Build standardized response
        return LLMResponse(
            content=content,
            model=response.model,
            usage=LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens
                + response.usage.output_tokens,
            ),
            metadata={
                "id": response.id,
                "stop_reason": response.stop_reason,
                "type": response.type,
            },
        )

    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens using rough estimation.

        Note: Anthropic SDK doesn't provide a token counting API.
        This uses a rough estimation of 4 characters per token.

        Args:
            text: Text to count tokens for
            model: Model to use for tokenization

        Returns:
            Approximate number of tokens
        """
        # Anthropic doesn't provide a token counting API
        # Use rough estimation: ~4 characters per token
        logger.warning("Using rough token estimation (4 chars per token)")
        return len(text) // 4


class GoogleProvider(LLMProvider):
    """Google Gemini provider with ADC support."""

    def _discover_credentials(self) -> str | None:
        """
        Discover Google API key or Application Default Credentials.

        Returns:
            API key or "USE_ADC" to use Application Default Credentials
        """
        return CredentialManager.get_google_key()

    def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate completion using Google Gemini API.

        Args:
            messages: List of conversation messages
            model: Gemini model identifier (e.g., 'gemini-2.0-flash-exp')
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Standardized LLM response
        """
        try:
            import google.generativeai as genai
        except ImportError as e:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            ) from e

        # Configure API key or use ADC
        if self.api_key == "USE_ADC":
            logger.info("Using Google Application Default Credentials")
            # ADC is automatically used when no API key is set
            # This works if user ran: gcloud auth application-default login
            genai.configure()  # type: ignore
        else:
            genai.configure(api_key=self.api_key)  # type: ignore

        # Convert our messages to Gemini format
        # Gemini uses "user" and "model" roles (not "assistant")
        gemini_messages = []
        system_instructions = []

        for msg in messages:
            if msg.role == "system":
                system_instructions.append(msg.content)
            elif msg.role == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg.content]})
            else:  # user
                gemini_messages.append({"role": msg.role, "parts": [msg.content]})

        # Create model with configuration
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Add system instructions if present
        model_kwargs: dict[str, object] = {"model_name": model}
        if system_instructions:
            model_kwargs["system_instruction"] = "\n\n".join(system_instructions)

        gemini_model = genai.GenerativeModel(**model_kwargs)  # type: ignore

        # Generate
        logger.info(
            f"Calling Google Gemini API with model={model}, "
            f"temperature={temperature}, max_tokens={max_tokens}"
        )

        response = gemini_model.generate_content(
            gemini_messages, generation_config=generation_config  # type: ignore
        )

        # Extract usage info (if available)
        prompt_tokens = (
            response.usage_metadata.prompt_token_count
            if hasattr(response, "usage_metadata")
            else 0
        )
        completion_tokens = (
            response.usage_metadata.candidates_token_count
            if hasattr(response, "usage_metadata")
            else 0
        )

        return LLMResponse(
            content=response.text,
            model=model,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            metadata={
                "finish_reason": (
                    response.candidates[0].finish_reason.name
                    if response.candidates
                    else None
                ),
            },
        )

    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens using Google's token counting.

        Args:
            text: Text to count tokens for
            model: Model to use for tokenization

        Returns:
            Number of tokens
        """
        try:
            import google.generativeai as genai
        except ImportError:
            # Fallback estimation
            logger.warning("google-generativeai not installed, using estimation")
            return len(text) // 4

        if self.api_key == "USE_ADC":
            genai.configure()  # type: ignore
        else:
            genai.configure(api_key=self.api_key)  # type: ignore

        gemini_model = genai.GenerativeModel(model_name=model)  # type: ignore
        return gemini_model.count_tokens(text).total_tokens


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def _discover_credentials(self) -> str | None:
        """Discover OpenAI API key."""
        return CredentialManager.get_openai_key()

    def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate completion using OpenAI API.

        Args:
            messages: List of conversation messages
            model: OpenAI model identifier (e.g., 'gpt-4o')
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Standardized LLM response
        """
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            ) from e

        client = OpenAI(api_key=self.api_key)

        # Convert to OpenAI format
        openai_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        logger.info(
            f"Calling OpenAI API with model={model}, "
            f"temperature={temperature}, max_tokens={max_tokens}"
        )

        response = client.chat.completions.create(
            model=model,
            messages=openai_messages,  # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract usage info with fallback
        usage = response.usage
        if usage is None:
            usage_info = LLMUsage(
                prompt_tokens=0, completion_tokens=0, total_tokens=0
            )
        else:
            usage_info = LLMUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage=usage_info,
            metadata={
                "id": response.id,
                "finish_reason": response.choices[0].finish_reason,
            },
        )

    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens using tiktoken.

        Args:
            text: Text to count tokens for
            model: Model to use for tokenization

        Returns:
            Number of tokens
        """
        try:
            import tiktoken
        except ImportError:
            logger.warning("tiktoken not installed, using rough estimation")
            return len(text) // 4

        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Model not found, use default encoding
            encoding = tiktoken.get_encoding("cl100k_base")

        return len(encoding.encode(text))


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider (uses OpenAI-compatible API)."""

    def _discover_credentials(self) -> str | None:
        """Discover OpenRouter API key."""
        return CredentialManager.get_openrouter_key()

    def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate completion using OpenRouter API.

        Args:
            messages: List of conversation messages
            model: Model identifier (e.g., 'anthropic/claude-sonnet-4')
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Standardized LLM response
        """
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            ) from e

        # OpenRouter uses OpenAI-compatible API with custom base URL
        client = OpenAI(
            api_key=self.api_key, base_url="https://openrouter.ai/api/v1"
        )

        # Convert to OpenAI format
        openai_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        logger.info(
            f"Calling OpenRouter API with model={model}, "
            f"temperature={temperature}, max_tokens={max_tokens}"
        )

        response = client.chat.completions.create(
            model=model,
            messages=openai_messages,  # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract usage info with fallback
        usage = response.usage
        if usage is None:
            usage_info = LLMUsage(
                prompt_tokens=0, completion_tokens=0, total_tokens=0
            )
        else:
            usage_info = LLMUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage=usage_info,
            metadata={
                "id": response.id,
                "finish_reason": response.choices[0].finish_reason,
            },
        )

    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens (rough estimation for OpenRouter).

        Args:
            text: Text to count tokens for
            model: Model to use for tokenization

        Returns:
            Approximate number of tokens
        """
        # OpenRouter doesn't provide token counting
        # Use rough estimation
        logger.warning("OpenRouter doesn't provide token counting, using estimation")
        return len(text) // 4
