"""
Anthropic Claude provider
"""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
import tiktoken

try:
    import anthropic
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None
    anthropic = None

from .base_provider import BaseLLMProvider
from ...config.models import LLMConfig


logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _validate_config(self) -> None:
        """Validate Anthropic configuration"""
        if not self.config.api_key:
            raise ValueError("Anthropic API key is required")

        # Set default model if not specified
        if not self.config.model:
            self.config.model = "claude-3-sonnet-20240229"

    async def _get_client(self):
        """Get or create Anthropic client"""
        if self._client is None:
            if AsyncAnthropic is None:
                raise ImportError("anthropic package is required for Anthropic provider")

            self._client = AsyncAnthropic(api_key=self.config.api_key)
        return self._client

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Anthropic Claude

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        try:
            client = await self._get_client()

            # Prepare request parameters
            params = {
                "model": kwargs.get("model", self.config.model),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "messages": [{"role": "user", "content": prompt}],
            }

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            response = await client.messages.create(**params)
            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
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
            client = await self._get_client()

            params = {
                "model": kwargs.get("model", self.config.model),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            }

            params = {k: v for k, v in params.items() if v is not None}

            async with client.messages.stream(**params) as stream:
                async for chunk in stream:
                    if chunk.type == "content_block_delta" and chunk.delta.text:
                        yield chunk.delta.text

        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            raise

    async def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings using Anthropic

        Note: Anthropic doesn't have a public embeddings API yet.
        This raises NotImplementedError.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        raise NotImplementedError("Anthropic does not provide a public embeddings API")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            # Claude uses similar tokenization to GPT
            encoder = tiktoken.encoding_for_model("cl100k_base")  # Claude's tokenizer
            return len(encoder.encode(text))
        except Exception:
            # Fallback: rough character-based estimation
            return len(text) // 4

    def get_max_tokens(self) -> int:
        """Get maximum context length"""
        model_limits = {
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-2.1": 200000,
            "claude-2": 100000,
            "claude-instant-1.2": 100000,
        }

        model = self.config.model or "claude-3-sonnet-20240229"
        return model_limits.get(model, 100000)

    def get_models(self) -> List[str]:
        """Get available Anthropic models"""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2",
            "claude-instant-1.2",
        ]

    def estimate_cost(self, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimate Anthropic API cost"""
        model = self.config.model or "claude-3-sonnet-20240229"

        # Pricing per 1M tokens (as of 2024)
        pricing = {
            "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
            "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
            "claude-2.1": {"input": 8.0, "output": 24.0},
            "claude-2": {"input": 8.0, "output": 24.0},
            "claude-instant-1.2": {"input": 0.8, "output": 2.4},
        }

        rates = pricing.get(model, pricing["claude-3-sonnet-20240229"])

        input_cost = (input_tokens / 1000000) * rates["input"]
        output_cost = (output_tokens / 1000000) * rates["output"]

        return input_cost + output_cost
