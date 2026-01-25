"""Google Gemini LLM provider."""

import json
import logging
from typing import Optional

from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider."""
    
    name = "gemini"
    default_model = "gemini-2.0-flash"
    
    AVAILABLE_MODELS = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ]
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
            self.client = genai.GenerativeModel(self.model)
        except ImportError:
            raise ImportError("google-generativeai package required. Install with: pip install google-generativeai")
    
    @classmethod
    def get_env_key(cls) -> str:
        return "GEMINI_API_KEY"
    
    @classmethod
    def get_available_models(cls) -> list[str]:
        return cls.AVAILABLE_MODELS
    
    def complete(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        """Generate a completion using Gemini."""
        response = self.client.generate_content(
            prompt,
            generation_config=self.genai.GenerationConfig(
                max_output_tokens=max_tokens,
            )
        )
        
        # Gemini doesn't always provide token counts
        input_tokens = None
        output_tokens = None
        if hasattr(response, 'usage_metadata'):
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', None)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', None)
        
        return LLMResponse(
            content=response.text,
            model=self.model,
            provider=self.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    
    def complete_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        """Generate a completion with JSON mode and parse."""
        # Use JSON mode for Gemini
        response = self.client.generate_content(
            prompt,
            generation_config=self.genai.GenerationConfig(
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
            )
        )
        
        content = response.text
        try:
            # Clean up response if needed
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response.text}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
