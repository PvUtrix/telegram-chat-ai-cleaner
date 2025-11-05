"""
Tests for privacy cleaner functionality
"""

from src.tg_analyzer.processors.cleaners.privacy_cleaner import PrivacyCleaner
from src.tg_analyzer.config.models import ChatInfo, Message
from datetime import datetime


class TestPrivacyCleaner:
    """Test suite for PrivacyCleaner class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.cleaner = PrivacyCleaner(level=2)

        # Create sample chat data
        self.chat_info = ChatInfo(
            name="Test Chat",
            type="personal_chat",
            id="123456",
            messages=[
                Message(
                    id=1,
                    type="message",
                    date=datetime(2024, 1, 1, 12, 0, 0),
                    from_user="John Doe",
                    from_id="user123",
                    text="Hello, this is a test message"
                ),
                Message(
                    id=2,
                    type="message",
                    date=datetime(2024, 1, 1, 12, 5, 0),
                    from_user="Jane Smith",
                    from_id="user456",
                    text="Reply to the test message",
                    reply_to_message_id=1
                )
            ]
        )

    def test_cleaner_initialization(self):
        """Test cleaner initializes correctly"""
        assert self.cleaner.approach == "privacy"
        assert self.cleaner.level == 2
        assert isinstance(self.cleaner.user_mapping, dict)

    def test_anonymize_user_id(self):
        """Test user ID anonymization"""
        user_id = "user123"
        anonymized = self.cleaner._anonymize_user_id(user_id)

        # Should return consistent anonymized ID
        assert anonymized.startswith("User_")
        assert len(anonymized) > 5

        # Should be consistent for same input
        anonymized2 = self.cleaner._anonymize_user_id(user_id)
        assert anonymized == anonymized2

        # Should be different for different inputs
        anonymized3 = self.cleaner._anonymize_user_id("user456")
        assert anonymized != anonymized3

    def test_anonymize_empty_user_id(self):
        """Test anonymization of empty user ID"""
        result = self.cleaner._anonymize_user_id("")
        assert result == "Anonymous"

    def test_clean_chat_info(self):
        """Test cleaning chat info"""
        result = self.cleaner.clean(self.chat_info)

        assert isinstance(result, str)
        assert "Test Chat" in result
        assert "Hello, this is a test message" in result

    def test_format_reactions_summary(self):
        """Test reaction formatting"""
        reactions = [
            {"emoji": "👍", "count": 5},
            {"emoji": "❤️", "count": 2}
        ]
        result = self.cleaner._format_reactions_summary(reactions)

        assert "👍(5)" in result
        assert "❤️(2)" in result

    def test_format_reactions_summary_empty(self):
        """Test reaction formatting with empty list"""
        result = self.cleaner._format_reactions_summary([])
        assert result == ""

    def test_format_media_info(self):
        """Test media info formatting"""
        message = {
            "media_type": "video_file",
            "duration_seconds": 30
        }
        result = self.cleaner._format_media_info(message)
        assert result == "Video (30s)"

    def test_format_media_info_photo(self):
        """Test photo media formatting"""
        message = {"media_type": "photo"}
        result = self.cleaner._format_media_info(message)
        assert result == "Photo"

    def test_format_media_info_no_media(self):
        """Test formatting when no media present"""
        message = {}
        result = self.cleaner._format_media_info(message)
        assert result == ""
