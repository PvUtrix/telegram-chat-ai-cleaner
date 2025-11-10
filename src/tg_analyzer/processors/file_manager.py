"""
File management for input/output organization
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import hashlib
import json
from datetime import datetime

from ..config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class FileManager:
    """Manages file organization for batch processing"""

    def __init__(self, config: ConfigManager):
        """
        Initialize file manager

        Args:
            config: Configuration manager
        """
        self.config = config
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.get_data_dir(),
            self.get_input_dir(),
            self.get_output_dir(),
            self.get_analysis_dir(),
            self.get_vectors_dir(),
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_data_dir(self) -> Path:
        """Get the base data directory"""
        return Path(self.config.get("data_dir", "data"))

    def get_input_dir(self) -> Path:
        """Get the input directory"""
        return self.get_data_dir() / self.config.get("input_dir", "input")

    def get_output_dir(
        self, approach: Optional[str] = None, level: Optional[int] = None
    ) -> Path:
        """Get the output directory, optionally with subdirectories"""
        base_output = self.get_data_dir() / self.config.get("output_dir", "output")

        if approach and level:
            level_name = ["basic", "medium", "full"][level - 1]
            return base_output / f"{approach}_{level_name}"

        return base_output

    def get_analysis_dir(self) -> Path:
        """Get the analysis results directory"""
        return self.get_data_dir() / self.config.get("analysis_dir", "analysis")

    def get_vectors_dir(self) -> Path:
        """Get the vectors metadata directory"""
        return self.get_data_dir() / self.config.get("vectors_dir", "vectors")

    def generate_output_path(
        self, input_file: str, approach: str, level: int, output_format: str
    ) -> str:
        """Generate output file path for a given input file"""
        input_path = Path(input_file)
        output_dir = self.get_data_dir() / "output"

        # Extract chat name from JSON file
        chat_name = self._extract_chat_name(input_path)

        # Generate filename
        extension = self._get_extension(output_format)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean chat name for filename
        clean_name = self._clean_filename(chat_name)
        level_name = ["basic", "medium", "full"][level - 1]

        filename = f"{clean_name}_{approach}_{level_name}_{timestamp}{extension}"

        return str(output_dir / filename)

    def generate_analysis_path(self, input_file: str, analysis_type: str) -> str:
        """Generate path for analysis results"""
        input_path = Path(input_file)
        analysis_dir = self.get_analysis_dir()

        stem = input_path.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{stem}_{analysis_type}_{timestamp}.md"

        return str(analysis_dir / filename)

    def list_input_files(self) -> List[Path]:
        """List all JSON files in input directory"""
        input_dir = self.get_input_dir()
        return list(input_dir.glob("*.json"))

    def list_processed_files(self, approach: str, level: int) -> List[Path]:
        """List all processed files for a given approach and level"""
        output_dir = self.get_output_dir(approach, level)
        return list(output_dir.glob("*"))

    def get_processing_log_path(self) -> Path:
        """Get path to processing log file"""
        return self.get_data_dir() / "processing_log.json"

    def log_processing_result(self, result: Dict[str, Any]):
        """Log a processing result to the processing log"""
        log_path = self.get_processing_log_path()

        # Load existing log
        if log_path.exists():
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    log_data = json.load(f)
            except Exception:
                log_data = {"entries": []}
        else:
            log_data = {"entries": []}

        # Add new entry
        entry = {"timestamp": datetime.now().isoformat(), **result}
        log_data["entries"].append(entry)

        # Keep only last 1000 entries
        log_data["entries"] = log_data["entries"][-1000:]

        # Save log
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

    def get_processing_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get processing history"""
        log_path = self.get_processing_log_path()

        if not log_path.exists():
            return []

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                log_data = json.load(f)
                return log_data.get("entries", [])[-limit:]
        except Exception:
            return []

    def find_similar_processed_files(self, input_file: str) -> List[Dict[str, Any]]:
        """Find previously processed versions of the same input file"""
        input_path = Path(input_file)

        history = self.get_processing_history(200)  # Check last 200 entries

        similar = []
        for entry in history:
            if entry.get("input_file") == str(input_path):
                similar.append(entry)

        return similar

    def cleanup_old_files(self, days_to_keep: int = 30):
        """Clean up old processed files"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        directories_to_clean = [
            self.get_output_dir(),
            self.get_analysis_dir(),
            self.get_vectors_dir(),
        ]

        total_cleaned = 0

        for directory in directories_to_clean:
            if not directory.exists():
                continue

            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    try:
                        # Check file modification time
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime < cutoff_date:
                            file_path.unlink()
                            total_cleaned += 1
                            logger.info(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {file_path}: {e}")

        logger.info(f"Cleaned up {total_cleaned} old files")
        return total_cleaned

    def get_directory_stats(self) -> Dict[str, Any]:
        """Get statistics about files in data directories"""
        stats = {
            "input_files": len(self.list_input_files()),
            "total_processed_files": 0,
            "total_analysis_files": 0,
            "total_vector_files": 0,
            "processing_history_entries": len(self.get_processing_history(1000)),
        }

        # Count files in output subdirectories
        output_base = self.get_output_dir()
        if output_base.exists():
            for subdir in output_base.iterdir():
                if subdir.is_dir():
                    file_count = len(list(subdir.glob("*")))
                    stats["total_processed_files"] += file_count

        # Count analysis files
        analysis_dir = self.get_analysis_dir()
        if analysis_dir.exists():
            stats["total_analysis_files"] = len(list(analysis_dir.glob("*")))

        # Count vector files
        vectors_dir = self.get_vectors_dir()
        if vectors_dir.exists():
            stats["total_vector_files"] = len(list(vectors_dir.glob("*")))

        return stats

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

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
        except Exception:
            return ""

        return hash_sha256.hexdigest()
