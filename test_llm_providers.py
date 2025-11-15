#!/usr/bin/env python3
"""
Test script to verify LLM provider implementations.

This script tests that the credential discovery and API integration
works correctly with real API calls.

Usage:
    python test_llm_providers.py [provider]

    provider: anthropic, google, or openai (default: all available)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from notebookmaker.llm import get_provider, LLMMessage


def test_provider(provider_name: str) -> bool:
    """Test a single provider with a simple API call."""
    print(f"\n{'='*60}")
    print(f"Testing {provider_name.upper()} Provider")
    print(f"{'='*60}")

    try:
        # Try to get provider (will auto-discover credentials)
        print(f"1. Auto-discovering credentials for {provider_name}...")
        provider = get_provider(provider_name)
        print(f"   ✓ Credentials found and provider initialized")

        # Choose appropriate model
        models = {
            "anthropic": "claude-sonnet-4-5-20250929",
            "google": "gemini-2.0-flash-exp",
            "openai": "gpt-4o-mini",  # Use mini for testing (cheaper)
            "openrouter": "anthropic/claude-sonnet-4",
        }
        model = models.get(provider_name, "default")

        # Make a simple API call
        print(f"2. Making test API call with model: {model}...")
        test_prompt = "Say 'Hello from {}!' and nothing else.".format(
            provider_name.upper()
        )

        response = provider.generate(
            messages=[LLMMessage(role="user", content=test_prompt)],
            model=model,
            temperature=0.0,
            max_tokens=50,
        )

        print(f"   ✓ API call successful!")
        print(f"\n   Response: {response.content}")
        print(f"   Model used: {response.model}")
        print(
            f"   Tokens: {response.usage.prompt_tokens} prompt + "
            f"{response.usage.completion_tokens} completion = "
            f"{response.usage.total_tokens} total"
        )

        # Test token counting
        print(f"\n3. Testing token counting...")
        test_text = "This is a test sentence for token counting."
        token_count = provider.count_tokens(test_text, model)
        print(f"   ✓ Token count for test text: {token_count} tokens")

        print(f"\n✅ {provider_name.upper()} provider: ALL TESTS PASSED")
        return True

    except ValueError as e:
        print(f"   ✗ Credentials not found: {e}")
        print(f"\n⚠️  {provider_name.upper()} provider: SKIPPED (no credentials)")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print(f"\n❌ {provider_name.upper()} provider: FAILED")
        import traceback

        traceback.print_exc()
        return False


def main() -> None:
    """Run tests for specified or all providers."""
    print("LLM Provider Integration Test")
    print("=" * 60)

    # Determine which providers to test
    if len(sys.argv) > 1:
        providers = [sys.argv[1]]
    else:
        providers = ["anthropic", "google", "openai", "openrouter"]

    results = {}
    for provider_name in providers:
        results[provider_name] = test_provider(provider_name)

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    for provider_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{provider_name:15} {status}")

    # Exit code
    if all(results.values()):
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed or were skipped")
        sys.exit(1)


if __name__ == "__main__":
    main()
