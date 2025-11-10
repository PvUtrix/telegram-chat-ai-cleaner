"""
OpenRouter LLM provider
"""

import logging
from typing import List, AsyncGenerator
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


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API provider (OpenAI-compatible)"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._encoder = None

    def _validate_config(self) -> None:
        """Validate OpenRouter configuration"""
        if not self.config.api_key:
            raise ValueError("OpenRouter API key is required")

        # Set default model if not specified
        if not self.config.model:
            self.config.model = "openai/gpt-4"

    async def _get_client(self):
        """Get or create OpenRouter client"""
        if self._client is None:
            if AsyncOpenAI is None:
                raise ImportError("openai package is required for OpenRouter provider")

            self._client = AsyncOpenAI(
                api_key=self.config.api_key, base_url="https://openrouter.ai/api/v1"
            )
        return self._client

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenRouter

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
            logger.error(f"OpenRouter generation failed: {e}")
            raise

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate text with streaming using OpenRouter

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
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

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            stream = await client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {e}")
            raise

    async def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings using OpenRouter

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        try:
            client = await self._get_client()

            # Use text-embedding-ada-002 model for embeddings
            model = kwargs.get("model", "openai/text-embedding-ada-002")

            response = await client.embeddings.create(model=model, input=texts)

            return [embedding.embedding for embedding in response.data]

        except Exception as e:
            logger.error(f"OpenRouter embeddings failed: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken

        Args:
            text: Input text

        Returns:
            Token count
        """
        try:
            if self._encoder is None:
                # Use cl100k_base encoding (GPT-4 compatible)
                self._encoder = tiktoken.get_encoding("cl100k_base")

            return len(self._encoder.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            # Fallback: rough estimation
            return len(text.split()) * 1.3

    def get_max_tokens(self) -> int:
        """Get maximum context length"""
        # OpenRouter supports various models with different limits
        # Default to GPT-4 limit
        return 8192

    def get_models(self) -> List[str]:
        """Get available models for OpenRouter"""
        return [
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "meta-llama/llama-2-70b-chat",
            "mistralai/mistral-7b-instruct",
        ]

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for OpenRouter usage

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # OpenRouter pricing varies by model
        # Using approximate GPT-4 pricing as default
        input_cost_per_1k = 0.03
        output_cost_per_1k = 0.06

        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k

        return input_cost + output_cost
