"""
Markdown formatter for readable output
"""

from typing import Dict, Any, List
import re
from .base_formatter import BaseFormatter


class MarkdownFormatter(BaseFormatter):
    """Formats cleaned data as Markdown"""

    def __init__(self):
        super().__init__("markdown")

    def format(self, cleaned_data: str) -> str:
        """
        Format cleaned data as Markdown

        Args:
            cleaned_data: Cleaned text data

        Returns:
            Markdown formatted output
        """
        lines = cleaned_data.strip().split('\n')
        formatted_lines = []
        in_code_block = False

        for line in lines:
            # Convert headers
            if line.startswith('Chat: ') and line.endswith('==='):
                # Chat header
                chat_name = line.replace('Chat: ', '').replace(' ===', '')
                formatted_lines.append(f"# {chat_name}")
                continue
            elif line.startswith('==='):
                # Section separator
                formatted_lines.append('')
                continue

            # Convert timestamps to smaller text
            line = re.sub(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', r'<small>\1</small>', line)

            # Convert user names to bold
            line = re.sub(r'^([^:]+):', r'**\1:**', line)

            # Convert reaction summaries
            line = re.sub(r'\[Reactions: ([^\]]+)\]', r'*(Reactions: \1)*', line)

            # Convert media info
            line = re.sub(r'\[Media: ([^\]]+)\]', r'*(Media: \1)*', line)

            # Convert links info
            line = re.sub(r'\[Links: ([^\]]+)\]', r'*(Links: \1)*', line)

            # Handle empty lines
            if not line.strip():
                formatted_lines.append('')
                continue

            formatted_lines.append(line)

        # Join and clean up
        result = '\n'.join(formatted_lines)

        # Remove excessive empty lines
        result = re.sub(r'\n\n\n+', '\n\n', result)

        return result.strip()

