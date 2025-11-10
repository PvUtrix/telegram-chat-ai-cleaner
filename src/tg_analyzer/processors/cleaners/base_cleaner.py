"""
Base cleaner class and factory functions
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..telegram_parser import ChatInfo


class BaseCleaner(ABC):
    """Abstract base class for all cleaning strategies"""

    def __init__(self, approach: str, level: int):
        """
        Initialize cleaner

        Args:
            approach: Cleaning approach (privacy, size, context)
            level: Cleaning level (1, 2, 3)
        """
        self.approach = approach
        self.level = level

    @abstractmethod
    def clean(self, chat_info: ChatInfo) -> str:
        """
        Clean the chat data

        Args:
            chat_info: Parsed chat information

        Returns:
            Cleaned text representation
        """
        pass

    def _format_message_basic(self, message: Dict[str, Any]) -> str:
        """Format a single message with basic information"""
        parts = []

        # Add timestamp if available
        if message.get("date"):
            parts.append(f"[{message['date'].strftime('%Y-%m-%d %H:%M:%S')}]")

        # Add sender if available
        if message.get("from_user"):
            parts.append(f"{message['from_user']}:")
        elif message.get("from_id"):
            parts.append(f"{message['from_id']}:")

        # Add text content
        if message.get("text"):
            parts.append(message["text"])

        return " ".join(parts) if parts else ""

    def _format_message_with_reply(
        self, message: Dict[str, Any], messages_dict: Dict[int, Dict[str, Any]]
    ) -> str:
        """Format message with reply context"""
        parts = []

        # Add reply indicator
        if (
            message.get("reply_to_message_id")
            and message["reply_to_message_id"] in messages_dict
        ):
            reply_to = messages_dict[message["reply_to_message_id"]]
            reply_sender = (
                reply_to.get("from_user") or reply_to.get("from_id") or "Unknown"
            )
            reply_text = reply_to.get("text", "")[:100]  # Truncate long replies
            if reply_text:
                parts.append(f"[Replying to {reply_sender}: {reply_text}]")

        # Add basic message
        basic_msg = self._format_message_basic(message)
        if basic_msg:
            parts.append(basic_msg)

        return "\n".join(parts) if parts else ""


def get_cleaner(approach: str, level: int) -> BaseCleaner:
    """
    Factory function to get the appropriate cleaner

    Args:
        approach: Cleaning approach (privacy, size, context)
        level: Cleaning level (1, 2, 3)

    Returns:
        Appropriate cleaner instance

    Raises:
        ValueError: If approach or level is invalid
    """
    if approach not in ["privacy", "size", "context"]:
        raise ValueError(
            f"Invalid approach: {approach}. Must be 'privacy', 'size', or 'context'"
        )

    if level not in [1, 2, 3]:
        raise ValueError(f"Invalid level: {level}. Must be 1, 2, or 3")

    # Import here to avoid circular imports
    if approach == "privacy":
        from .privacy_cleaner import PrivacyCleaner

        return PrivacyCleaner(level)
    elif approach == "size":
        from .size_cleaner import SizeCleaner

        return SizeCleaner(level)
    elif approach == "context":
        from .context_cleaner import ContextCleaner

        return ContextCleaner(level)

    raise ValueError(f"Unknown cleaner approach: {approach}")
