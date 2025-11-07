"""
Text formatter for plain text output
"""

from .base_formatter import BaseFormatter


class TextFormatter(BaseFormatter):
    """Formats cleaned data as plain text"""

    def __init__(self):
        super().__init__("text")

    def format(self, cleaned_data: str) -> str:
        """
        Format cleaned data as plain text

        Args:
            cleaned_data: Cleaned text data

        Returns:
            Plain text output (essentially unchanged)
        """
        # Text formatter is essentially pass-through
        # The cleaned_data is already in the desired text format
        return cleaned_data.strip()
