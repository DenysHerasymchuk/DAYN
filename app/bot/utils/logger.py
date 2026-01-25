import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class UserLogger:
    """Logger with user context."""

    @staticmethod
    def log_user_action(
            function_name: str,
            user_id: int,
            action: str,
            details: str = "",
            extra: Optional[Dict[str, Any]] = None
    ):
        """Log user actions with context."""
        message = f"[{function_name}] {action}"
        if details:
            message += f" | {details}"

        extra_data = extra or {}
        extra_data['user_id'] = user_id

        logger.info(message, extra=extra_data)

    @staticmethod
    def log_user_error(
            function_name: str,
            user_id: int,
            error_message: str,
            exc_info: bool = True,
            extra: Optional[Dict[str, Any]] = None
    ):
        """Log user-related errors."""
        message = f"[{function_name}] ERROR: {error_message}"

        extra_data = extra or {}
        extra_data['user_id'] = user_id

        logger.error(message, extra=extra_data, exc_info=exc_info)

    @staticmethod
    def log_download_start(
            platform: str,
            user_id: int,
            url: str,
            quality: Optional[str] = None
    ):
        """Log download start."""
        message = f"DOWNLOAD START | Platform: {platform}"
        if quality:
            message += f" | Quality: {quality}"

        # Store URL in extra, not in message
        logger.info(message, extra={
            'user_id': user_id,
            'url': url[:100],
            'quality': quality
        })

    @staticmethod
    def log_download_complete(
            platform: str,
            user_id: int,
            file_size_mb: float,
            success: bool = True
    ):
        """Log download completion."""
        status = "SUCCESS" if success else "FAILED"
        message = f"DOWNLOAD {status} | Platform: {platform} | Size: {file_size_mb:.1f}MB"

        logger.info(message, extra={
            'user_id': user_id,
            'file_size_mb': file_size_mb,
            'success': success
        })


# Convenience instance
user_logger = UserLogger()