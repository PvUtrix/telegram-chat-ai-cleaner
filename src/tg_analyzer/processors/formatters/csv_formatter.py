"""
CSV formatter for spreadsheet-compatible output
"""

import csv
import io
from .base_formatter import BaseFormatter


class CSVFormatter(BaseFormatter):
    """Formats cleaned data as CSV"""

    def __init__(self):
        super().__init__("csv")

    def format(self, cleaned_data: str) -> str:
        """
        Format cleaned data as CSV

        Note: This is a basic implementation that creates a simple
        timestamp,sender,message format. For more complex CSV output,
        additional parsing would be needed.

        Args:
            cleaned_data: Cleaned text data

        Returns:
            CSV formatted output
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["timestamp", "sender", "message"])

        # Parse lines and extract basic information
        lines = cleaned_data.strip().split("\n")

        for line in lines:
            line = line.strip()
            if (
                not line
                or line.startswith("Chat:")
                or line.startswith("=")
                or line.startswith("Type:")
            ):
                continue

            # Try to parse basic format: [timestamp] sender: message
            import re

            match = re.match(r"(?:\[([^\]]+)\]\s*)?([^:]+):\s*(.+)", line)
            if match:
                timestamp = match.group(1) or ""
                sender = match.group(2).strip()
                message = match.group(3).strip()
                writer.writerow([timestamp, sender, message])
            else:
                # If parsing fails, put everything in message column
                writer.writerow(["", "", line])

        return output.getvalue()
