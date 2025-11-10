"""
Size-focused cleaning strategies

These cleaners prioritize reducing output size by filtering out less important information.
"""

from typing import Dict, Any, List
from ..telegram_parser import ChatInfo
from .base_cleaner import BaseCleaner


class SizeCleaner(BaseCleaner):
    """Size-focused cleaner that minimizes output"""

    def __init__(self, level: int):
        super().__init__("size", level)

    def clean(self, chat_info: ChatInfo) -> str:
        """
        Clean chat data with size focus

        Level 1: Text only, strip all metadata
        Level 2: + links + basic metadata (date, sender)
        Level 3: + all media references, reactions, edits
        """
        lines = []

        # Add minimal chat header for levels 2+
        if self.level >= 2:
            lines.append(f"Chat: {chat_info.name}")
            lines.append("=" * 30)
            lines.append("")

        # Create message dictionary for reply resolution (only for level 3)
        messages_dict = {}
        if self.level == 3:
            messages_dict = {msg.id: msg.model_dump() for msg in chat_info.messages}

        for message in chat_info.messages:
            msg_dict = message.model_dump()

            if self.level == 1:
                # Basic: Text only, strip all metadata
                cleaned_msg = self._clean_level_1(msg_dict)
            elif self.level == 2:
                # Medium: + links + basic metadata (date, sender)
                cleaned_msg = self._clean_level_2(msg_dict)
            elif self.level == 3:
                # Full: + all media references, reactions, edits
                cleaned_msg = self._clean_level_3(msg_dict, messages_dict)
            else:
                continue

            if cleaned_msg.strip():
                lines.append(cleaned_msg)

        return "\n".join(lines)

    def _clean_level_1(self, message: Dict[str, Any]) -> str:
        """Level 1: Text only, strip all metadata"""
        # Only include actual text messages
        if message.get("type") != "message":
            return ""

        text = message.get("text", "").strip()

        # Skip empty messages
        if not text:
            return ""

        # Skip very short messages (likely just reactions or commands)
        if len(text) < 3:
            return ""

        # Extract links and mentions for minimal context
        text_entities = message.get("text_entities", [])
        links = []
        mentions = []

        for entity in text_entities:
            entity_type = entity.get("type", "")
            entity_text = entity.get("text", "")

            if entity_type == "link":
                links.append(entity_text)
            elif entity_type in ["mention", "mention_name"]:
                mentions.append(entity_text)

        # If message is mostly links/mentions, include them
        if not text and (links or mentions):
            all_entities = links + mentions
            return " ".join(all_entities)

        # If message has significant text, include it
        if len(text) > 2:
            return text

        return ""

    def _clean_level_2(self, message: Dict[str, Any]) -> str:
        """Level 2: + links + basic metadata (date, sender)"""
        # Skip non-message types
        if message.get("type") != "message":
            return ""

        parts = []

        # Add date (compact format)
        if message.get("date"):
            date_str = message["date"].strftime("%m/%d %H:%M")
            parts.append(f"[{date_str}]")

        # Add sender (compact)
        sender = message.get("from_user") or message.get("from_id", "Unknown")
        parts.append(f"{sender}:")

        # Add text content
        text = message.get("text", "").strip()
        if text:
            parts.append(text)

        # Add important links separately
        text_entities = message.get("text_entities", [])
        important_links = []

        for entity in text_entities:
            entity_type = entity.get("type", "")
            entity_text = entity.get("text", "")

            if entity_type == "link" and any(
                domain in entity_text.lower()
                for domain in [
                    "github.com",
                    "youtube.com",
                    "twitter.com",
                    "telegram.org",
                ]
            ):
                important_links.append(entity_text)

        if important_links:
            parts.append(f"[Links: {' | '.join(important_links)}]")

        return " ".join(parts)

    def _clean_level_3(
        self, message: Dict[str, Any], messages_dict: Dict[int, Dict[str, Any]]
    ) -> str:
        """Level 3: + all media references, reactions, edits"""
        # Include more message types
        msg_type = message.get("type", "")
        if msg_type not in [
            "message",
            "photo",
            "video_file",
            "document",
            "voice_message",
        ]:
            return ""

        parts = []

        # Add timestamp
        if message.get("date"):
            timestamp = message["date"].strftime("%Y-%m-%d %H:%M")
            parts.append(f"[{timestamp}]")

        # Add edited indicator
        if message.get("edited"):
            parts.append("[EDITED]")

        # Add reply indicator (compact)
        if (
            message.get("reply_to_message_id")
            and message["reply_to_message_id"] in messages_dict
        ):
            parts.append("[REPLY]")

        # Add sender
        sender = message.get("from_user") or message.get("from_id", "Unknown")
        parts.append(f"{sender}:")

        # Add text content
        text = message.get("text", "").strip()
        if text:
            parts.append(text)

        # Add media information
        media_info = self._get_media_description(message)
        if media_info:
            parts.append(f"[{media_info}]")

        # Add reactions (compact format)
        reactions = message.get("reactions", [])
        if reactions:
            top_reactions = self._get_top_reactions(reactions, limit=3)
            if top_reactions:
                parts.append(f"[{top_reactions}]")

        # Add all links and entities
        entities_info = self._get_entities_info(message)
        if entities_info:
            parts.append(f"[{entities_info}]")

        return " ".join(parts)

    def _get_media_description(self, message: Dict[str, Any]) -> str:
        """Get compact media description"""
        media_type = message.get("media_type")
        if not media_type:
            return ""

        descriptions = {
            "photo": "📷",
            "video_file": "🎥",
            "voice_message": "🎤",
            "audio_file": "🎵",
            "document": "📄",
            "sticker": "🎭",
            "animation": "🎬",
        }

        desc = descriptions.get(media_type, media_type)

        # Add size/duration info where relevant
        if media_type in ["video_file", "voice_message", "audio_file"]:
            duration = message.get("duration_seconds")
            if duration:
                desc += f" {duration}s"

        if media_type == "document":
            file_name = message.get("file_name", "")
            if file_name:
                # Truncate long filenames
                if len(file_name) > 20:
                    file_name = file_name[:17] + "..."
                desc += f" {file_name}"

        return desc

    def _get_top_reactions(
        self, reactions: List[Dict[str, Any]], limit: int = 3
    ) -> str:
        """Get top reactions as compact string"""
        if not reactions:
            return ""

        # Sort by count
        sorted_reactions = sorted(
            reactions, key=lambda r: r.get("count", 0), reverse=True
        )

        top_reactions = []
        for reaction in sorted_reactions[:limit]:
            emoji = reaction.get("emoji", "")
            count = reaction.get("count", 0)
            if emoji and count > 0:
                top_reactions.append(f"{emoji}{count}")

        return " ".join(top_reactions)

    def _get_entities_info(self, message: Dict[str, Any]) -> str:
        """Get information about text entities"""
        text_entities = message.get("text_entities", [])
        if not text_entities:
            return ""

        entity_counts = {}
        links = []

        for entity in text_entities:
            entity_type = entity.get("type", "")
            entity_text = entity.get("text", "")

            if entity_type == "link":
                links.append(entity_text)
            else:
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

        parts = []

        # Add link count
        if links:
            parts.append(f"{len(links)} links")

        # Add other entity counts
        for entity_type, count in entity_counts.items():
            if count > 0:
                parts.append(f"{count} {entity_type}")

        return ", ".join(parts)
