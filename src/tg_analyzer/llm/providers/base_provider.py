"""
Base LLM provider interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from ...config.models import LLMConfig


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, config: LLMConfig):
        """
        Initialize provider

        Args:
            config: LLM configuration
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration"""
        pass

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text response

        Args:
            prompt: Input prompt
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate text response with streaming

        Args:
            prompt: Input prompt
            **kwargs: Provider-specific parameters

        Yields:
            Text chunks as they are generated
        """
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings for texts

        Args:
            texts: List of texts to embed
            **kwargs: Provider-specific parameters

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Input text

        Returns:
            Token count
        """
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Get maximum context length"""
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """Get available models for this provider"""
        pass

    def estimate_cost(self, input_tokens: int, output_tokens: int = 0) -> float:
        """
        Estimate cost for token usage

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Default implementation - override in subclasses for actual pricing
        return 0.0

    def truncate_text(self, text: str, max_tokens: Optional[int] = None) -> str:
        """
        Truncate text to fit within token limit

        Args:
            text: Input text
            max_tokens: Maximum token count (uses provider default if None)

        Returns:
            Truncated text
        """
        if max_tokens is None:
            max_tokens = self.get_max_tokens()

        # Simple character-based truncation as fallback
        # Subclasses should implement proper token-based truncation
        chars_per_token = 4  # Rough estimate
        max_chars = max_tokens * chars_per_token

        if len(text) <= max_chars:
            return text

        return text[:max_chars].rsplit(' ', 1)[0] + "..."
