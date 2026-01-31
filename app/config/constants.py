class Timeouts:
    SESSION_EXPIRY_SECONDS = 86400
    SOCKET_TIMEOUT = 30
    DOWNLOAD_TIMEOUT = 300
    PROGRESS_UPDATE_INTERVAL = 0.5
    PROGRESS_TASK_WAIT = 1.0


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
        "• https://youtu.be/...\n"
        "• https://www.tiktok.com/@.../video/..."
    )
