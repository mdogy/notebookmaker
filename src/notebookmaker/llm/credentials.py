"""Secure credential discovery and management for LLM providers."""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

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

    # Cache for the loaded config to avoid reading file multiple times
    _config_cache: dict[str, Any] | None = None

    @staticmethod
    def _load_config() -> dict[str, Any]:
        """
        Load configuration from ~/.notebookmaker_config.yaml.

        Returns:
            Dictionary with configuration values, or empty dict if file doesn't exist
        """
        if CredentialManager._config_cache is not None:
            return CredentialManager._config_cache

        config_path = Path.home() / ".notebookmaker_config.yaml"
        if not config_path.exists():
            logger.info(
                f"Config file not found at {config_path}. "
                "Will fall back to environment variables only."
            )
            CredentialManager._config_cache = {}
            return CredentialManager._config_cache

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
                CredentialManager._config_cache = config
                logger.info(f"Loaded configuration from {config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            CredentialManager._config_cache = {}
            return CredentialManager._config_cache

    @staticmethod
    def get_anthropic_key() -> str | None:
        """
        Discover Anthropic API key from multiple sources.

        Priority order:
        1. ~/.notebookmaker_config.yaml file
        2. ANTHROPIC_API_KEY environment variable
        3. NOTEBOOKMAKER_ANTHROPIC_KEY environment variable
        4. None (will require user to provide)

        Returns:
            API key if found, None otherwise
        """
        # 1. Check config file first (highest priority)
        config = CredentialManager._load_config()
        if key := config.get("anthropic_api_key"):
            # Skip placeholder values from example file
            if isinstance(key, str) and key != "your-anthropic-key-here":
                logger.info("Found Anthropic API key in ~/.notebookmaker_config.yaml")
                if CredentialManager._validate_key(key, "anthropic"):
                    return key

        # 2. Check standard env var (used by Claude CLI)
        if key := os.getenv("ANTHROPIC_API_KEY"):
            logger.info("Found Anthropic API key in ANTHROPIC_API_KEY env var")
            if CredentialManager._validate_key(key, "anthropic"):
                return key

        # 3. Check application-specific env var
        if key := os.getenv("NOTEBOOKMAKER_ANTHROPIC_KEY"):
            logger.info(
                "Found Anthropic API key in NOTEBOOKMAKER_ANTHROPIC_KEY env var"
            )
            if CredentialManager._validate_key(key, "anthropic"):
                return key

        logger.warning("Anthropic API key not found in any source")
        return None

    @staticmethod
    def get_google_key() -> str | None:
        """
        Discover Google API key or credentials.

        Priority order:
        1. ~/.notebookmaker_config.yaml file
        2. GOOGLE_API_KEY environment variable
        3. NOTEBOOKMAKER_GOOGLE_KEY environment variable
        4. Google Cloud Application Default Credentials (ADC)
        5. None (will require user to provide)

        Returns:
            API key if found, "USE_ADC" for Application Default Credentials,
            or None otherwise
        """
        # 1. Check config file first (highest priority)
        config = CredentialManager._load_config()
        if key := config.get("google_api_key"):
            # Skip placeholder values from example file
            if isinstance(key, str) and key != "your-google-key-here":
                logger.info("Found Google API key in ~/.notebookmaker_config.yaml")
                if CredentialManager._validate_key(key, "google"):
                    return key

        # 2. Check standard env var
        if key := os.getenv("GOOGLE_API_KEY"):
            logger.info("Found Google API key in GOOGLE_API_KEY env var")
            if CredentialManager._validate_key(key, "google"):
                return key

        # 3. Check application-specific env var
        if key := os.getenv("NOTEBOOKMAKER_GOOGLE_KEY"):
            logger.info("Found Google API key in NOTEBOOKMAKER_GOOGLE_KEY env var")
            if CredentialManager._validate_key(key, "google"):
                return key

        # 4. Check for Application Default Credentials (from gcloud CLI)
        adc_path = (
            Path.home() / ".config/gcloud/application_default_credentials.json"
        )
        if adc_path.exists():
            logger.info(
                "Found Google Application Default Credentials "
                "(from gcloud CLI) - will use ADC"
            )
            return "USE_ADC"

        logger.warning("Google API key not found in any source")
        return None

    @staticmethod
    def get_openai_key() -> str | None:
        """
        Discover OpenAI API key from multiple sources.

        Priority order:
        1. ~/.notebookmaker_config.yaml file
        2. OPENAI_API_KEY environment variable
        3. NOTEBOOKMAKER_OPENAI_KEY environment variable
        4. None (will require user to provide)

        Returns:
            API key if found, None otherwise
        """
        # 1. Check config file first (highest priority)
        config = CredentialManager._load_config()
        if key := config.get("openai_api_key"):
            # Skip placeholder values from example file
            if isinstance(key, str) and key != "your-openai-key-here":
                logger.info("Found OpenAI API key in ~/.notebookmaker_config.yaml")
                if CredentialManager._validate_key(key, "openai"):
                    return key

        # 2. Check standard env var
        if key := os.getenv("OPENAI_API_KEY"):
            logger.info("Found OpenAI API key in OPENAI_API_KEY env var")
            if CredentialManager._validate_key(key, "openai"):
                return key

        # 3. Check application-specific env var
        if key := os.getenv("NOTEBOOKMAKER_OPENAI_KEY"):
            logger.info("Found OpenAI API key in NOTEBOOKMAKER_OPENAI_KEY env var")
            if CredentialManager._validate_key(key, "openai"):
                return key

        logger.warning("OpenAI API key not found in any source")
        return None

    @staticmethod
    def get_openrouter_key() -> str | None:
        """
        Discover OpenRouter API key from multiple sources.

        Priority order:
        1. ~/.notebookmaker_config.yaml file
        2. OPENROUTER_API_KEY environment variable
        3. NOTEBOOKMAKER_OPENROUTER_KEY environment variable
        4. None (will require user to provide)

        Returns:
            API key if found, None otherwise
        """
        # 1. Check config file first (highest priority)
        config = CredentialManager._load_config()
        if key := config.get("openrouter_api_key"):
            # Skip placeholder values from example file
            if isinstance(key, str) and key != "your-openrouter-key-here":
                logger.info("Found OpenRouter API key in ~/.notebookmaker_config.yaml")
                if CredentialManager._validate_key(key, "openrouter"):
                    return key

        # 2. Check standard env var
        if key := os.getenv("OPENROUTER_API_KEY"):
            logger.info("Found OpenRouter API key in OPENROUTER_API_KEY env var")
            if CredentialManager._validate_key(key, "openrouter"):
                return key

        # 3. Check application-specific env var
        if key := os.getenv("NOTEBOOKMAKER_OPENROUTER_KEY"):
            logger.info(
                "Found OpenRouter API key in NOTEBOOKMAKER_OPENROUTER_KEY env var"
            )
            if CredentialManager._validate_key(key, "openrouter"):
                return key

        logger.warning("OpenRouter API key not found in any source")
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
    def get_analysis_config() -> dict[str, Any]:
        """
        Get analysis phase LLM configuration from config file.

        Returns:
            Dictionary with analysis config (provider, model, max_tokens, etc.)
            or empty dict if not configured. Falls back to 'llm' config if
            'analysis' is not specified.
        """
        config = CredentialManager._load_config()

        # Check for two-phase config first
        if "analysis" in config and isinstance(config["analysis"], dict):
            return config["analysis"]

        # Fall back to single-phase 'llm' config
        if "llm" in config and isinstance(config["llm"], dict):
            return config["llm"]

        return {}

    @staticmethod
    def get_generation_config() -> dict[str, Any]:
        """
        Get generation phase LLM configuration from config file.

        Returns:
            Dictionary with generation config (provider, model, max_tokens, etc.)
            or empty dict if not configured. Falls back to 'llm' config if
            'generation' is not specified.
        """
        config = CredentialManager._load_config()

        # Check for two-phase config first
        if "generation" in config and isinstance(config["generation"], dict):
            return config["generation"]

        # Fall back to single-phase 'llm' config
        if "llm" in config and isinstance(config["llm"], dict):
            return config["llm"]

        return {}

    @staticmethod
    def get_llm_config() -> dict[str, Any]:
        """
        Get LLM configuration from config file (legacy single-phase mode).

        Returns:
            Dictionary with LLM config (provider, model, max_tokens, temperature, etc.)
            or empty dict if not configured
        """
        config = CredentialManager._load_config()
        llm_config = config.get("llm", {})
        if isinstance(llm_config, dict):
            return llm_config
        return {}

    @staticmethod
    def get_logging_config() -> dict[str, Any]:
        """
        Get logging configuration from config file.

        Returns:
            Dictionary with logging config (level, log_llm_details)
            or empty dict if not configured
        """
        config = CredentialManager._load_config()
        logging_config = config.get("logging", {})
        if isinstance(logging_config, dict):
            return logging_config
        return {}

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
