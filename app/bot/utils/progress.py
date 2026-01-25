def create_video_progress_bar(percent: float) -> str:
    """Create a visual progress bar with boxes."""
    filled_boxes = int(percent / 10)  # 10 boxes total, each = 10%
    empty_boxes = 10 - filled_boxes

    bar = "⬜" * filled_boxes + "⬛" * empty_boxes
    return f"{bar} {percent:.0f}%"



def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: int) -> str:
    """Format seconds to readable time."""
    if not seconds:
        return 'Unknown'

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"