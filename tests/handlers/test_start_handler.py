"""Tests for start and help handlers."""
from unittest.mock import patch

import pytest


class TestStartHandler:
    """Tests for /start command handler."""

    @pytest.mark.asyncio
    async def test_start_sends_welcome_message(self, mock_message):
        """Test that /start sends a welcome message."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.bot.handlers.common.start import start_handler

            await start_handler(mock_message)

            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            message_text = call_args[0][0]

            assert "Video Downloader Bot" in message_text
            assert "YouTube" in message_text
            assert "TikTok" in message_text

    @pytest.mark.asyncio
    async def test_start_uses_html_parse_mode(self, mock_message):
        """Test that /start uses HTML parse mode."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.bot.handlers.common.start import start_handler

            await start_handler(mock_message)

            call_kwargs = mock_message.answer.call_args[1]
            assert call_kwargs.get("parse_mode") == "HTML"

    @pytest.mark.asyncio
    async def test_start_shows_file_size_limit(self, mock_message):
        """Test that /start shows file size limit."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.bot.handlers.common.start import start_handler

            await start_handler(mock_message)

            call_args = mock_message.answer.call_args
            message_text = call_args[0][0]

            assert "50MB" in message_text


class TestHelpHandler:
    """Tests for /help command handler."""

    @pytest.mark.asyncio
    async def test_help_sends_help_message(self, mock_message):
        """Test that /help sends help information."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.bot.handlers.common.start import help_handler

            await help_handler(mock_message)

            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            message_text = call_args[0][0]

            assert "How to use" in message_text

    @pytest.mark.asyncio
    async def test_help_uses_html_parse_mode(self, mock_message):
        """Test that /help uses HTML parse mode."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.bot.handlers.common.start import help_handler

            await help_handler(mock_message)

            call_kwargs = mock_message.answer.call_args[1]
            assert call_kwargs.get("parse_mode") == "HTML"

    @pytest.mark.asyncio
    async def test_help_mentions_supported_platforms(self, mock_message):
        """Test that /help mentions supported platforms."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.bot.handlers.common.start import help_handler

            await help_handler(mock_message)

            call_args = mock_message.answer.call_args
            message_text = call_args[0][0]

            assert "YouTube" in message_text
            assert "TikTok" in message_text
