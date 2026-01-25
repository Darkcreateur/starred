"""Anthropic Claude LLM provider."""

import json
import logging
from typing import Optional

from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""
    
    name = "anthropic"
    default_model = "claude-sonnet-4-20250514"
    
    AVAILABLE_MODELS = [
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ]
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package required. Install with: pip install anthropic")
    
    @classmethod
    def get_env_key(cls) -> str:
        return "ANTHROPIC_API_KEY"
    
    @classmethod
    def get_available_models(cls) -> list[str]:
        return cls.AVAILABLE_MODELS
    
    def complete(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        """Generate a completion using Claude."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            provider=self.name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
    
    def complete_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        """Generate a completion and parse as JSON."""
        response = self.complete(prompt, max_tokens)
        try:
            # Try to extract JSON from the response
            content = response.content.strip()
            # Handle markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response.content}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
