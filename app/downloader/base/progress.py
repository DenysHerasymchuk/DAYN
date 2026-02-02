"""Shared progress tracking for downloaders."""
import asyncio
import logging
from typing import Callable, Optional

from app.config.constants import Timeouts

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Handles progress tracking for yt-dlp downloads.

    Usage:
        tracker = ProgressTracker(progress_callback)
        ydl_opts = {'progress_hooks': [tracker.hook]}

        await tracker.start()
        # ... run download ...
        await tracker.stop()
    """

    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.state = {'percent': 0, 'downloading': True}
        self.task: Optional[asyncio.Task] = None

    def hook(self, d: dict) -> None:
        """yt-dlp progress hook. Runs in download thread."""
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%').strip('%')
            try:
                self.state['percent'] = float(percent_str)
            except ValueError:
                pass
        elif d['status'] == 'finished':
            self.state['downloading'] = False

    async def _update_loop(self) -> None:
        """Background task to send progress updates."""
        last_percent = -1
        while self.state['downloading']:
            current_percent = self.state['percent']
            if abs(current_percent - last_percent) >= Timeouts.PROGRESS_CHANGE_THRESHOLD:
                try:
                    await self.callback(current_percent)
                    last_percent = current_percent
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            await asyncio.sleep(Timeouts.PROGRESS_UPDATE_INTERVAL)

    async def start(self) -> None:
        """Start the progress update loop."""
        if self.callback:
            self.task = asyncio.create_task(self._update_loop())

    async def stop(self) -> None:
        """Stop the progress update loop and cleanup."""
        self.state['downloading'] = False
        if self.task and not self.task.done():
            try:
                await asyncio.wait_for(self.task, timeout=Timeouts.PROGRESS_TASK_WAIT)
            except asyncio.TimeoutError:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
        self.task = None
