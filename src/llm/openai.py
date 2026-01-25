"""OpenAI GPT LLM provider."""

import json
import logging
from typing import Optional

from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT API provider."""
    
    name = "openai"
    default_model = "gpt-4o"
    
    AVAILABLE_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1",
        "o1-mini",
        "o3-mini",
    ]
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
    
    @classmethod
    def get_env_key(cls) -> str:
        return "OPENAI_API_KEY"
    
    @classmethod
    def get_available_models(cls) -> list[str]:
        return cls.AVAILABLE_MODELS
    
    def complete(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        """Generate a completion using GPT."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider=self.name,
            input_tokens=response.usage.prompt_tokens if response.usage else None,
            output_tokens=response.usage.completion_tokens if response.usage else None,
        )
    
    def complete_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        """Generate a completion with JSON mode and parse."""
        # Use JSON mode for OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds in JSON format."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {content}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
