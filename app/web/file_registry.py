import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import aiofiles.os

logger = logging.getLogger(__name__)


@dataclass
class FileEntry:
    token: str
    file_path: str
    filename: str
    file_size: int
    content_type: str          # "video" or "audio"
    created_at: datetime
    expires_at: datetime
    audio_token: Optional[str] = None   # token of extracted audio (video entries only)
    consumed: bool = False              # True after the file has been downloaded


class FileRegistry:
    """Token-based registry that tracks hosted files awaiting user download."""

    def __init__(self) -> None:
        self._entries: dict[str, FileEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    def start_cleanup_task(self) -> None:
        """Start the background cleanup task. Must be called inside a running event loop."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(300)  # check every 5 minutes
            await self.cleanup_expired()

    async def register(
        self,
        file_path: str,
        filename: str,
        file_size: int,
        content_type: str = "video",
        expires_seconds: int = 1800,
        audio_token: Optional[str] = None,
    ) -> str:
        """Register a file for hosting and return its access token."""
        token = uuid.uuid4().hex
        now = datetime.utcnow()
        entry = FileEntry(
            token=token,
            file_path=file_path,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            created_at=now,
            expires_at=now + timedelta(seconds=expires_seconds),
            audio_token=audio_token,
        )
        async with self._lock:
            self._entries[token] = entry
        logger.info(
            f"Registered {content_type} for web hosting: {filename} "
            f"({file_size / (1024 * 1024):.1f} MB) token={token[:8]}..."
        )
        return token

    async def get(self, token: str) -> Optional[FileEntry]:
        """Return the entry if it exists and has not expired.
        Returns the entry even if consumed — callers must check entry.consumed."""
        async with self._lock:
            entry = self._entries.get(token)
        if entry is None:
            return None
        if datetime.utcnow() > entry.expires_at:
            await self._remove(token, entry)
            return None
        return entry

    async def consume(self, token: str) -> None:
        """Mark entry as consumed and delete its file.
        The entry remains in the registry until expiry so callers can detect the consumed state."""
        async with self._lock:
            entry = self._entries.get(token)
        if entry is None or entry.consumed:
            return
        entry.consumed = True
        try:
            if await aiofiles.os.path.exists(entry.file_path):
                await aiofiles.os.remove(entry.file_path)
                logger.info(f"Consumed and deleted: {entry.filename}")
        except OSError as e:
            logger.warning(f"Could not delete {entry.file_path}: {e}")

    async def _remove(self, token: str, entry: FileEntry) -> None:
        """Remove entry from registry and delete its file if not yet consumed."""
        async with self._lock:
            self._entries.pop(token, None)
        if not entry.consumed:
            try:
                if await aiofiles.os.path.exists(entry.file_path):
                    await aiofiles.os.remove(entry.file_path)
                    logger.info(f"Deleted expired file: {entry.filename}")
            except OSError as e:
                logger.warning(f"Could not delete {entry.file_path}: {e}")

    async def cleanup_expired(self) -> int:
        """Remove all expired entries and their files. Returns the number removed."""
        now = datetime.utcnow()
        async with self._lock:
            expired = [
                (token, entry)
                for token, entry in self._entries.items()
                if now > entry.expires_at
            ]
        count = 0
        for token, entry in expired:
            await self._remove(token, entry)
            count += 1
        if count:
            logger.info(f"Web file cleanup: removed {count} expired entry/entries")
        return count


_registry: Optional[FileRegistry] = None


def get_file_registry() -> FileRegistry:
    global _registry
    if _registry is None:
        _registry = FileRegistry()
    return _registry
