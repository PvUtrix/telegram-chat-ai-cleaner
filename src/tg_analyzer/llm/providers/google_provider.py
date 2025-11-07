"""
Google Gemini provider
"""

import logging
from typing import List, AsyncGenerator

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .base_provider import BaseLLMProvider
from ...config.models import LLMConfig


logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """Google Gemini API provider"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._model = None

    def _validate_config(self) -> None:
        """Validate Google configuration"""
        if not self.config.api_key:
            raise ValueError("Google API key is required")

        # Set default model if not specified
        if not self.config.model:
            self.config.model = "gemini-pro"

    def _get_model(self):
        """Get or create Gemini model"""
        if self._model is None:
            if genai is None:
                raise ImportError(
                    "google-generativeai package is required for Google provider"
                )

            genai.configure(api_key=self.config.api_key)
            self._model = genai.GenerativeModel(self.config.model)

        return self._model

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Google Gemini

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        try:
            model = self._get_model()

            # Prepare generation config
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get("temperature", self.config.temperature),
                max_output_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )

            response = await model.generate_content_async(
                prompt, generation_config=generation_config
            )

            return response.text

        except Exception as e:
            logger.error(f"Google Gemini generation failed: {e}")
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
            model = self._get_model()

            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get("temperature", self.config.temperature),
                max_output_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )

            response = await model.generate_content_async(
                prompt, generation_config=generation_config, stream=True
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Google Gemini streaming failed: {e}")
            raise

    async def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings using Google

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        try:
            if genai is None:
                raise ImportError("google-generativeai package is required")

            # Use the embedding model
            model_name = kwargs.get("model", "models/embedding-001")

            # Google has limits on batch size
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]

                result = genai.embed_content(
                    model=model_name, content=batch, task_type="retrieval_document"
                )

                # Handle both single and batch responses
                if (
                    isinstance(result["embedding"], list)
                    and len(result["embedding"]) > 0
                ):
                    if isinstance(result["embedding"][0], list):
                        # Batch response
                        all_embeddings.extend(result["embedding"])
                    else:
                        # Single response
                        all_embeddings.append(result["embedding"])

            return all_embeddings

        except Exception as e:
            logger.error(f"Google embeddings failed: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            model = self._get_model()
            return model.count_tokens(text).total_tokens
        except Exception:
            # Fallback: rough character-based estimation
            return len(text) // 4

    def get_max_tokens(self) -> int:
        """Get maximum context length"""
        model_limits = {
            "gemini-pro": 32768,
            "gemini-pro-vision": 16384,
            "gemini-1.5-pro": 2097152,  # 2M tokens!
            "gemini-1.5-flash": 1048576,  # 1M tokens
        }

        model = self.config.model or "gemini-pro"
        return model_limits.get(model, 32768)

    def get_models(self) -> List[str]:
        """Get available Google models"""
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]

    def estimate_cost(self, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimate Google API cost"""
        model = self.config.model or "gemini-pro"

        # Pricing per 1K tokens (as of 2024)
        pricing = {
            "gemini-pro": {"input": 0.00025, "output": 0.0005},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        }

        rates = pricing.get(model, pricing["gemini-pro"])

        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]

        return input_cost + output_cost
