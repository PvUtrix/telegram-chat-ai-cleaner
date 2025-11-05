"""
Ollama local LLM provider
"""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
import aiohttp
import json

from .base_provider import BaseLLMProvider
from ...config.models import LLMConfig


logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama local API provider"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._base_url = self.config.base_url or "http://localhost:11434"
        self._session = None

    def _validate_config(self) -> None:
        """Validate Ollama configuration"""
        # Ollama doesn't require API keys, just a base URL
        if not self.config.model:
            self.config.model = "llama2"

    async def _get_session(self):
        """Get or create HTTP session"""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Ollama API"""
        session = await self._get_session()
        url = f"{self._base_url}/{endpoint}"

        async with session.post(url, json=data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama API error: {response.status} - {error_text}")

            return await response.json()

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Ollama

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        try:
            data = {
                "model": kwargs.get("model", self.config.model),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                }
            }

            # Remove None values from options
            data["options"] = {k: v for k, v in data["options"].items() if v is not None}

            response = await self._make_request("api/generate", data)
            return response.get("response", "")

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
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
            session = await self._get_session()
            url = f"{self._base_url}/api/generate"

            data = {
                "model": kwargs.get("model", self.config.model),
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                }
            }

            # Remove None values from options
            data["options"] = {k: v for k, v in data["options"].items() if v is not None}

            async with session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")

                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line:
                        try:
                            chunk = json.loads(line)
                            if chunk.get("response"):
                                yield chunk["response"]
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise

    async def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings using Ollama

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        try:
            all_embeddings = []

            for text in texts:
                data = {
                    "model": kwargs.get("model", self.config.model),
                    "prompt": text,
                }

                response = await self._make_request("api/embeddings", data)
                embedding = response.get("embedding", [])
                all_embeddings.append(embedding)

            return all_embeddings

        except Exception as e:
            logger.error(f"Ollama embeddings failed: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        # Ollama doesn't provide token counting, use rough estimation
        return len(text) // 4

    def get_max_tokens(self) -> int:
        """Get maximum context length"""
        # This varies by model, use a conservative default
        # In practice, you'd need to query the model info
        model_limits = {
            "llama2": 4096,
            "llama2:13b": 4096,
            "llama2:70b": 4096,
            "codellama": 16384,
            "mistral": 8192,
            "mixtral": 32768,
        }

        model = self.config.model or "llama2"
        return model_limits.get(model, 4096)

    def get_models(self) -> List[str]:
        """Get available Ollama models"""
        # This would ideally query the Ollama API for available models
        # For now, return common models
        return [
            "llama2",
            "llama2:13b",
            "llama2:70b",
            "codellama",
            "mistral",
            "mixtral",
            "vicuna",
            "orca-mini",
        ]

    def estimate_cost(self, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimate Ollama cost (always free for local models)"""
        return 0.0

    async def close(self):
        """Close HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None
