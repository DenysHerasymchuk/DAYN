"""Tests for URL validators."""
import pytest

from app.bot.utils.validators import is_tiktok_url, is_youtube_url


class TestYouTubeValidator:
    """Tests for YouTube URL validation."""

    @pytest.mark.parametrize("url", [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "http://youtu.be/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        "www.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtube.com/watch?v=dQw4w9WgXcQ",
        "youtu.be/dQw4w9WgXcQ",
        "HTTPS://WWW.YOUTUBE.COM/watch?v=dQw4w9WgXcQ",  # uppercase
    ])
    def test_valid_youtube_urls(self, url):
        """Test that valid YouTube URLs are recognized."""
        assert is_youtube_url(url) is True

    @pytest.mark.parametrize("url", [
        "https://www.tiktok.com/@user/video/123",
        "https://vimeo.com/123456",
        "https://www.dailymotion.com/video/x123",
        "https://www.facebook.com/video/123",
        "https://twitter.com/user/status/123",
        "not a url at all",
        "",
        "youtube",
        "https://fakeyoutube.com/watch?v=123",
        "https://youtubeee.com/watch?v=123",
    ])
    def test_invalid_youtube_urls(self, url):
        """Test that non-YouTube URLs are rejected."""
        assert is_youtube_url(url) is False


class TestTikTokValidator:
    """Tests for TikTok URL validation."""

    @pytest.mark.parametrize("url", [
        "https://www.tiktok.com/@username/video/7123456789012345678",
        "https://tiktok.com/@username/video/7123456789012345678",
        "http://www.tiktok.com/@username/video/7123456789012345678",
        "https://vm.tiktok.com/ABC123xyz/",
        "https://vt.tiktok.com/ABC123xyz/",
        "https://m.tiktok.com/@username/video/7123456789012345678",
        "www.tiktok.com/@username/video/123",
        "tiktok.com/@username/video/123",
        "HTTPS://WWW.TIKTOK.COM/@user/video/123",  # uppercase
    ])
    def test_valid_tiktok_urls(self, url):
        """Test that valid TikTok URLs are recognized."""
        assert is_tiktok_url(url) is True

    @pytest.mark.parametrize("url", [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.instagram.com/reel/123",
        "https://twitter.com/user/status/123",
        "not a url at all",
        "",
        "tiktok",
        "https://faketiktok.com/@user/video/123",
        "https://tiktokk.com/@user/video/123",
    ])
    def test_invalid_tiktok_urls(self, url):
        """Test that non-TikTok URLs are rejected."""
        assert is_tiktok_url(url) is False


class TestCrossValidation:
    """Test that validators don't overlap."""

    def test_youtube_not_detected_as_tiktok(self):
        """YouTube URLs should not match TikTok validator."""
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert is_youtube_url(youtube_url) is True
        assert is_tiktok_url(youtube_url) is False

    def test_tiktok_not_detected_as_youtube(self):
        """TikTok URLs should not match YouTube validator."""
        tiktok_url = "https://www.tiktok.com/@user/video/123"
        assert is_tiktok_url(tiktok_url) is True
        assert is_youtube_url(tiktok_url) is False
