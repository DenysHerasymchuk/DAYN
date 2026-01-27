import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required in .env file")

    # File size limit (default 50MB - Telegram bot limit)
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))

    # Directories
    TEMP_DIR = "temp"
    LOGS_DIR = "logs"

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Create directories
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Download settings
    MAX_DOWNLOAD_RETRIES = 3
    DOWNLOAD_TIMEOUT = 300  # 5 minutes

    # Cache settings
    CACHE_TTL = 3600  # 1 hour


settings = Settings()