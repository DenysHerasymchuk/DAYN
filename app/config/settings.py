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

    # Web file server (large file fallback)
    WEB_PORT = int(os.getenv("WEB_PORT", 8080))
    WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:8080")
    FILE_EXPIRY_SECONDS = int(os.getenv("FILE_EXPIRY_SECONDS", 1800))  # 30 minutes

    # Download performance
    CONCURRENT_FRAGMENT_DOWNLOADS = int(os.getenv("CONCURRENT_FRAGMENT_DOWNLOADS", 4))

    # Download settings
    MAX_DOWNLOAD_RETRIES = 3
    DOWNLOAD_TIMEOUT = 300  # 5 minutes

    # Cache settings
    CACHE_TTL = 3600  # 1 hour


settings = Settings()
