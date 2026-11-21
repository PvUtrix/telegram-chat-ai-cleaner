"""
Pytest configuration and fixtures
"""
import sys
import pytest
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Mock optional dependencies that might not be available during testing
sys.modules['google.generativeai'] = __import__('unittest.mock').mock.MagicMock()
sys.modules['anthropic'] = __import__('unittest.mock').mock.MagicMock()
sys.modules['groq'] = __import__('unittest.mock').mock.MagicMock()
sys.modules['openai'] = __import__('unittest.mock').mock.MagicMock()
sys.modules['supabase'] = __import__('unittest.mock').mock.MagicMock()


@pytest.fixture
def sample_chat_data():
    """Sample Telegram chat data for testing"""
    return {
        "name": "Test Chat",
        "type": "personal_chat",
        "id": 123456,
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "date_unixtime": 1704110400,
                "from": "John Doe",
                "from_id": "user123",
                "text": "Hello, world!"
            },
            {
                "id": 2,
                "type": "message",
                "date": "2024-01-01T12:05:00",
                "date_unixtime": 1704110700,
                "from": "Jane Smith",
                "from_id": "user456",
                "text": "Hi there!",
                "reply_to_message_id": 1
            }
        ]
    }


@pytest.fixture
def temp_json_file(tmp_path, sample_chat_data):
    """Create a temporary JSON file with sample data"""
    import json

    json_file = tmp_path / "test_chat.json"
    json_file.write_text(json.dumps(sample_chat_data, indent=2))
    return str(json_file)
