"""
Prometheus metrics for the bot.
"""
import logging
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server

logger = logging.getLogger(__name__)

# Bot info
BOT_INFO = Info('dayn_bot', 'DAYN Bot information')

# Download counters
DOWNLOADS_TOTAL = Counter(
    'dayn_downloads_total',
    'Total number of downloads',
    ['platform', 'content_type', 'status']
)

# Download duration
DOWNLOAD_DURATION = Histogram(
    'dayn_download_duration_seconds',
    'Download duration in seconds',
    ['platform', 'content_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

# File sizes
FILE_SIZE_BYTES = Histogram(
    'dayn_file_size_bytes',
    'Downloaded file sizes in bytes',
    ['platform', 'content_type'],
    buckets=[1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6]
)

# Active users
ACTIVE_USERS = Gauge(
    'dayn_active_users',
    'Number of active users in the last hour'
)

# Requests
REQUESTS_TOTAL = Counter(
    'dayn_requests_total',
    'Total number of requests',
    ['handler', 'status']
)

# Errors
ERRORS_TOTAL = Counter(
    'dayn_errors_total',
    'Total number of errors',
    ['platform', 'error_type']
)

# Message processing time
MESSAGE_PROCESSING_TIME = Histogram(
    'dayn_message_processing_seconds',
    'Message processing time in seconds',
    ['handler'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
)


def start_metrics_server(port: int = 8000):
    """Start the Prometheus metrics HTTP server."""
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")


def set_bot_info(version: str = "1.0.0", environment: str = "production"):
    """Set bot information."""
    BOT_INFO.info({
        'version': version,
        'environment': environment
    })


def record_download(platform: str, content_type: str, success: bool, duration: float, file_size: int):
    """Record a download event."""
    status = 'success' if success else 'failed'
    DOWNLOADS_TOTAL.labels(platform=platform, content_type=content_type, status=status).inc()

    if success:
        DOWNLOAD_DURATION.labels(platform=platform, content_type=content_type).observe(duration)
        FILE_SIZE_BYTES.labels(platform=platform, content_type=content_type).observe(file_size)


def record_request(handler: str, success: bool):
    """Record a request event."""
    status = 'success' if success else 'failed'
    REQUESTS_TOTAL.labels(handler=handler, status=status).inc()


def record_error(platform: str, error_type: str):
    """Record an error event."""
    ERRORS_TOTAL.labels(platform=platform, error_type=error_type).inc()


def record_processing_time(handler: str, duration: float):
    """Record message processing time."""
    MESSAGE_PROCESSING_TIME.labels(handler=handler).observe(duration)


def update_active_users(count: int):
    """Update active users gauge."""
    ACTIVE_USERS.set(count)
