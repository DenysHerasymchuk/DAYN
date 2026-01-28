"""Tests for file manager utilities."""
import os
from unittest.mock import patch

import pytest


class TestFileManagerUnit:
    """Unit tests for FileManager that don't require actual file operations."""

    def test_create_temp_filename_format(self, temp_dir):
        """Test temp filename format."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            filename = fm.create_temp_filename(prefix="test", extension="mp4")

            assert "test_" in filename
            assert filename.endswith(".mp4")
            assert str(temp_dir) in filename

    def test_create_temp_filename_unique(self, temp_dir):
        """Test that temp filenames are unique."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            filename1 = fm.create_temp_filename()
            filename2 = fm.create_temp_filename()

            assert filename1 != filename2


class TestFileOperations:
    """Tests for file operations with actual files."""

    @pytest.mark.asyncio
    async def test_cleanup_file_exists(self, temp_dir):
        """Test cleanup of existing file."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            # Create a test file
            test_file = temp_dir / "test_file.txt"
            test_file.write_text("test content")
            assert test_file.exists()

            # Clean it up
            result = await fm.cleanup_file(str(test_file))

            assert result is True
            assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_cleanup_file_not_exists(self, temp_dir):
        """Test cleanup of non-existing file returns False."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            result = await fm.cleanup_file(str(temp_dir / "nonexistent.txt"))
            assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_files_multiple(self, temp_dir):
        """Test cleanup of multiple files."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            # Create test files
            files = []
            for i in range(3):
                f = temp_dir / f"test_{i}.txt"
                f.write_text(f"content {i}")
                files.append(str(f))

            deleted = await fm.cleanup_files(files)

            assert deleted == 3
            for f in files:
                assert not os.path.exists(f)

    @pytest.mark.asyncio
    async def test_get_file_size(self, temp_dir):
        """Test getting file size."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            # Create a file with known content
            test_file = temp_dir / "size_test.txt"
            content = "x" * 100
            test_file.write_text(content)

            size = await fm.get_file_size(str(test_file))
            assert size == 100

    @pytest.mark.asyncio
    async def test_get_file_size_nonexistent(self, temp_dir):
        """Test getting size of nonexistent file returns 0."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            size = await fm.get_file_size(str(temp_dir / "nonexistent.txt"))
            assert size == 0

    @pytest.mark.asyncio
    async def test_get_file_size_mb(self, temp_dir):
        """Test getting file size in MB."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            # Create a 1KB file
            test_file = temp_dir / "mb_test.txt"
            test_file.write_bytes(b"x" * 1024)

            size_mb = await fm.get_file_size_mb(str(test_file))
            assert abs(size_mb - 0.0009765625) < 0.0001  # 1KB in MB

    @pytest.mark.asyncio
    async def test_is_file_too_large_under_limit(self, temp_dir):
        """Test file under size limit."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 1024  # 1KB limit

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            test_file = temp_dir / "small.txt"
            test_file.write_bytes(b"x" * 100)

            is_too_large = await fm.is_file_too_large(str(test_file), max_size=1024)
            assert is_too_large is False

    @pytest.mark.asyncio
    async def test_is_file_too_large_over_limit(self, temp_dir):
        """Test file over size limit."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 100

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            test_file = temp_dir / "large.txt"
            test_file.write_bytes(b"x" * 200)

            is_too_large = await fm.is_file_too_large(str(test_file), max_size=100)
            assert is_too_large is True

    @pytest.mark.asyncio
    async def test_get_temp_dir_size(self, temp_dir):
        """Test getting temp directory size."""
        with patch("app.config.settings.settings") as mock_settings:
            mock_settings.TEMP_DIR = str(temp_dir)
            mock_settings.MAX_FILE_SIZE = 50 * 1024 * 1024

            from app.core.file_manager import FileManager
            fm = FileManager()
            fm.temp_dir = str(temp_dir)

            # Create some files
            for i in range(3):
                (temp_dir / f"file_{i}.txt").write_bytes(b"x" * 1024)

            size_mb, count = await fm.get_temp_dir_size()

            assert count == 3
            assert size_mb > 0
