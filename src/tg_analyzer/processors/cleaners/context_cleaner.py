"""
Context-focused cleaning strategies

These cleaners prioritize conversation context and relationships between messages.
"""

from typing import Dict, Any, List, Set
from collections import defaultdict
from ..telegram_parser import ChatInfo
from .base_cleaner import BaseCleaner


class ContextCleaner(BaseCleaner):
    """Context-focused cleaner that preserves conversation flow"""

    def __init__(self, level: int):
        super().__init__("context", level)

    def clean(self, chat_info: ChatInfo) -> str:
        """
        Clean chat data with context focus

        Level 1: Flat message list (chronological)
        Level 2: + reply chains, threaded structure
        Level 3: + reactions + full conversation graph
        """
        lines = []

        # Add chat header
        lines.append(f"Chat: {chat_info.name}")
        lines.append(f"Type: {chat_info.type}")
        lines.append("=" * 50)
        lines.append("")

        messages = [msg.model_dump() for msg in chat_info.messages]

        if self.level == 1:
            # Basic: Flat message list (chronological)
            cleaned_messages = self._clean_level_1(messages)
        elif self.level == 2:
            # Medium: + reply chains, threaded structure
            cleaned_messages = self._clean_level_2(messages)
        elif self.level == 3:
            # Full: + reactions + full conversation graph
            cleaned_messages = self._clean_level_3(messages)
        else:
            cleaned_messages = []

        lines.extend(cleaned_messages)
        return "\n".join(lines)

    def _clean_level_1(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Level 1: Flat message list (chronological)"""
        lines = []

        for message in messages:
            # Skip non-message types
            if message.get("type") != "message":
                continue

            # Format basic message
            formatted = self._format_basic_message(message)
            if formatted:
                lines.append(formatted)
                lines.append("")  # Spacing

        return lines

    def _clean_level_2(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Level 2: + reply chains, threaded structure"""
        lines = []

        # Create message lookup
        msg_lookup = {msg["id"]: msg for msg in messages}

        # Track processed messages to avoid duplicates
        processed = set()

        for message in messages:
            if message["id"] in processed:
                continue

            # Process reply chain
            chain_lines = self._process_reply_chain(message, msg_lookup, processed)
            lines.extend(chain_lines)

            # Add separator between chains
            if chain_lines:
                lines.append("")

        return lines

    def _clean_level_3(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Level 3: + reactions + full conversation graph"""
        lines = []

        # Create message lookup and build conversation graph
        msg_lookup = {msg["id"]: msg for msg in messages}
        conversation_graph = self._build_conversation_graph(messages)

        # Find root messages (no replies)
        root_messages = [msg for msg in messages if not msg.get("reply_to_message_id")]

        # Process each conversation thread
        for root_msg in root_messages:
            thread_lines = self._process_conversation_thread(
                root_msg, msg_lookup, conversation_graph
            )
            lines.extend(thread_lines)
            lines.append("")  # Thread separator

        return lines

    def _format_basic_message(self, message: Dict[str, Any]) -> str:
        """Format a basic message"""
        parts = []

        # Add timestamp
        if message.get("date"):
            timestamp = message["date"].strftime("%Y-%m-%d %H:%M:%S")
            parts.append(f"[{timestamp}]")

        # Add sender
        sender = message.get("from_user") or message.get("from_id", "Unknown")
        parts.append(f"{sender}:")

        # Add text
        text = message.get("text", "").strip()
        if text:
            parts.append(text)

        return " ".join(parts)

    def _process_reply_chain(
        self,
        start_message: Dict[str, Any],
        msg_lookup: Dict[int, Dict[str, Any]],
        processed: Set[int],
    ) -> List[str]:
        """Process a chain of replies"""
        lines = []
        current_msg = start_message
        chain_messages = []

        # Collect the chain
        while current_msg:
            if current_msg["id"] in processed:
                break

            chain_messages.append(current_msg)
            processed.add(current_msg["id"])

            reply_to_id = current_msg.get("reply_to_message_id")
            if reply_to_id and reply_to_id in msg_lookup:
                current_msg = msg_lookup[reply_to_id]
            else:
                break

        # Reverse to show chronological order (oldest first)
        chain_messages.reverse()

        # Format the chain
        for i, message in enumerate(chain_messages):
            if message.get("type") != "message":
                continue

            indent = "  " * i  # Indent replies

            formatted = self._format_basic_message(message)
            if formatted:
                lines.append(f"{indent}{formatted}")

        return lines

    def _build_conversation_graph(
        self, messages: List[Dict[str, Any]]
    ) -> Dict[int, List[int]]:
        """Build a graph of message relationships"""
        graph = defaultdict(list)

        for message in messages:
            reply_to = message.get("reply_to_message_id")
            if reply_to:
                graph[reply_to].append(message["id"])

        return dict(graph)

    def _process_conversation_thread(
        self,
        root_message: Dict[str, Any],
        msg_lookup: Dict[int, Dict[str, Any]],
        conversation_graph: Dict[int, List[int]],
    ) -> List[str]:
        """Process a conversation thread with full context"""
        lines = []

        def process_message(msg_id: int, depth: int = 0) -> None:
            if msg_id not in msg_lookup:
                return

            message = msg_lookup[msg_id]
            if message.get("type") != "message":
                return

            # Format message with context
            formatted = self._format_context_message(message, depth)
            if formatted:
                lines.append(formatted)

            # Process replies
            replies = conversation_graph.get(msg_id, [])
            for reply_id in sorted(replies):  # Sort by ID for consistency
                process_message(reply_id, depth + 1)

        # Start with root message
        process_message(root_message["id"])

        return lines

    def _format_context_message(self, message: Dict[str, Any], depth: int = 0) -> str:
        """Format message with full context information"""
        parts = []
        indent = "  " * depth

        # Add timestamp
        if message.get("date"):
            timestamp = message["date"].strftime("%Y-%m-%d %H:%M:%S")
            parts.append(f"[{timestamp}]")

        # Add message ID
        parts.append(f"#{message.get('id', 'unknown')}")

        # Add edited indicator
        if message.get("edited"):
            parts.append("[EDITED]")

        # Add sender
        sender = message.get("from_user") or message.get("from_id", "Unknown")
        parts.append(f"{sender}:")

        # Add text
        text = message.get("text", "").strip()
        if text:
            parts.append(text)

        # Add reactions
        reactions = message.get("reactions", [])
        if reactions:
            reaction_str = self._format_reactions(reactions)
            parts.append(f"[Reactions: {reaction_str}]")

        # Add media info
        media_info = self._get_media_context(message)
        if media_info:
            parts.append(f"[Media: {media_info}]")

        # Add forwarded info
        if message.get("forwarded_from"):
            parts.append(f"[Forwarded from: {message['forwarded_from']}]")

        return f"{indent}{' '.join(parts)}"

    def _format_reactions(self, reactions: List[Dict[str, Any]]) -> str:
        """Format reactions for context display"""
        if not reactions:
            return ""

        reaction_parts = []
        for reaction in reactions:
            emoji = reaction.get("emoji", "")
            count = reaction.get("count", 0)
            if emoji and count > 0:
                reaction_parts.append(f"{emoji}×{count}")

        return ", ".join(reaction_parts)

    def _get_media_context(self, message: Dict[str, Any]) -> str:
        """Get media information with context"""
        media_type = message.get("media_type")
        if not media_type:
            return ""

        context_parts = [media_type]

        # Add file name if available
        if message.get("file_name"):
            context_parts.append(f"'{message['file_name']}'")

        # Add duration for media
        duration = message.get("duration_seconds")
        if duration:
            context_parts.append(f"{duration}s")

        # Add dimensions for images/videos
        width = message.get("width")
        height = message.get("height")
        if width and height:
            context_parts.append(f"{width}×{height}")

        return " ".join(context_parts)
