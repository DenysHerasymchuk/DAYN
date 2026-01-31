from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class LRUThrottleCache:
    """LRU cache with TTL for throttling. Prevents memory leaks."""

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 60):
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: OrderedDict[int, List[datetime]] = OrderedDict()

    def _evict_expired(self, user_id: int, now: datetime) -> None:
        if user_id in self._cache:
            self._cache[user_id] = [
                ts for ts in self._cache[user_id]
                if now - ts < self.ttl
            ]
            if not self._cache[user_id]:
                del self._cache[user_id]

    def _enforce_max_size(self) -> None:
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def add_request(self, user_id: int, now: datetime) -> None:
        self._evict_expired(user_id, now)

        if user_id not in self._cache:
            self._cache[user_id] = []

        self._cache[user_id].append(now)
        self._cache.move_to_end(user_id)
        self._enforce_max_size()

    def get_request_count(self, user_id: int, now: datetime) -> int:
        self._evict_expired(user_id, now)
        return len(self._cache.get(user_id, []))


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware for throttling requests with memory-safe LRU cache."""

    def __init__(self, rate_limit: int = 1, period: int = 1, max_users: int = 10000):
        self.rate_limit = rate_limit
        self.period = period
        self._cache = LRUThrottleCache(max_size=max_users, ttl_seconds=period)

    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = datetime.now()

        if self._cache.get_request_count(user_id, current_time) >= self.rate_limit:
            if isinstance(event, Message):
                await event.answer("Please wait before sending another request.")
            else:
                await event.answer("Please wait...", show_alert=True)
            return

        self._cache.add_request(user_id, current_time)
        return await handler(event, data)
