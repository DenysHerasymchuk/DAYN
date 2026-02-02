class Timeouts:
    SESSION_EXPIRY_SECONDS = 86400
    SOCKET_TIMEOUT = 30
    DOWNLOAD_TIMEOUT = 300
    PROGRESS_UPDATE_INTERVAL = 0.3  # Seconds between progress checks
    PROGRESS_TASK_WAIT = 1.0
    PROGRESS_CHANGE_THRESHOLD = 2  # Minimum % change to trigger update


class TelegramConfig:
    MEDIA_GROUP_BATCH_SIZE = 10  # Telegram's media group limit


class HttpConfig:
    # Chrome User-Agent (for YouTube, general use)
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    # Firefox User-Agent (for services that block Chrome, like musicaldown)
    USER_AGENT_FIREFOX = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
    ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    ACCEPT_LANGUAGE = "en-US,en;q=0.5"


class TelegramLimits:
    MAX_TITLE_LENGTH = 64
    MAX_CAPTION_LENGTH = 1024
    MAX_FILENAME_LENGTH = 64


class DownloadSettings:
    PROGRESS_UPDATE_THRESHOLD_PERCENT = 20
    AUDIO_BITRATE = '192k'
    AUDIO_CODEC = 'libmp3lame'
    MAX_RETRIES = 3
    FRAGMENT_RETRIES = 3
    EXTRACTOR_RETRIES = 3


class ProgressPercent:
    AUDIO_EXTRACTION_START = 80
    COMPLETE = 100


BYTES_PER_MB = 1024 * 1024


class CallbackData:
    """Typed callback data constants to avoid stringly-typed callbacks."""
    # YouTube
    QUALITY_PREFIX = "quality_"
    FORMAT_AUDIO = "format_audio"

    # TikTok
    TIKTOK_EXTRACT_AUDIO = "tiktok_extract_audio"

    # Common
    CANCEL = "cancel"

    @staticmethod
    def quality(height: int) -> str:
        """Generate quality callback data."""
        return f"{CallbackData.QUALITY_PREFIX}{height}"

    @staticmethod
    def parse_quality(data: str) -> int | None:
        """Parse quality from callback data."""
        if data.startswith(CallbackData.QUALITY_PREFIX):
            try:
                return int(data[len(CallbackData.QUALITY_PREFIX):])
            except ValueError:
                return None
        return None


class Emojis:
    VIDEO = "🎬"
    MUSIC = "🎵"
    PHOTO = "📸"
    DOWNLOAD = "⬇️"
    CHECK = "✅"
    CROSS = "❌"
    WARNING = "⚠️"
    GEAR = "⚙️"
    HOURGLASS = "⏳"
    CLOCK = "⏱"
    USER = "👤"
    SIZE = "💾"
    HELP = "📋"
    LIGHT = "💡"
    UPLOAD = "📤"


class Messages:
    """Message templates."""
    START = (
        "{video} <b>Video Downloader Bot</b>\n\n"
        "Send me a YouTube or TikTok URL to download!\n\n"
        "{light} <b>Features:</b>\n"
        "• Choose video quality\n"
        "• Download audio only (MP3)\n"
        "• Real-time download progress\n"
        "• Automatic cleanup\n\n"
        "{gear} <b>Mode:</b> {status}"
    )

    HELP = (
        "{help} <b>How to use:</b>\n"
        "1. Send YouTube or TikTok URL\n"
        "2. Choose video quality or audio format\n"
        "3. Wait for download (you'll see progress)\n"
        "4. Receive your file!\n\n"
        "{light} <b>Tips:</b>\n"
        "• {limit_text}\n"
        "• Audio files are usually smaller\n"
        "• Files are auto-deleted after sending\n\n"
        "<i>Supported: YouTube, TikTok</i>"
    )

    ERROR_INVALID_URL = (
        "{cross} Please send a valid YouTube or TikTok URL.\n\n"
        "{light} <b>Examples:</b>\n"
        "• https://www.youtube.com/watch?v=...\n"
        "• https://www.tiktok.com/@.../video/..."
    )
