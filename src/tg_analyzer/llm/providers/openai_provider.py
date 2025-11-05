"""
OpenAI LLM provider
"""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
import tiktoken

try:
    from openai import AsyncOpenAI
    from openai import OpenAIError
except ImportError:
    AsyncOpenAI = None
    OpenAIError = Exception

from .base_provider import BaseLLMProvider
from ...config.models import LLMConfig


logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._encoder = None

    def _validate_config(self) -> None:
        """Validate OpenAI configuration"""
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required")

        # Set default model if not specified
        if not self.config.model:
            self.config.model = "gpt-4"

    async def _get_client(self):
        """Get or create OpenAI client"""
        if self._client is None:
            if AsyncOpenAI is None:
                raise ImportError("openai package is required for OpenAI provider")

            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
        return self._client

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI

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
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            }

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            response = await client.chat.completions.create(**params)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
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
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "stream": True,
            }

            params = {k: v for k, v in params.items() if v is not None}

            stream = await client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise

    async def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings using OpenAI

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        try:
            client = await self._get_client()

            model = kwargs.get("model", "text-embedding-3-small")

            # OpenAI has a limit on batch size
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                response = await client.embeddings.create(
                    input=batch,
                    model=model
                )

                embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(embeddings)

            return all_embeddings

        except Exception as e:
            logger.error(f"OpenAI embeddings failed: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            if self._encoder is None:
                self._encoder = tiktoken.encoding_for_model(self.config.model or "gpt-4")

            return len(self._encoder.encode(text))
        except Exception:
            # Fallback: rough character-based estimation
            return len(text) // 4

    def get_max_tokens(self) -> int:
        """Get maximum context length"""
        model_limits = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-4-turbo-preview": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
        }

        model = self.config.model or "gpt-4"
        return model_limits.get(model, 4096)

    def get_models(self) -> List[str]:
        """Get available OpenAI models"""
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]

    def estimate_cost(self, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimate OpenAI API cost"""
        model = self.config.model or "gpt-4"

        # Pricing per 1K tokens (as of 2024)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        }

        rates = pricing.get(model, pricing["gpt-4"])

        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]

        return input_cost + output_cost
