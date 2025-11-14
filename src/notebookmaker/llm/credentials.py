"""Secure credential discovery and management for LLM providers."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class CredentialManager:
    """
    Manages secure credential discovery for LLM providers.

    Security features:
    - Never logs actual API key values (only shows masked versions)
    - Searches multiple sources in priority order
    - Validates key formats before returning
    - Supports reusing existing CLI credentials
    """

    # Security: These patterns are for basic validation only
    # They help catch obvious errors but don't guarantee key validity
    KEY_PATTERNS = {
        "anthropic": lambda k: k.startswith("sk-ant-") and len(k) > 20,
        "openai": lambda k: k.startswith("sk-") and len(k) > 20,
        "openrouter": lambda k: k.startswith("sk-or-") and len(k) > 20,
        "google": lambda k: len(k) > 20,  # Google keys are long alphanumeric strings
    }

    @staticmethod
    def get_anthropic_key() -> str | None:
        """
        Discover Anthropic API key from multiple sources.

        Priority order:
        1. ANTHROPIC_API_KEY environment variable
        2. NOTEBOOKMAKER_ANTHROPIC_KEY environment variable
        3. .env file
        4. None (will require user to provide)

        Returns:
            API key if found, None otherwise
        """
        # 1. Check standard env var (used by Claude CLI)
        if key := os.getenv("ANTHROPIC_API_KEY"):
            logger.info("Found Anthropic API key in ANTHROPIC_API_KEY env var")
            if CredentialManager._validate_key(key, "anthropic"):
                return key

        # 2. Check application-specific env var
        if key := os.getenv("NOTEBOOKMAKER_ANTHROPIC_KEY"):
            logger.info(
                "Found Anthropic API key in NOTEBOOKMAKER_ANTHROPIC_KEY env var"
            )
            if CredentialManager._validate_key(key, "anthropic"):
                return key

        # 3. Check .env file
        if key := CredentialManager._load_from_env_file("ANTHROPIC_API_KEY"):
            logger.info("Found Anthropic API key in .env file")
            if CredentialManager._validate_key(key, "anthropic"):
                return key

        logger.warning("Anthropic API key not found in any source")
        return None

    @staticmethod
    def get_google_key() -> str | None:
        """
        Discover Google API key or credentials.

        Priority order:
        1. GOOGLE_API_KEY environment variable
        2. NOTEBOOKMAKER_GOOGLE_KEY environment variable
        3. Google Cloud Application Default Credentials (ADC)
        4. .env file
        5. None (will require user to provide)

        Returns:
            API key if found, "USE_ADC" for Application Default Credentials,
            or None otherwise
        """
        # 1. Check standard env var
        if key := os.getenv("GOOGLE_API_KEY"):
            logger.info("Found Google API key in GOOGLE_API_KEY env var")
            if CredentialManager._validate_key(key, "google"):
                return key

        # 2. Check application-specific env var
        if key := os.getenv("NOTEBOOKMAKER_GOOGLE_KEY"):
            logger.info("Found Google API key in NOTEBOOKMAKER_GOOGLE_KEY env var")
            if CredentialManager._validate_key(key, "google"):
                return key

        # 3. Check for Application Default Credentials (from gcloud CLI)
        adc_path = (
            Path.home() / ".config/gcloud/application_default_credentials.json"
        )
        if adc_path.exists():
            logger.info(
                "Found Google Application Default Credentials "
                "(from gcloud CLI) - will use ADC"
            )
            return "USE_ADC"

        # 4. Check .env file
        if key := CredentialManager._load_from_env_file("GOOGLE_API_KEY"):
            logger.info("Found Google API key in .env file")
            if CredentialManager._validate_key(key, "google"):
                return key

        logger.warning("Google API key not found in any source")
        return None

    @staticmethod
    def get_openai_key() -> str | None:
        """
        Discover OpenAI API key from multiple sources.

        Priority order:
        1. OPENAI_API_KEY environment variable
        2. NOTEBOOKMAKER_OPENAI_KEY environment variable
        3. .env file
        4. None (will require user to provide)

        Returns:
            API key if found, None otherwise
        """
        # 1. Check standard env var
        if key := os.getenv("OPENAI_API_KEY"):
            logger.info("Found OpenAI API key in OPENAI_API_KEY env var")
            if CredentialManager._validate_key(key, "openai"):
                return key

        # 2. Check application-specific env var
        if key := os.getenv("NOTEBOOKMAKER_OPENAI_KEY"):
            logger.info("Found OpenAI API key in NOTEBOOKMAKER_OPENAI_KEY env var")
            if CredentialManager._validate_key(key, "openai"):
                return key

        # 3. Check .env file
        if key := CredentialManager._load_from_env_file("OPENAI_API_KEY"):
            logger.info("Found OpenAI API key in .env file")
            if CredentialManager._validate_key(key, "openai"):
                return key

        logger.warning("OpenAI API key not found in any source")
        return None

    @staticmethod
    def get_openrouter_key() -> str | None:
        """
        Discover OpenRouter API key from multiple sources.

        Priority order:
        1. OPENROUTER_API_KEY environment variable
        2. NOTEBOOKMAKER_OPENROUTER_KEY environment variable
        3. .env file
        4. None (will require user to provide)

        Returns:
            API key if found, None otherwise
        """
        # 1. Check standard env var
        if key := os.getenv("OPENROUTER_API_KEY"):
            logger.info("Found OpenRouter API key in OPENROUTER_API_KEY env var")
            if CredentialManager._validate_key(key, "openrouter"):
                return key

        # 2. Check application-specific env var
        if key := os.getenv("NOTEBOOKMAKER_OPENROUTER_KEY"):
            logger.info(
                "Found OpenRouter API key in NOTEBOOKMAKER_OPENROUTER_KEY env var"
            )
            if CredentialManager._validate_key(key, "openrouter"):
                return key

        # 3. Check .env file
        if key := CredentialManager._load_from_env_file("OPENROUTER_API_KEY"):
            logger.info("Found OpenRouter API key in .env file")
            if CredentialManager._validate_key(key, "openrouter"):
                return key

        logger.warning("OpenRouter API key not found in any source")
        return None

    @staticmethod
    def _load_from_env_file(key_name: str) -> str | None:
        """
        Load a key from .env file if it exists.

        Args:
            key_name: The name of the environment variable to load

        Returns:
            The key value if found and non-empty, None otherwise
        """
        env_file = Path.cwd() / ".env"
        if not env_file.exists():
            return None

        try:
            # Use python-dotenv for secure loading
            from dotenv import dotenv_values

            config = dotenv_values(env_file)
            value = config.get(key_name)

            # Return None if the value is empty or just whitespace
            if value and value.strip():
                return value.strip()

        except ImportError:
            logger.warning(
                "python-dotenv not installed, skipping .env file. "
                "Install with: pip install python-dotenv"
            )
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")

        return None

    @staticmethod
    def _validate_key(key: str, provider: str) -> bool:
        """
        Validate API key format (basic sanity check).

        Security note: This is NOT a security check. It only validates
        that the key matches expected patterns to catch obvious errors.

        Args:
            key: The API key to validate
            provider: The provider name (for pattern matching)

        Returns:
            True if key appears valid, False otherwise
        """
        if not key or not key.strip():
            logger.warning(f"Empty or whitespace-only key for {provider}")
            return False

        validator = CredentialManager.KEY_PATTERNS.get(provider)
        if not validator:
            logger.warning(f"No validation pattern for provider: {provider}")
            return True  # Unknown provider, assume valid

        is_valid = validator(key)  # type: ignore
        if not is_valid:
            # Security: Never log the actual key, only show masked version
            masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
            logger.warning(
                f"API key format appears invalid for {provider}: {masked_key}"
            )

        return is_valid

    @staticmethod
    def mask_key(key: str) -> str:
        """
        Mask an API key for safe logging/display.

        Args:
            key: The API key to mask

        Returns:
            Masked version showing only first 8 and last 4 characters
        """
        if not key or len(key) < 12:
            return "***"
        return f"{key[:8]}...{key[-4:]}"
