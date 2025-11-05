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
        """
        # Parse the input file
        data = self.parser.parse_file(input_file)

        # Get the appropriate cleaner
        cleaner = get_cleaner(approach, level)

        # Clean the data
        cleaned_data = cleaner.clean(data)

        # Format the output
        formatter = get_formatter(output_format)
        return formatter.format(cleaned_data)

    def analyze(
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
        """
        return self.llm_manager.analyze(
            input_data=input_data,
            prompt=prompt,
            provider=provider,
            model=model,
            **kwargs
        )

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
