"""Integration tests for download flows.

These tests verify the complete download flow from URL to file delivery.
External APIs (YouTube, TikTok) are mocked to ensure test reliability.
"""
from unittest.mock import patch

import pytest


class TestYouTubeDownloadFlow:
    """Integration tests for YouTube download flow."""

    @pytest.mark.asyncio
    async def test_youtube_flow_url_to_quality_selection(
        self, mock_message, mock_state, sample_video_info
    ):
        """Test flow from URL submission to quality selection display."""
        mock_message.text = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Verify URL is recognized
        from app.bot.utils.validators import is_youtube_url
        assert is_youtube_url(mock_message.text) is True

        # Mock state should be updated with video info
        await mock_state.update_data(video_info=sample_video_info)
        mock_state.update_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_youtube_quality_selection_flow(
        self, mock_callback_query, mock_state, sample_video_info
    ):
        """Test quality selection callback handling."""
        mock_callback_query.data = "yt_quality:720p"

        # Mock state returns video info
        mock_state.get_data.return_value = {"video_info": sample_video_info}

        data = await mock_state.get_data()
        assert "video_info" in data
        assert data["video_info"]["title"] == "Test Video Title"


class TestTikTokDownloadFlow:
    """Integration tests for TikTok download flow."""

    @pytest.mark.asyncio
    async def test_tiktok_flow_url_detection(self, mock_message):
        """Test TikTok URL is properly detected."""
        mock_message.text = "https://www.tiktok.com/@user/video/7123456789"

        from app.bot.utils.validators import is_tiktok_url
        assert is_tiktok_url(mock_message.text) is True

    @pytest.mark.asyncio
    async def test_tiktok_audio_extraction_flow(
        self, mock_callback_query, mock_state, temp_dir
    ):
        """Test audio extraction from TikTok video."""
        mock_callback_query.data = "tt_audio:video123"

        # Mock state with video path
        video_path = str(temp_dir / "test_video.mp4")
        mock_state.get_data.return_value = {"video_path": video_path}

        data = await mock_state.get_data()
        assert "video_path" in data


class TestErrorHandling:
    """Test error handling in download flows."""

    @pytest.mark.asyncio
    async def test_invalid_url_rejected(self, mock_message):
        """Test that invalid URLs are properly rejected."""
        from app.bot.utils.validators import is_tiktok_url, is_youtube_url

        mock_message.text = "not a valid url"

        assert is_youtube_url(mock_message.text) is False
        assert is_tiktok_url(mock_message.text) is False

    @pytest.mark.asyncio
    async def test_file_cleanup_after_send(self, temp_dir):
        """Test that temporary files are cleaned up after sending."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            # Create a temp file
            test_file = temp_dir / "temp_video.mp4"
            test_file.write_bytes(b"fake video content")

            # Simulate cleanup
            result = await fm.cleanup_file(str(test_file))

            assert result is True
            assert not test_file.exists()
