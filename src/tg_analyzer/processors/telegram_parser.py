"""
Telegram JSON export parser

Parses Telegram Desktop JSON exports and extracts structured message data.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import chardet

from ..config.models import Message, ChatInfo, TextEntity, Reaction


logger = logging.getLogger(__name__)


class TelegramParser:
    """Parser for Telegram JSON exports"""

    def __init__(self):
        self.supported_types = {
            "message",
            "service",
            "photo",
            "video",
            "voice_message",
            "audio_file",
            "document",
            "sticker",
            "animation"
        }

    def parse_file(self, file_path: Union[str, Path]) -> ChatInfo:
        """
        Parse a Telegram JSON export file

        Args:
            file_path: Path to the JSON file

        Returns:
            ChatInfo object with parsed data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid JSON or not a Telegram export
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Detect encoding and read file
        raw_data = self._read_file_with_encoding(file_path)
        data = json.loads(raw_data)

        return self.parse_data(data, str(file_path))

    def parse_data(self, data: Dict[str, Any], source_file: str = "") -> ChatInfo:
        """
        Parse Telegram export data from dict

        Args:
            data: Parsed JSON data
            source_file: Source file path for reference

        Returns:
            ChatInfo object
        """
        if not self._is_valid_telegram_export(data):
            raise ValueError("Invalid Telegram export format")

        chat_info = ChatInfo(
            name=data.get("name", "Unknown Chat"),
            type=data.get("type", "unknown"),
            id=str(data.get("id", 0)),
            messages=[],
            source_file=source_file
        )

        messages_data = data.get("messages", [])
        for msg_data in messages_data:
            message = self._parse_message(msg_data)
            if message:
                chat_info.messages.append(message)

        logger.info(f"Parsed {len(chat_info.messages)} messages from {source_file}")
        return chat_info

    def _read_file_with_encoding(self, file_path: Path) -> str:
        """Read file with automatic encoding detection

        Raises:
            IOError: If file cannot be read
            ValueError: If no valid encoding can be found
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
        except IOError as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise IOError(f"Cannot read file {file_path}: {str(e)}") from e

        if not raw_data:
            raise ValueError(f"File {file_path} is empty")

        # First try UTF-8 directly (most common for JSON files)
        try:
            return raw_data.decode('utf-8')
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decode failed for {file_path}, trying to detect encoding")

            # If UTF-8 fails, try to detect encoding
            try:
                detected = chardet.detect(raw_data)
                encoding = detected.get('encoding', 'utf-8')
                confidence = detected.get('confidence', 0)

                logger.info(f"Detected encoding: {encoding} (confidence: {confidence})")

                if confidence < 0.7:
                    logger.warning(f"Low confidence ({confidence}) in detected encoding {encoding}")

                # Try detected encoding
                return raw_data.decode(encoding)
            except (UnicodeDecodeError, AttributeError, TypeError) as e:
                logger.error(f"Failed to decode with detected encoding: {e}")

                # Final fallback with error replacement
                logger.warning("Using UTF-8 with error replacement as last resort")
                return raw_data.decode('utf-8', errors='replace')

    def _is_valid_telegram_export(self, data: Dict[str, Any]) -> bool:
        """Check if data is a valid Telegram export"""
        required_keys = {"name", "type", "id", "messages"}

        # Check for required top-level keys
        if not all(key in data for key in required_keys):
            return False

        # Check if messages is a list
        if not isinstance(data.get("messages"), list):
            return False

        # Check if we have at least some messages
        messages = data.get("messages", [])
        if len(messages) == 0:
            return False

        # Check if first message has expected structure
        first_msg = messages[0]
        if not isinstance(first_msg, dict) or "id" not in first_msg:
            return False

        return True

    def _parse_message(self, msg_data: Dict[str, Any]) -> Optional[Message]:
        """Parse individual message data"""
        try:
            # Skip unsupported message types
            msg_type = msg_data.get("type", "")
            if msg_type not in self.supported_types:
                logger.debug(f"Skipping unsupported message type: {msg_type}")
                return None

            # Parse basic message info
            message = Message(
                id=msg_data.get("id"),
                type=msg_type,
                date=self._parse_date(msg_data.get("date")),
                date_unixtime=msg_data.get("date_unixtime"),
                edited=self._parse_date(msg_data.get("edited")),
                edited_unixtime=msg_data.get("edited_unixtime"),
                from_user=msg_data.get("from"),
                from_id=msg_data.get("from_id"),
                reply_to_message_id=msg_data.get("reply_to_message_id"),
                text=self._parse_text(msg_data),
                text_entities=self._parse_text_entities(msg_data.get("text_entities", [])),
                reactions=self._parse_reactions(msg_data.get("reactions", [])),
                forwarded_from=msg_data.get("forwarded_from"),
                via_bot=msg_data.get("via_bot"),
                media_type=msg_data.get("media_type"),
                mime_type=msg_data.get("mime_type"),
                duration_seconds=msg_data.get("duration_seconds"),
                width=msg_data.get("width"),
                height=msg_data.get("height"),
                file=msg_data.get("file"),
                file_name=msg_data.get("file_name"),
                file_size=msg_data.get("file_size"),
                thumbnail=msg_data.get("thumbnail"),
                thumbnail_file_size=msg_data.get("thumbnail_file_size"),
                photo=msg_data.get("photo"),
                contact_information=msg_data.get("contact_information"),
                contact_vcard=msg_data.get("contact_vcard"),
                location_information=msg_data.get("location_information"),
                live_location_period_seconds=msg_data.get("live_location_period_seconds"),
                live_location_last_update_date=self._parse_date(msg_data.get("live_location_last_update_date")),
                live_location_last_update_date_unixtime=msg_data.get("live_location_last_update_date_unixtime"),
                poll=msg_data.get("poll"),
                performer=msg_data.get("performer"),
                title=msg_data.get("title")
            )

            return message

        except Exception as e:
            logger.warning(f"Failed to parse message {msg_data.get('id')}: {e}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None

        try:
            # Telegram format: "2025-08-22T00:48:13"
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Failed to parse date: {date_str}")
            return None

    def _parse_text(self, msg_data: Dict[str, Any]) -> str:
        """Extract text content from message"""
        text = msg_data.get("text", "")

        # Handle complex text structures (arrays with links)
        if isinstance(text, list):
            # Extract plain text parts
            plain_parts = []
            for part in text:
                if isinstance(part, str):
                    plain_parts.append(part)
                elif isinstance(part, dict) and "text" in part:
                    plain_parts.append(part["text"])
            text = "".join(plain_parts)

        return str(text)

    def _parse_text_entities(self, entities_data: List[Dict[str, Any]]) -> List[TextEntity]:
        """Parse text entities (links, mentions, etc.)"""
        entities = []

        for entity_data in entities_data:
            try:
                entity = TextEntity(
                    type=entity_data.get("type", "plain"),
                    text=entity_data.get("text", ""),
                    href=entity_data.get("href"),
                    user_id=entity_data.get("user_id")
                )
                entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to parse text entity: {e}")

        return entities

    def _parse_reactions(self, reactions_data: List[Dict[str, Any]]) -> List[Reaction]:
        """Parse message reactions"""
        reactions = []

        for reaction_data in reactions_data:
            try:
                reaction = Reaction(
                    type=reaction_data.get("type", "emoji"),
                    emoji=reaction_data.get("emoji"),
                    count=reaction_data.get("count", 0),
                    recent=self._parse_recent_reactions(reaction_data.get("recent", []))
                )
                reactions.append(reaction)
            except Exception as e:
                logger.warning(f"Failed to parse reaction: {e}")

        return reactions

    def _parse_recent_reactions(self, recent_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse recent reaction data"""
        recent = []

        for recent_item in recent_data:
            try:
                recent.append({
                    "from": recent_item.get("from"),
                    "from_id": recent_item.get("from_id"),
                    "date": self._parse_date(recent_item.get("date"))
                })
            except Exception as e:
                logger.warning(f"Failed to parse recent reaction: {e}")

        return recent

