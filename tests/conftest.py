"""Shared test fixtures for DAYN bot tests."""
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

# Set test environment before importing app modules
os.environ["BOT_TOKEN"] = "test_token_12345"


@pytest.fixture
def mock_message():
    """Create a mock Telegram message."""
    message = AsyncMock()
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.chat = MagicMock()
    message.chat.id = 12345
    message.chat.type = "private"
    message.text = ""
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    message.edit_text = AsyncMock()
    message.delete = AsyncMock()
    return message


@pytest.fixture
def mock_bot():
    """Create a mock Telegram bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_video = AsyncMock()
    bot.send_audio = AsyncMock()
    bot.send_document = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.delete_message = AsyncMock()
    return bot


@pytest.fixture
def mock_callback_query():
    """Create a mock callback query for inline keyboard interactions."""
    callback = AsyncMock()
    callback.from_user = MagicMock()
    callback.from_user.id = 12345
    callback.from_user.username = "testuser"
    callback.message = AsyncMock()
    callback.message.chat = MagicMock()
    callback.message.chat.id = 12345
    callback.message.edit_text = AsyncMock()
    callback.message.delete = AsyncMock()
    callback.data = ""
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def mock_state():
    """Create a mock FSM state."""
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.set_data = AsyncMock()
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for file operations."""
    return tmp_path


@pytest.fixture
def sample_video_info():
    """Sample YouTube video info for testing."""
    return {
        "title": "Test Video Title",
        "author": "Test Channel",
        "duration": 180,
        "thumbnail": "https://example.com/thumb.jpg",
        "formats": [
            {"quality": "360p", "filesize": 10_000_000},
            {"quality": "720p", "filesize": 25_000_000},
            {"quality": "1080p", "filesize": 45_000_000},
        ]
    }


@pytest.fixture
def sample_tiktok_info():
    """Sample TikTok video info for testing."""
    return {
        "title": "TikTok Video",
        "author": "@testuser",
        "duration": 30,
        "thumbnail": "https://example.com/tiktok_thumb.jpg",
    }
