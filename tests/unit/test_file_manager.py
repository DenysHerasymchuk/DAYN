"""Tests for file manager utilities."""
import os

import pytest

from app.core.file_manager import create_file_manager


class TestFileManagerUnit:
    """Unit tests for FileManager that don't require actual file operations."""

    def test_create_temp_filename_format(self, temp_dir):
        """Test temp filename format."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        filename = fm.create_temp_filename(prefix="test", extension="mp4")

        assert "test_" in filename
        assert filename.endswith(".mp4")
        assert str(temp_dir) in filename

    def test_create_temp_filename_unique(self, temp_dir):
        """Test that temp filenames are unique."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        filename1 = fm.create_temp_filename()
        filename2 = fm.create_temp_filename()

        assert filename1 != filename2

    def test_initialization_creates_directory(self, temp_dir):
        """Test that initialize() creates the temp directory."""
        new_dir = temp_dir / "new_subdir"
        assert not new_dir.exists()

        fm = create_file_manager(str(new_dir))
        assert not new_dir.exists()  # Not created yet

        fm.initialize()
        assert new_dir.exists()  # Now created

    def test_double_initialization_safe(self, temp_dir):
        """Test that calling initialize() twice is safe."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()
        fm.initialize()  # Should not raise


class TestFileOperations:
    """Tests for file operations with actual files."""

    @pytest.mark.asyncio
    async def test_cleanup_file_exists(self, temp_dir):
        """Test cleanup of existing file."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

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
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        result = await fm.cleanup_file(str(temp_dir / "nonexistent.txt"))
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_files_multiple(self, temp_dir):
        """Test cleanup of multiple files."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

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
    async def test_cleanup_files_partial_failure(self, temp_dir):
        """Test cleanup handles partial failures gracefully."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        # Create one real file
        real_file = temp_dir / "real.txt"
        real_file.write_text("content")

        # Mix real and fake files
        files = [
            str(real_file),
            str(temp_dir / "nonexistent1.txt"),
            str(temp_dir / "nonexistent2.txt"),
        ]

        deleted = await fm.cleanup_files(files)

        assert deleted == 1  # Only the real file was deleted
        assert not real_file.exists()

    @pytest.mark.asyncio
    async def test_get_file_size(self, temp_dir):
        """Test getting file size."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        # Create a file with known content
        test_file = temp_dir / "size_test.txt"
        content = "x" * 100
        test_file.write_text(content)

        size = await fm.get_file_size(str(test_file))
        assert size == 100

    @pytest.mark.asyncio
    async def test_get_file_size_nonexistent(self, temp_dir):
        """Test getting size of nonexistent file returns 0."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        size = await fm.get_file_size(str(temp_dir / "nonexistent.txt"))
        assert size == 0

    @pytest.mark.asyncio
    async def test_get_file_size_mb(self, temp_dir):
        """Test getting file size in MB."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        # Create a 1KB file
        test_file = temp_dir / "mb_test.txt"
        test_file.write_bytes(b"x" * 1024)

        size_mb = await fm.get_file_size_mb(str(test_file))
        assert abs(size_mb - 0.0009765625) < 0.0001  # 1KB in MB

    @pytest.mark.asyncio
    async def test_is_file_too_large_under_limit(self, temp_dir):
        """Test file under size limit."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        test_file = temp_dir / "small.txt"
        test_file.write_bytes(b"x" * 100)

        is_too_large = await fm.is_file_too_large(str(test_file), max_size=1024)
        assert is_too_large is False

    @pytest.mark.asyncio
    async def test_is_file_too_large_over_limit(self, temp_dir):
        """Test file over size limit."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        test_file = temp_dir / "large.txt"
        test_file.write_bytes(b"x" * 200)

        is_too_large = await fm.is_file_too_large(str(test_file), max_size=100)
        assert is_too_large is True

    @pytest.mark.asyncio
    async def test_get_temp_dir_size(self, temp_dir):
        """Test getting temp directory size."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        # Create some files
        for i in range(3):
            (temp_dir / f"file_{i}.txt").write_bytes(b"x" * 1024)

        size_mb, count = await fm.get_temp_dir_size()

        assert count == 3
        assert size_mb > 0

    @pytest.mark.asyncio
    async def test_cleanup_files_empty_list(self, temp_dir):
        """Test cleanup with empty list returns 0."""
        fm = create_file_manager(str(temp_dir))
        fm.initialize()

        deleted = await fm.cleanup_files([])
        assert deleted == 0
