class Emojis:
    """Emoji constants."""
    VIDEO = "🎬"
    MUSIC = "🎵"
    PHOTO = "📸"
    DOWNLOAD = "⬇️"
    CHECK = "✅"
    CROSS = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    GEAR = "⚙️"
    CLOCK = "⏱"
    USER = "👤"
    FOLDER = "📁"
    SIZE = "💾"
    QUALITY = "📺"
    HELP = "📋"
    LIGHT = "💡"
    THUMB_UP = "👍"
    THUMB_DOWN = "👎"
    PROGRESS = "📊"
    LINK = "🔗"
    MAGNIFY = "🔍"
    ROBOT = "🤖"


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