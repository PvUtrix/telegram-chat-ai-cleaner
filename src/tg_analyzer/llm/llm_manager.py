"""
LLM Manager - Unified interface for all LLM providers
"""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from ..config.config_manager import ConfigManager
from ..config.models import LLMConfig
from .providers import (
    BaseLLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    GroqProvider,
    OllamaProvider,
    OpenRouterProvider,
)


logger = logging.getLogger(__name__)


class LLMManager:
    """Manages multiple LLM providers with unified interface"""

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize LLM manager

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._current_provider: Optional[str] = None

    def _get_provider_config(self, provider_name: str) -> LLMConfig:
        """Get configuration for a specific provider"""
        config = self.config_manager.get_all()

        # Map provider names to config keys
        provider_configs = {
            "openai": {
                "api_key": config.get("openai_api_key"),
                "model": config.get("default_llm_model", "gpt-4"),
            },
            "anthropic": {
                "api_key": config.get("anthropic_api_key"),
                "model": config.get("default_llm_model", "claude-3-sonnet-20240229"),
            },
            "google": {
                "api_key": config.get("google_api_key"),
                "model": config.get("default_llm_model", "gemini-pro"),
            },
            "groq": {
                "api_key": config.get("groq_api_key"),
                "model": config.get("default_llm_model", "mixtral-8x7b-32768"),
            },
            "ollama": {
                "base_url": config.get("ollama_base_url", "http://localhost:11434"),
                "model": config.get("ollama_model", "llama2"),
            },
            "openrouter": {
                "api_key": config.get("openrouter_api_key"),
                "model": config.get("default_llm_model", "openai/gpt-4"),
            },
        }

        provider_config = provider_configs.get(provider_name, {})
        if not provider_config:
            raise ValueError(f"Unknown provider: {provider_name}")

        return LLMConfig(
            provider=provider_name,
            model=provider_config.get("model"),
            api_key=provider_config.get("api_key"),
            base_url=provider_config.get("base_url"),
            temperature=config.get("default_llm_temperature", 0.7),
        )

    def _get_provider(self, provider_name: Optional[str] = None) -> BaseLLMProvider:
        """
        Get or create provider instance

        Args:
            provider_name: Provider name, uses default if None

        Returns:
            Provider instance
        """
        if provider_name is None:
            provider_name = self.config_manager.get("default_llm_provider", "openai")

        if provider_name not in self._providers:
            provider_config = self._get_provider_config(provider_name)

            # Create provider instance
            providers = {
                "openai": OpenAIProvider,
                "anthropic": AnthropicProvider,
                "google": GoogleProvider,
                "groq": GroqProvider,
                "ollama": OllamaProvider,
                "openrouter": OpenRouterProvider,
            }

            provider_class = providers.get(provider_name)
            if not provider_class:
                raise ValueError(f"Unsupported provider: {provider_name}")

            self._providers[provider_name] = provider_class(provider_config)

        return self._providers[provider_name]

    async def generate(
        self,
        input_data: str,
        prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate analysis using LLM

        Args:
            input_data: Chat data to analyze
            prompt: Custom prompt (optional)
            provider: LLM provider override
            model: Model override
            **kwargs: Additional parameters

        Returns:
            Generated analysis
        """
        provider_instance = self._get_provider(provider)

        # Prepare the full prompt
        full_prompt = self._prepare_prompt(input_data, prompt)

        # Override model if specified
        if model:
            kwargs["model"] = model

        try:
            logger.info(f"Generating with {provider or 'default'} provider")
            result = await provider_instance.generate(full_prompt, **kwargs)
            logger.info("Generation completed successfully")
            return result

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    async def generate_stream(
        self,
        input_data: str,
        prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate analysis with streaming

        Args:
            input_data: Chat data to analyze
            prompt: Custom prompt (optional)
            provider: LLM provider override
            model: Model override
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
        """
        provider_instance = self._get_provider(provider)
        full_prompt = self._prepare_prompt(input_data, prompt)

        if model:
            kwargs["model"] = model

        try:
            async for chunk in provider_instance.generate_stream(full_prompt, **kwargs):
                yield chunk

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

    async def analyze(
        self,
        input_data: str,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Analyze chat data with custom prompt

        Args:
            input_data: Chat data to analyze
            prompt: Analysis prompt
            provider: LLM provider override
            model: Model override
            **kwargs: Additional parameters

        Returns:
            Analysis result
        """
        # For analysis, we combine the prompt with the data
        full_prompt = f"{prompt}\n\nChat Data:\n{input_data}"

        return await self.generate(
            input_data=full_prompt,
            prompt=None,  # Already included in input_data
            provider=provider,
            model=model,
            **kwargs
        )

    def _prepare_prompt(self, input_data: str, custom_prompt: Optional[str] = None) -> str:
        """Prepare the full prompt for LLM"""
        if custom_prompt:
            return f"{custom_prompt}\n\nData to analyze:\n{input_data}"

        # Default analysis prompt
        default_prompt = """Please analyze this Telegram chat export and provide insights about:

1. Main topics discussed
2. Key participants and their roles
3. Overall sentiment and tone
4. Any notable patterns or trends
5. Important links or resources shared

Chat data:
{input_data}
"""

        return default_prompt.format(input_data=input_data)

    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return ["openai", "anthropic", "google", "groq", "ollama", "openrouter"]

    def get_provider_info(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a provider

        Args:
            provider: Provider name, or current default if None

        Returns:
            Provider information
        """
        if provider is None:
            provider = self.config_manager.get("default_llm_provider", "openai")

        provider_instance = self._get_provider(provider)

        return {
            "name": provider,
            "models": provider_instance.get_models(),
            "max_tokens": provider_instance.get_max_tokens(),
            "current_model": provider_instance.config.model,
        }

    def estimate_cost(self, text: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Estimate cost for processing text

        Args:
            text: Text to process
            provider: Provider name

        Returns:
            Cost estimation details
        """
        provider_instance = self._get_provider(provider)
        input_tokens = provider_instance.count_tokens(text)

        # Assume output is roughly 1/3 of input for analysis tasks
        output_tokens = input_tokens // 3

        cost = provider_instance.estimate_cost(input_tokens, output_tokens)

        return {
            "provider": provider or self.config_manager.get("default_llm_provider"),
            "input_tokens": input_tokens,
            "estimated_output_tokens": output_tokens,
            "estimated_cost_usd": cost,
        }

    async def close(self):
        """Close all provider connections"""
        for provider in self._providers.values():
            if hasattr(provider, 'close'):
                try:
                    await provider.close()
                except Exception as e:
                    logger.warning(f"Error closing provider: {e}")

        self._providers.clear()

