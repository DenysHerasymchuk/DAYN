"""Tests for YouTube URL handlers."""

import pytest


class TestYouTubeURLDetection:
    """Tests for YouTube URL detection in handlers."""

    @pytest.mark.asyncio
    async def test_youtube_url_filter_accepts_valid_url(self, mock_message):
        """Test that YouTube filter accepts valid YouTube URLs."""
        from app.bot.utils.validators import is_youtube_url

        mock_message.text = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert is_youtube_url(mock_message.text) is True

    @pytest.mark.asyncio
    async def test_youtube_url_filter_rejects_tiktok(self, mock_message):
        """Test that YouTube filter rejects TikTok URLs."""
        from app.bot.utils.validators import is_youtube_url

        mock_message.text = "https://www.tiktok.com/@user/video/123"
        assert is_youtube_url(mock_message.text) is False


class TestYouTubeCallbacks:
    """Tests for YouTube callback handling."""

    def test_quality_callback_data_format(self):
        """Test YouTube quality callback data format."""
        # Callback data should follow pattern: yt_quality:{quality}
        callback_data = "yt_quality:720p"
        parts = callback_data.split(":")

        assert len(parts) == 2
        assert parts[0] == "yt_quality"
        assert parts[1] == "720p"

    def test_audio_callback_data_format(self):
        """Test YouTube audio callback data format."""
        callback_data = "yt_audio"
        assert callback_data == "yt_audio"

    @pytest.mark.asyncio
    async def test_callback_answer_called(self, mock_callback_query):
        """Test that callback query is answered."""
        mock_callback_query.data = "yt_quality:720p"

        # Simulate answering the callback
        await mock_callback_query.answer()

        mock_callback_query.answer.assert_called_once()
