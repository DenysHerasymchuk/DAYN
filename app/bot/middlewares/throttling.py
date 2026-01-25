import asyncio
from datetime import datetime, timedelta
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Dict, Any, Callable, Awaitable


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware for throttling requests."""

    def __init__(self, rate_limit: int = 1, period: int = 1):
        self.rate_limit = rate_limit
        self.period = period
        self.users: Dict[int, list] = {}

    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = datetime.now()

        # Clean old timestamps
        if user_id in self.users:
            self.users[user_id] = [
                ts for ts in self.users[user_id]
                if current_time - ts < timedelta(seconds=self.period)
            ]

        # Initialize user if not exists
        if user_id not in self.users:
            self.users[user_id] = []

        # Check rate limit
        if len(self.users[user_id]) >= self.rate_limit:
            if isinstance(event, Message):
                await event.answer("⏳ Please wait before sending another request.")
            else:
                await event.answer("⏳ Please wait...", show_alert=True)
            return

        # Add current timestamp
        self.users[user_id].append(current_time)

        # Call handler
        return await handler(event, data)