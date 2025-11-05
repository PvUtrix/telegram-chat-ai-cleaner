"""
Tests for core TelegramAnalyzer functionality
"""

import pytest
from src.tg_analyzer.core import TelegramAnalyzer


class TestTelegramAnalyzer:
    """Test suite for TelegramAnalyzer class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = TelegramAnalyzer()

    def test_initialization(self):
        """Test analyzer initializes correctly"""
        assert self.analyzer is not None
        assert self.analyzer.config is not None
        assert self.analyzer.parser is not None
        assert self.analyzer.llm_manager is not None

    def test_clean_invalid_approach(self):
        """Test clean with invalid approach raises ValueError"""
        with pytest.raises(ValueError, match="Invalid approach"):
            self.analyzer.clean(
                "test.json",
                approach="invalid",
                level=2
            )

    def test_clean_invalid_level(self):
        """Test clean with invalid level raises ValueError"""
        with pytest.raises(ValueError, match="Invalid level"):
            self.analyzer.clean(
                "test.json",
                approach="privacy",
                level=5
            )

    def test_clean_invalid_format(self):
        """Test clean with invalid format raises ValueError"""
        with pytest.raises(ValueError, match="Invalid format"):
            self.analyzer.clean(
                "test.json",
                approach="privacy",
                level=2,
                output_format="invalid"
            )

    def test_clean_nonexistent_file(self):
        """Test clean with nonexistent file raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            self.analyzer.clean(
                "nonexistent.json",
                approach="privacy",
                level=2
            )

    @pytest.mark.asyncio
    async def test_analyze_empty_input(self):
        """Test analyze with empty input raises ValueError"""
        with pytest.raises(ValueError, match="Input data cannot be empty"):
            await self.analyzer.analyze(
                input_data="",
                prompt="Test prompt"
            )

    @pytest.mark.asyncio
    async def test_analyze_empty_prompt(self):
        """Test analyze with empty prompt raises ValueError"""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await self.analyzer.analyze(
                input_data="Test data",
                prompt=""
            )

    @pytest.mark.asyncio
    async def test_analyze_invalid_provider(self):
        """Test analyze with invalid provider raises ValueError"""
        with pytest.raises(ValueError, match="Invalid provider"):
            await self.analyzer.analyze(
                input_data="Test data",
                prompt="Test prompt",
                provider="invalid_provider"
            )

    def test_get_config(self):
        """Test get_config returns configuration dictionary"""
        config = self.analyzer.get_config()
        assert isinstance(config, dict)
        assert "default_cleaning_approach" in config

    def test_update_config(self):
        """Test update_config modifies configuration"""
        original_approach = self.analyzer.config.get("default_cleaning_approach")
        new_approach = "size" if original_approach != "size" else "privacy"

        self.analyzer.update_config("default_cleaning_approach", new_approach)
        updated_value = self.analyzer.config.get("default_cleaning_approach")

        assert updated_value == new_approach
