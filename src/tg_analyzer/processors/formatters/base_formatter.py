"""
Base formatter class and factory functions
"""

from abc import ABC, abstractmethod


class BaseFormatter(ABC):
    """Abstract base class for output formatters"""

    def __init__(self, format_type: str):
        """
        Initialize formatter

        Args:
            format_type: Format type (text, json, markdown, etc.)
        """
        self.format_type = format_type

    @abstractmethod
    def format(self, cleaned_data: str) -> str:
        """
        Format the cleaned data

        Args:
            cleaned_data: Cleaned text data from cleaner

        Returns:
            Formatted output
        """
        pass


def get_formatter(format_type: str) -> BaseFormatter:
    """
    Factory function to get the appropriate formatter

    Args:
        format_type: Output format type

    Returns:
        Appropriate formatter instance

    Raises:
        ValueError: If format_type is not supported
    """
    # Import here to avoid circular imports
    if format_type == "text":
        from .text_formatter import TextFormatter

        return TextFormatter()
    elif format_type == "json":
        from .json_formatter import JSONFormatter

        return JSONFormatter()
    elif format_type == "markdown":
        from .markdown_formatter import MarkdownFormatter

        return MarkdownFormatter()
    elif format_type == "csv":
        from .csv_formatter import CSVFormatter

        return CSVFormatter()
    else:
        supported_formats = ["text", "json", "markdown", "csv"]
        raise ValueError(
            f"Unsupported format: {format_type}. Supported: {supported_formats}"
        )
