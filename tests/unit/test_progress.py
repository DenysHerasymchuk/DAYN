"""Tests for progress utilities."""
import pytest

from app.bot.utils.progress import (
    create_video_progress_bar,
    format_duration,
    format_file_size,
)


class TestProgressBar:
    """Tests for progress bar generation."""

    def test_zero_percent(self):
        """Test progress bar at 0%."""
        result = create_video_progress_bar(0)
        assert "0%" in result
        assert result.count("⬛") == 10
        assert result.count("⬜") == 0

    def test_fifty_percent(self):
        """Test progress bar at 50%."""
        result = create_video_progress_bar(50)
        assert "50%" in result
        assert result.count("⬜") == 5
        assert result.count("⬛") == 5

    def test_hundred_percent(self):
        """Test progress bar at 100%."""
        result = create_video_progress_bar(100)
        assert "100%" in result
        assert result.count("⬜") == 10
        assert result.count("⬛") == 0

    @pytest.mark.parametrize("percent,filled", [
        (0, 0),
        (10, 1),
        (25, 2),
        (33, 3),
        (50, 5),
        (75, 7),
        (90, 9),
        (100, 10),
    ])
    def test_various_percentages(self, percent, filled):
        """Test progress bar at various percentages."""
        result = create_video_progress_bar(percent)
        assert result.count("⬜") == filled


class TestFormatFileSize:
    """Tests for file size formatting."""

    @pytest.mark.parametrize("size_bytes,expected", [
        (0, "0.0 B"),
        (500, "500.0 B"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (1024 * 1024, "1.0 MB"),
        (1024 * 1024 * 1.5, "1.5 MB"),
        (1024 * 1024 * 50, "50.0 MB"),
        (1024 * 1024 * 1024, "1.0 GB"),
        (1024 * 1024 * 1024 * 1024, "1.0 TB"),
    ])
    def test_file_size_formatting(self, size_bytes, expected):
        """Test file size formatting at various sizes."""
        assert format_file_size(int(size_bytes)) == expected


class TestFormatDuration:
    """Tests for duration formatting."""

    def test_zero_duration(self):
        """Test formatting zero duration."""
        assert format_duration(0) == "Unknown"

    def test_none_duration(self):
        """Test formatting None duration."""
        assert format_duration(None) == "Unknown"

    @pytest.mark.parametrize("seconds,expected", [
        (30, "0:30"),
        (60, "1:00"),
        (90, "1:30"),
        (180, "3:00"),
        (3599, "59:59"),
        (3600, "1:00:00"),
        (3661, "1:01:01"),
        (7200, "2:00:00"),
        (86400, "24:00:00"),
    ])
    def test_duration_formatting(self, seconds, expected):
        """Test duration formatting at various lengths."""
        assert format_duration(seconds) == expected

    def test_minutes_padded(self):
        """Test that minutes are zero-padded in hour format."""
        result = format_duration(3665)  # 1 hour, 1 minute, 5 seconds
        assert result == "1:01:05"

    def test_seconds_padded(self):
        """Test that seconds are zero-padded."""
        result = format_duration(65)  # 1 minute, 5 seconds
        assert result == "1:05"
