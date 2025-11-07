"""
Batch processing for multiple Telegram chat files
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core import TelegramAnalyzer
from ..config.models import ProcessingResult, BatchProcessingResult


logger = logging.getLogger(__name__)


class BatchProcessor:
    """Handles batch processing of multiple Telegram export files"""

    def __init__(self, analyzer: TelegramAnalyzer, max_workers: int = 4):
        """
        Initialize batch processor

        Args:
            analyzer: TelegramAnalyzer instance
            max_workers: Maximum number of worker threads
        """
        self.analyzer = analyzer
        self.max_workers = max_workers

    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        approach: str = "privacy",
        level: int = 2,
        output_format: str = "text",
        skip_existing: bool = True,
    ) -> Dict[str, str]:
        """
        Process all JSON files in a directory

        Args:
            input_dir: Directory containing JSON files
            output_dir: Directory to save processed files
            approach: Cleaning approach
            level: Cleaning level
            output_format: Output format
            skip_existing: Skip files that have already been processed

        Returns:
            Dict mapping input file paths to output file paths
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_path}")

        # Find all JSON files
        json_files = list(input_path.glob("*.json"))
        if not json_files:
            logger.warning(f"No JSON files found in {input_path}")
            return {}

        logger.info(f"Found {len(json_files)} JSON files to process")

        # Process files
        results = {}

        if len(json_files) == 1:
            # Single file - process directly
            input_file = json_files[0]
            output_file = self._generate_output_path(
                input_file, output_path, approach, level, output_format
            )

            if skip_existing and output_file.exists():
                logger.info(f"Skipping existing file: {input_file}")
                results[str(input_file)] = str(output_file)
            else:
                result = self._process_single_file(
                    input_file, output_file, approach, level, output_format
                )
                results[str(input_file)] = str(output_file) if result.success else ""
        else:
            # Multiple files - use thread pool
            results = self._process_multiple_files(
                json_files, output_path, approach, level, output_format, skip_existing
            )

        return results

    def _process_multiple_files(
        self,
        files: List[Path],
        output_dir: Path,
        approach: str,
        level: int,
        output_format: str,
        skip_existing: bool,
    ) -> Dict[str, str]:
        """Process multiple files using thread pool"""
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {}
            for input_file in files:
                output_file = self._generate_output_path(
                    input_file, output_dir, approach, level, output_format
                )

                if skip_existing and output_file.exists():
                    logger.info(f"Skipping existing file: {input_file}")
                    results[str(input_file)] = str(output_file)
                    continue

                future = executor.submit(
                    self._process_single_file,
                    input_file,
                    output_file,
                    approach,
                    level,
                    output_format,
                )
                future_to_file[future] = (input_file, output_file)

            # Collect results
            for future in as_completed(future_to_file):
                input_file, output_file = future_to_file[future]
                try:
                    result = future.result()
                    results[str(input_file)] = (
                        str(output_file) if result.success else ""
                    )
                except Exception as e:
                    logger.error(f"Failed to process {input_file}: {e}")
                    results[str(input_file)] = ""

        return results

    def _process_single_file(
        self,
        input_file: Path,
        output_file: Path,
        approach: str,
        level: int,
        output_format: str,
    ) -> ProcessingResult:
        """Process a single file"""
        try:
            logger.info(f"Processing: {input_file}")

            # Clean the data
            cleaned_data = self.analyzer.clean(
                input_file=str(input_file),
                approach=approach,
                level=level,
                output_format=output_format,
            )

            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Save result
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(cleaned_data)

            logger.info(f"Successfully processed: {input_file} -> {output_file}")

            return ProcessingResult(
                success=True,
                input_file=str(input_file),
                output_file=str(output_file),
                message_count=self._estimate_message_count(cleaned_data),
                processing_time=0.0,  # Would need timing decorator
                metadata={
                    "approach": approach,
                    "level": level,
                    "format": output_format,
                    "size_bytes": len(cleaned_data),
                },
            )

        except Exception as e:
            logger.error(f"Failed to process {input_file}: {e}")

            return ProcessingResult(
                success=False, input_file=str(input_file), error=str(e)
            )

    def _generate_output_path(
        self,
        input_file: Path,
        output_dir: Path,
        approach: str,
        level: int,
        output_format: str,
    ) -> Path:
        """Generate output file path"""
        # Use output directory directly (no subdirectories)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract chat name from JSON file
        chat_name = self._extract_chat_name(input_file)

        # Generate filename
        extension = self._get_extension(output_format)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean chat name for filename
        clean_name = self._clean_filename(chat_name)
        level_name = ["basic", "medium", "full"][level - 1]

        filename = f"{clean_name}_{approach}_{level_name}_{timestamp}{extension}"

        return output_dir / filename

    def _get_extension(self, output_format: str) -> str:
        """Get file extension for output format"""
        extensions = {"text": ".txt", "json": ".json", "markdown": ".md", "csv": ".csv"}
        return extensions.get(output_format, ".txt")

    def _extract_chat_name(self, input_path: Path) -> str:
        """Extract chat name from Telegram JSON file"""
        try:
            import json

            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("name", input_path.stem)
        except Exception:
            # Fallback to filename if JSON parsing fails
            return input_path.stem

    def _clean_filename(self, name: str) -> str:
        """Clean chat name for use in filename"""
        import re

        # Remove special characters except spaces, hyphens, and underscores
        clean_name = re.sub(r"[^\w\s-]", "", name)
        # Replace spaces and multiple hyphens with single underscore
        clean_name = re.sub(r"[-\s]+", "_", clean_name)
        # Remove leading/trailing underscores
        clean_name = clean_name.strip("_")
        return clean_name or "unknown_chat"

    def _estimate_message_count(self, cleaned_data: str) -> int:
        """Estimate number of messages in cleaned data"""
        # Rough estimation based on line breaks and content
        lines = cleaned_data.strip().split("\n")

        # Count non-empty lines that look like message starts
        message_count = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith("=") and not line.startswith("Chat:"):
                # Look for patterns that indicate message starts
                if any(indicator in line for indicator in [":", "]:", "ID:"]):
                    message_count += 1

        return max(message_count, 1)  # At least 1 if we have content

    def get_processing_stats(self, results: Dict[str, str]) -> BatchProcessingResult:
        """
        Generate statistics from batch processing results

        Args:
            results: Results from process_directory

        Returns:
            Batch processing statistics
        """
        total_files = len(results)
        successful_files = sum(1 for output in results.values() if output)
        failed_files = total_files - successful_files

        processing_results = []
        total_time = 0.0

        for input_file, output_file in results.items():
            success = bool(output_file)
            processing_results.append(
                ProcessingResult(
                    success=success,
                    input_file=input_file,
                    output_file=output_file if success else None,
                    processing_time=0.0,  # Would need actual timing
                )
            )

        return BatchProcessingResult(
            total_files=total_files,
            successful_files=successful_files,
            failed_files=failed_files,
            results=processing_results,
            total_processing_time=total_time,
        )
