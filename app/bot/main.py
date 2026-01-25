import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config.settings import settings
from app.bot.handlers import router
from app.bot.middlewares.throttling import ThrottlingMiddleware

# Custom formatter to include user_id when available
# Custom formatter to include user_id when available
class UserAwareFormatter(logging.Formatter):
    def format(self, record):
        # Try to extract user_id from extra dict
        user_id = getattr(record, 'user_id', None)

        # Format the message normally first
        message = super().format(record)

        # Remove ALL occurrences of [User:XXX] and "User: XXX" patterns from the message
        import re
        # Remove [User:XXX] patterns
        message = re.sub(r'\[User:\d+\]\s*', '', message)
        # Remove "User: XXX" patterns (with or without brackets)
        message = re.sub(r'User:\s*\d+\s*[\|]?\s*', '', message)
        # Remove "| User: XXX" patterns
        message = re.sub(r'\|\s*User:\s*\d+', '', message)

        # Clean up any double pipes or trailing/leading spaces
        message = re.sub(r'\s*\|\s*\|', ' |', message)  # Fix double pipes
        message = re.sub(r'\s*\|\s*$', '', message)  # Remove trailing pipe
        message = message.strip()

        # Add clean user ID at the beginning if available
        if user_id:
            message = f"[User:{user_id}] {message}"

        return message

# Configure logging
logger = logging.getLogger(__name__)

# Create formatter
formatter = UserAwareFormatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create handlers
file_handler = logging.FileHandler(f"{settings.LOGS_DIR}/bot.log", encoding='utf-8')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    handlers=[file_handler, stream_handler]
)


async def main():
    """Start the bot."""
    # Create bot
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Setup middleware
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    # Include router
    dp.include_router(router)

    # Start bot
    logger.info("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())