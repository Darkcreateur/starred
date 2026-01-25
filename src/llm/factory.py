"""Factory for creating LLM providers."""

import os
import logging
from typing import Optional

from .base import BaseLLMProvider
from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
from .gemini import GeminiProvider

logger = logging.getLogger(__name__)

PROVIDERS = {
    "anthropic": AnthropicProvider,
    "claude": AnthropicProvider,  # Alias
    "openai": OpenAIProvider,
    "gpt": OpenAIProvider,  # Alias
    "gemini": GeminiProvider,
    "google": GeminiProvider,  # Alias
}


def list_providers() -> list[str]:
    """List all available provider names."""
    return ["anthropic", "openai", "gemini"]


def get_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMProvider:
    """
    Get an LLM provider instance.
    
    Args:
        provider_name: Name of the provider (anthropic, openai, gemini).
                      If not specified, will auto-detect from available API keys.
        api_key: API key for the provider. If not specified, will use env var.
        model: Model to use. If not specified, will use provider default.
    
    Returns:
        An instance of the requested LLM provider.
    
    Raises:
        ValueError: If provider not found or no API key available.
    """
    # Auto-detect provider from environment if not specified
    if provider_name is None:
        provider_name = _auto_detect_provider()
    
    provider_name = provider_name.lower()
    
    if provider_name not in PROVIDERS:
        available = ", ".join(list_providers())
        raise ValueError(f"Unknown provider: {provider_name}. Available: {available}")
    
    provider_class = PROVIDERS[provider_name]
    
    # Get API key from env if not provided
    if api_key is None:
        env_key = provider_class.get_env_key()
        api_key = os.environ.get(env_key)
        if not api_key:
            raise ValueError(
                f"No API key provided and {env_key} environment variable not set. "
                f"Set the environment variable or pass api_key parameter."
            )
    
    logger.info(f"Using LLM provider: {provider_name} (model: {model or provider_class.default_model})")
    return provider_class(api_key=api_key, model=model)


def _auto_detect_provider() -> str:
    """Auto-detect which provider to use based on available API keys."""
    # Check in order of preference
    providers_to_check = [
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("openai", "OPENAI_API_KEY"),
        ("gemini", "GEMINI_API_KEY"),
    ]
    
    for provider_name, env_var in providers_to_check:
        if os.environ.get(env_var):
            logger.info(f"Auto-detected provider: {provider_name} (found {env_var})")
            return provider_name
    
    raise ValueError(
        "No LLM provider API key found. Set one of: "
        "ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY"
    )
