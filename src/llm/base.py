"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Standard response from any LLM provider."""
    content: str
    model: str
    provider: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    
    @property
    def total_tokens(self) -> Optional[int]:
        if self.input_tokens is not None and self.output_tokens is not None:
            return self.input_tokens + self.output_tokens
        return None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    name: str = "base"
    default_model: str = ""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.default_model
    
    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        """Generate a completion for the given prompt."""
        pass
    
    @abstractmethod
    def complete_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        """Generate a completion and parse as JSON."""
        pass
    
    @classmethod
    def get_env_key(cls) -> str:
        """Return the environment variable name for the API key."""
        return f"{cls.name.upper()}_API_KEY"
    
    @classmethod
    def get_available_models(cls) -> list[str]:
        """Return list of available models for this provider."""
        return []
