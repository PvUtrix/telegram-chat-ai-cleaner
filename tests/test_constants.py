"""
Tests for application constants
"""

from src.tg_analyzer.constants import (
    VALID_CLEANING_APPROACHES,
    VALID_CLEANING_LEVELS,
    VALID_OUTPUT_FORMATS,
    VALID_LLM_PROVIDERS,
    MODEL_PRICING,
    MODEL_CONTEXT_LENGTHS
)


class TestConstants:
    """Test suite for application constants"""

    def test_valid_cleaning_approaches(self):
        """Test valid cleaning approaches are defined"""
        assert "privacy" in VALID_CLEANING_APPROACHES
        assert "size" in VALID_CLEANING_APPROACHES
        assert "context" in VALID_CLEANING_APPROACHES
        assert len(VALID_CLEANING_APPROACHES) == 3

    def test_valid_cleaning_levels(self):
        """Test valid cleaning levels are defined"""
        assert 1 in VALID_CLEANING_LEVELS
        assert 2 in VALID_CLEANING_LEVELS
        assert 3 in VALID_CLEANING_LEVELS
        assert len(VALID_CLEANING_LEVELS) == 3

    def test_valid_output_formats(self):
        """Test valid output formats are defined"""
        assert "text" in VALID_OUTPUT_FORMATS
        assert "json" in VALID_OUTPUT_FORMATS
        assert "markdown" in VALID_OUTPUT_FORMATS
        assert "csv" in VALID_OUTPUT_FORMATS

    def test_valid_llm_providers(self):
        """Test valid LLM providers are defined"""
        assert "openai" in VALID_LLM_PROVIDERS
        assert "anthropic" in VALID_LLM_PROVIDERS
        assert "google" in VALID_LLM_PROVIDERS
        assert "groq" in VALID_LLM_PROVIDERS
        assert "ollama" in VALID_LLM_PROVIDERS
        assert "openrouter" in VALID_LLM_PROVIDERS

    def test_model_pricing_structure(self):
        """Test model pricing has correct structure"""
        for model, prices in MODEL_PRICING.items():
            assert "input" in prices
            assert "output" in prices
            assert isinstance(prices["input"], (int, float))
            assert isinstance(prices["output"], (int, float))
            assert prices["input"] > 0
            assert prices["output"] > 0

    def test_model_context_lengths(self):
        """Test model context lengths are defined"""
        assert "gpt-4" in MODEL_CONTEXT_LENGTHS
        assert "gpt-4-turbo" in MODEL_CONTEXT_LENGTHS
        assert "gpt-3.5-turbo" in MODEL_CONTEXT_LENGTHS

        for model, length in MODEL_CONTEXT_LENGTHS.items():
            assert isinstance(length, int)
            assert length > 0
