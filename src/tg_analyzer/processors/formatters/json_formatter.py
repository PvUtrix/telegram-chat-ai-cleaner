"""
JSON formatter for structured output
"""

import json
from .base_formatter import BaseFormatter


class JSONFormatter(BaseFormatter):
    """Formats cleaned data as JSON"""

    def __init__(self):
        super().__init__("json")

    def format(self, cleaned_data: str) -> str:
        """
        Format cleaned data as JSON

        Note: This formatter expects the cleaned_data to be in a specific
        format that can be parsed back into structured data. For now,
        it wraps the text in a simple JSON structure.

        Args:
            cleaned_data: Cleaned text data

        Returns:
            JSON formatted output
        """
        # For now, create a simple JSON structure
        # In a more advanced implementation, this could parse the cleaned
        # text back into structured message objects

        result = {
            "format": "telegram_chat_cleaned",
            "version": "1.0",
            "content": cleaned_data.strip(),
            "metadata": {
                "generated_by": "telegram-chat-analyzer",
                "format_type": "text_wrapped_json",
            },
        }

        return json.dumps(result, indent=2, ensure_ascii=False)
