import re


def is_youtube_url(url: str) -> bool:
    """Check if URL is YouTube."""
    youtube_patterns = [
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/',
        r'^(https?://)?(m\.)?youtube\.com/',
        r'^(https?://)?(music\.)?youtube\.com/'
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, url, re.IGNORECASE):
            return True
    return False


def is_tiktok_url(url: str) -> bool:
    """Check if URL is TikTok."""
    tiktok_patterns = [
        r'^(https?://)?(www\.)?tiktok\.com/',
        r'^(https?://)?(vm|vt)\.tiktok\.com/',
        r'^(https?://)?(m\.)?tiktok\.com/'
    ]

    for pattern in tiktok_patterns:
        if re.match(pattern, url, re.IGNORECASE):
            return True
    return False
