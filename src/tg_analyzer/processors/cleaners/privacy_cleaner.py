"""
Privacy-focused cleaning strategies

These cleaners prioritize user privacy by anonymizing or removing identifying information.
"""

import hashlib
from typing import Dict, Any, List
from ..telegram_parser import ChatInfo
from .base_cleaner import BaseCleaner
from ...constants import REPLY_TEXT_PREVIEW_LENGTH, ANONYMIZED_USER_ID_LENGTH


class PrivacyCleaner(BaseCleaner):
    """Privacy-focused cleaner that anonymizes user data"""

    def __init__(self, level: int):
        super().__init__("privacy", level)
        self.user_mapping = {}  # Maps real user IDs to anonymized IDs

    def clean(self, chat_info: ChatInfo) -> str:
        """
        Clean chat data with privacy focus

        Level 1: Names + content only, anonymize user IDs
        Level 2: + timestamps + reply structure
        Level 3: + all metadata, keep user identifiers
        """
        lines = []

        # Add chat header
        lines.append(f"Chat: {chat_info.name}")
        lines.append(f"Type: {chat_info.type}")
        lines.append("=" * 50)
        lines.append("")

        # Create message dictionary for reply resolution
        messages_dict = {msg.id: msg.model_dump() for msg in chat_info.messages}

        for message in chat_info.messages:
            msg_dict = message.model_dump()

            if self.level == 1:
                # Basic: Names + content only, anonymize user IDs
                cleaned_msg = self._clean_level_1(msg_dict)
            elif self.level == 2:
                # Medium: + timestamps + reply structure
                cleaned_msg = self._clean_level_2(msg_dict, messages_dict)
            elif self.level == 3:
                # Full: + all metadata, keep user identifiers
                cleaned_msg = self._clean_level_3(msg_dict, messages_dict)
            else:
                continue

            if cleaned_msg.strip():
                lines.append(cleaned_msg)
                lines.append("")  # Empty line between messages

        return "\n".join(lines)

    def _clean_level_1(self, message: Dict[str, Any]) -> str:
        """Level 1: Names + content only, anonymize user IDs"""
        # Skip non-message types
        if message.get("type") != "message":
            return ""

        # Anonymize user identifier
        user_id = message.get("from_id")
        if user_id:
            anonymized_id = self._anonymize_user_id(user_id)
        else:
            anonymized_id = "Anonymous"

        user_name = message.get("from_user", anonymized_id)

        # Only include text content
        text = message.get("text", "").strip()
        if not text:
            return ""

        return f"{user_name}: {text}"

    def _clean_level_2(self, message: Dict[str, Any], messages_dict: Dict[int, Dict[str, Any]]) -> str:
        """Level 2: + timestamps + reply structure"""
        # Skip non-message types
        if message.get("type") != "message":
            return ""

        parts = []

        # Add timestamp
        if message.get("date"):
            timestamp = message["date"].strftime("%Y-%m-%d %H:%M")
            parts.append(f"[{timestamp}]")

        # Add reply context
        if message.get("reply_to_message_id") and message["reply_to_message_id"] in messages_dict:
            reply_to = messages_dict[message["reply_to_message_id"]]
            reply_sender = reply_to.get("from_user") or self._anonymize_user_id(reply_to.get("from_id", ""))
            reply_text = reply_to.get("text", "")[:REPLY_TEXT_PREVIEW_LENGTH]  # Truncate for preview
            if reply_text:
                parts.append(f"[Reply to {reply_sender}: {reply_text}...]")

        # Add sender (anonymized)
        user_id = message.get("from_id")
        if user_id:
            anonymized_id = self._anonymize_user_id(user_id)
        else:
            anonymized_id = "Anonymous"

        user_name = message.get("from_user", anonymized_id)
        parts.append(f"{user_name}:")

        # Add text content
        text = message.get("text", "").strip()
        if text:
            parts.append(text)

        return " ".join(parts)

    def _clean_level_3(self, message: Dict[str, Any], messages_dict: Dict[int, Dict[str, Any]]) -> str:
        """Level 3: + all metadata, keep user identifiers"""
        # Skip non-message types except service messages
        msg_type = message.get("type", "")
        if msg_type not in ["message", "service"]:
            return ""

        parts = []

        # Add timestamp
        if message.get("date"):
            timestamp = message["date"].strftime("%Y-%m-%d %H:%M:%S")
            parts.append(f"[{timestamp}]")

        # Add message ID
        parts.append(f"ID:{message.get('id', 'unknown')}")

        # Add reply context
        if message.get("reply_to_message_id") and message["reply_to_message_id"] in messages_dict:
            reply_id = message["reply_to_message_id"]
            parts.append(f"[Reply to ID:{reply_id}]")

        # Add sender (keep original identifiers)
        user_name = message.get("from_user", "")
        user_id = message.get("from_id", "")
        if user_name and user_id:
            parts.append(f"{user_name} ({user_id}):")
        elif user_name:
            parts.append(f"{user_name}:")
        elif user_id:
            parts.append(f"{user_id}:")
        else:
            parts.append("Unknown:")

        # Add edited indicator
        if message.get("edited"):
            parts.append("[EDITED]")

        # Add forwarded indicator
        if message.get("forwarded_from"):
            parts.append(f"[Forwarded from: {message['forwarded_from']}]")

        # Add text content
        text = message.get("text", "").strip()
        if text:
            parts.append(text)

        # Add reactions summary
        reactions = message.get("reactions", [])
        if reactions:
            reaction_summary = self._format_reactions_summary(reactions)
            if reaction_summary:
                parts.append(f"[Reactions: {reaction_summary}]")

        # Add media info
        media_info = self._format_media_info(message)
        if media_info:
            parts.append(f"[Media: {media_info}]")

        return " ".join(parts)

    def _anonymize_user_id(self, user_id: str) -> str:
        """Create anonymized user identifier using secure SHA-256 hashing"""
        if not user_id:
            return "Anonymous"

        if user_id not in self.user_mapping:
            # Create hash-based anonymized ID using SHA-256 for security
            hash_obj = hashlib.sha256(user_id.encode())
            short_hash = hash_obj.hexdigest()[:ANONYMIZED_USER_ID_LENGTH]
            self.user_mapping[user_id] = f"User_{short_hash}"

        return self.user_mapping[user_id]

    def _format_reactions_summary(self, reactions: List[Dict[str, Any]]) -> str:
        """Format reactions into a summary string"""
        if not reactions:
            return ""

        summaries = []
        for reaction in reactions:
            emoji = reaction.get("emoji", "")
            count = reaction.get("count", 0)
            if emoji and count > 0:
                summaries.append(f"{emoji}({count})")

        return " ".join(summaries)

    def _format_media_info(self, message: Dict[str, Any]) -> str:
        """Format media information"""
        media_type = message.get("media_type")
        if not media_type:
            return ""

        if media_type == "video_file":
            duration = message.get("duration_seconds")
            if duration:
                return f"Video ({duration}s)"
            return "Video"
        elif media_type == "photo":
            return "Photo"
        elif media_type == "voice_message":
            duration = message.get("duration_seconds")
            if duration:
                return f"Voice message ({duration}s)"
            return "Voice message"
        elif media_type == "document":
            file_name = message.get("file_name", "")
            if file_name:
                return f"Document: {file_name}"
            return "Document"
        elif media_type == "audio_file":
            title = message.get("title", "")
            performer = message.get("performer", "")
            if title and performer:
                return f"Audio: {performer} - {title}"
            elif title:
                return f"Audio: {title}"
            return "Audio"

        return media_type

