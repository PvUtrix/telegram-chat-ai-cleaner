"""
Core TelegramAnalyzer class providing the main API
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import json

from .config.config_manager import ConfigManager
from .processors.telegram_parser import TelegramParser
from .processors.cleaners import get_cleaner
from .processors.formatters import get_formatter
from .llm.llm_manager import LLMManager
from .vector.supabase_client import SupabaseClient


class TelegramAnalyzer:
    """Main class for analyzing Telegram chat exports"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the TelegramAnalyzer

        Args:
            config_path: Path to .env config file (optional)
        """
        self.config = ConfigManager(config_path)
        self.parser = TelegramParser()
        self.llm_manager = LLMManager(self.config)
        self.vector_client = SupabaseClient(self.config)

    def clean(
        self,
        input_file: str,
        approach: str = "privacy",
        level: int = 2,
        output_format: str = "text"
    ) -> str:
        """
        Clean a Telegram export file

        Args:
            input_file: Path to Telegram JSON export
            approach: Cleaning approach (privacy, size, context)
            level: Cleaning level (1, 2, 3)
            output_format: Output format (text, json, markdown)

        Returns:
            Cleaned data as string

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If invalid approach, level, or format specified
            Exception: For other processing errors
        """
        try:
            # Validate inputs
            from .constants import VALID_CLEANING_APPROACHES, VALID_CLEANING_LEVELS, VALID_OUTPUT_FORMATS

            if approach not in VALID_CLEANING_APPROACHES:
                raise ValueError(f"Invalid approach: {approach}. Must be one of {VALID_CLEANING_APPROACHES}")

            if level not in VALID_CLEANING_LEVELS:
                raise ValueError(f"Invalid level: {level}. Must be one of {VALID_CLEANING_LEVELS}")

            if output_format not in VALID_OUTPUT_FORMATS:
                raise ValueError(f"Invalid format: {output_format}. Must be one of {VALID_OUTPUT_FORMATS}")

            # Parse the input file
            data = self.parser.parse_file(input_file)

            if not data or not data.messages:
                raise ValueError(f"No messages found in {input_file}. File may be empty or invalid.")

            # Get the appropriate cleaner
            cleaner = get_cleaner(approach, level)

            # Clean the data
            cleaned_data = cleaner.clean(data)

            # Format the output
            formatter = get_formatter(output_format)
            return formatter.format(cleaned_data)

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Input file not found: {input_file}") from e
        except ValueError as e:
            raise ValueError(f"Validation error: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Failed to clean file {input_file}: {str(e)}") from e

    async def analyze(
        self,
        input_data: str,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Analyze cleaned data with LLM

        Args:
            input_data: Cleaned chat data
            prompt: Analysis prompt
            provider: LLM provider override
            model: Model override
            **kwargs: Additional LLM parameters

        Returns:
            LLM analysis result

        Raises:
            ValueError: If inputs are invalid or API key is missing
            Exception: For LLM API errors
        """
        try:
            if not input_data or not input_data.strip():
                raise ValueError("Input data cannot be empty")

            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")

            # Validate provider if specified
            if provider:
                from .constants import VALID_LLM_PROVIDERS
                if provider not in VALID_LLM_PROVIDERS:
                    raise ValueError(f"Invalid provider: {provider}. Must be one of {VALID_LLM_PROVIDERS}")

            return await self.llm_manager.analyze(
                input_data=input_data,
                prompt=prompt,
                provider=provider,
                model=model,
                **kwargs
            )
        except ValueError as e:
            raise ValueError(f"Analysis validation error: {str(e)}") from e
        except Exception as e:
            raise Exception(f"LLM analysis failed: {str(e)}") from e

    async def vectorize(
        self,
        input_data: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        chunking_strategy: str = "overlap"
    ) -> Dict[str, Any]:
        """
        Create embeddings and store in vector database

        Args:
            input_data: Text data to vectorize
            provider: Embedding provider
            model: Embedding model
            metadata: Additional metadata to store
            chunking_strategy: Text chunking strategy

        Returns:
            Vectorization result with statistics
        """
        from .vector import EmbeddingPipeline, ChunkingStrategy

        pipeline = EmbeddingPipeline(self.config, self.llm_manager)

        # Convert string strategy to enum
        strategy_map = {
            "fixed_size": ChunkingStrategy.FIXED_SIZE,
            "sentence": ChunkingStrategy.SENTENCE,
            "paragraph": ChunkingStrategy.PARAGRAPH,
            "overlap": ChunkingStrategy.OVERLAP
        }

        strategy = strategy_map.get(chunking_strategy, ChunkingStrategy.OVERLAP)

        return await pipeline.process_and_store(
            text=input_data,
            source_metadata=metadata or {},
            chunking_strategy=strategy,
            provider=provider,
            model=model
        )

    async def search_vectors(
        self,
        query: str,
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search vector database for similar content

        Args:
            query: Search query
            limit: Maximum results to return
            metadata_filter: Filter by metadata
            provider: Embedding provider for query

        Returns:
            Search results with similarity scores
        """
        from .vector import EmbeddingPipeline

        pipeline = EmbeddingPipeline(self.config, self.llm_manager)
        return await pipeline.search_similar(
            query=query,
            provider=provider,
            limit=limit,
            metadata_filter=metadata_filter
        )

    def batch_process(
        self,
        input_dir: str = "data/input",
        output_dir: str = "data/output",
        approach: str = "privacy",
        level: int = 2,
        output_format: str = "text"
    ) -> Dict[str, str]:
        """
        Process all JSON files in input directory

        Args:
            input_dir: Directory containing JSON files
            output_dir: Directory to save cleaned files
            approach: Cleaning approach
            level: Cleaning level
            output_format: Output format

        Returns:
            Dict mapping input files to output files
        """
        # Import here to avoid circular import
        from .processors.batch_processor import BatchProcessor

        processor = BatchProcessor(self)
        return processor.process_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            approach=approach,
            level=level,
            output_format=output_format
        )

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.get_all()

    def update_config(self, key: str, value: Any) -> None:
        """Update a configuration value"""
        self.config.set(key, value)
