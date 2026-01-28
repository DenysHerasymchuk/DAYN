import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import router
from app.bot.middlewares.throttling import ThrottlingMiddleware
from app.bot.utils.metrics import set_bot_info, start_metrics_server
from app.config.settings import settings


# Custom formatter to include user_id when available
class UserAwareFormatter(logging.Formatter):
    def format(self, record):
        # Get user_id from extra dict if available
        user_id = getattr(record, 'user_id', None)

        # Format normally first
        message = super().format(record)

        # Prepend user_id if available (without modifying original record)
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
    # Start metrics server
    metrics_port = int(os.getenv('METRICS_PORT', 8000))
    start_metrics_server(metrics_port)
    set_bot_info(version="1.0.0", environment=os.getenv('ENVIRONMENT', 'development'))

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
    logger.info(f"Metrics available at http://localhost:{metrics_port}/metrics")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
