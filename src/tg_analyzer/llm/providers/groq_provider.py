"""
Groq provider
"""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator

try:
    import groq
    from groq import Groq
except ImportError:
    Groq = None
    groq = None

from .base_provider import BaseLLMProvider
from ...config.models import LLMConfig


logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq API provider"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _validate_config(self) -> None:
        """Validate Groq configuration"""
        if not self.config.api_key:
            raise ValueError("Groq API key is required")

        # Set default model if not specified
        if not self.config.model:
            self.config.model = "mixtral-8x7b-32768"

    def _get_client(self):
        """Get or create Groq client"""
        if self._client is None:
            if Groq is None:
                raise ImportError("groq package is required for Groq provider")

            self._client = Groq(api_key=self.config.api_key)
        return self._client

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Groq

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        try:
            client = self._get_client()

            # Prepare request parameters
            params = {
                "model": kwargs.get("model", self.config.model),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            }

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            response = client.chat.completions.create(**params)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate text with streaming

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Yields:
            Text chunks
        """
        try:
            client = self._get_client()

            params = {
                "model": kwargs.get("model", self.config.model),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "stream": True,
            }

            params = {k: v for k, v in params.items() if v is not None}

            stream = client.chat.completions.create(**params)

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            raise

    async def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings using Groq

        Note: Groq doesn't provide embeddings API.
        This raises NotImplementedError.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        raise NotImplementedError("Groq does not provide an embeddings API")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        # Groq uses similar tokenization to other LLMs
        # Rough estimation: ~4 characters per token
        return len(text) // 4

    def get_max_tokens(self) -> int:
        """Get maximum context length"""
        model_limits = {
            "mixtral-8x7b-32768": 32768,
            "llama2-70b-4096": 4096,
            "llama2-7b-2048": 2048,
            "gemma-7b-it": 8192,
        }

        model = self.config.model or "mixtral-8x7b-32768"
        return model_limits.get(model, 4096)

    def get_models(self) -> List[str]:
        """Get available Groq models"""
        return [
            "mixtral-8x7b-32768",
            "llama2-70b-4096",
            "llama2-7b-2048",
            "gemma-7b-it",
        ]

    def estimate_cost(self, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimate Groq API cost"""
        model = self.config.model or "mixtral-8x7b-32768"

        # Pricing per 1M tokens (as of 2024)
        pricing = {
            "mixtral-8x7b-32768": {"input": 0.27, "output": 0.27},
            "llama2-70b-4096": {"input": 0.70, "output": 0.80},
            "llama2-7b-2048": {"input": 0.10, "output": 0.10},
            "gemma-7b-it": {"input": 0.10, "output": 0.10},
        }

        rates = pricing.get(model, pricing["mixtral-8x7b-32768"])

        input_cost = (input_tokens / 1000000) * rates["input"]
        output_cost = (output_tokens / 1000000) * rates["output"]

        return input_cost + output_cost
