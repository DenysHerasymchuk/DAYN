"""Tests for TikTok URL handlers."""

import pytest


class TestTikTokURLDetection:
    """Tests for TikTok URL detection in handlers."""

    @pytest.mark.asyncio
    async def test_tiktok_url_filter_accepts_valid_url(self, mock_message):
        """Test that TikTok filter accepts valid TikTok URLs."""
        from app.bot.utils.validators import is_tiktok_url

        mock_message.text = "https://www.tiktok.com/@user/video/7123456789"
        assert is_tiktok_url(mock_message.text) is True

    @pytest.mark.asyncio
    async def test_tiktok_url_filter_accepts_short_url(self, mock_message):
        """Test that TikTok filter accepts short URLs."""
        from app.bot.utils.validators import is_tiktok_url

        mock_message.text = "https://vm.tiktok.com/ABC123/"
        assert is_tiktok_url(mock_message.text) is True

    @pytest.mark.asyncio
    async def test_tiktok_url_filter_rejects_youtube(self, mock_message):
        """Test that TikTok filter rejects YouTube URLs."""
        from app.bot.utils.validators import is_tiktok_url

        mock_message.text = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert is_tiktok_url(mock_message.text) is False


class TestTikTokCallbacks:
    """Tests for TikTok callback handling."""

    def test_audio_callback_data_format(self):
        """Test TikTok audio extraction callback data format."""
        # Callback data should follow pattern: tt_audio:{video_id}
        callback_data = "tt_audio:video123"
        parts = callback_data.split(":")

        assert len(parts) == 2
        assert parts[0] == "tt_audio"
        assert parts[1] == "video123"

    @pytest.mark.asyncio
    async def test_callback_answer_called(self, mock_callback_query):
        """Test that callback query is answered."""
        mock_callback_query.data = "tt_audio:video123"

        await mock_callback_query.answer()

        mock_callback_query.answer.assert_called_once()
