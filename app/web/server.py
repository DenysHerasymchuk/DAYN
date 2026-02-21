import json
import logging
from pathlib import Path
from string import Template
from typing import Optional

import aiofiles
from aiohttp import web

from app.web.file_registry import FileEntry, get_file_registry

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"

# Load templates once at import time — missing files fail fast on startup
_tmpl_download = Template((_TEMPLATES_DIR / "download.html").read_text(encoding="utf-8"))
_page_consumed = (_TEMPLATES_DIR / "consumed.html").read_text(encoding="utf-8")
_page_expired = (_TEMPLATES_DIR / "expired.html").read_text(encoding="utf-8")


def _format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _safe(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def _render_page(entry: FileEntry, token: str, audio_entry: Optional[FileEntry] = None) -> str:
    safe_filename = _safe(entry.filename)
    size_str = _format_size(entry.file_size)
    expires_str = entry.expires_at.strftime("%Y-%m-%d %H:%M UTC")
    is_video = entry.content_type == "video"
    content_label = "Video" if is_video else "Audio"
    mime = "video/mp4" if is_video else "audio/mpeg"

    if is_video:
        player = (
            f'<video controls preload="metadata">'
            f'<source src="/preview/{token}" type="{mime}">'
            f'Your browser does not support video.</video>'
        )
    else:
        player = (
            f'<audio controls preload="metadata">'
            f'<source src="/preview/{token}" type="{mime}">'
            f'Your browser does not support audio.</audio>'
        )

    btn_class = "btn-video" if is_video else "btn-audio"
    btn_label = "Video" if is_video else "Audio"
    dl_btn = (
        f'<a class="btn {btn_class}" href="/files/{token}" download="{safe_filename}">'
        f'&#11015;&#65039; Download {btn_label} &mdash; {size_str}</a>'
    )

    audio_btn = ""
    if is_video and audio_entry and not audio_entry.consumed:
        safe_audio = _safe(audio_entry.filename)
        audio_size_str = _format_size(audio_entry.file_size)
        audio_btn = (
            f'<a class="btn btn-audio" href="/files/{audio_entry.token}" download="{safe_audio}">'
            f'&#127925; Download Audio (MP3) &mdash; {audio_size_str}</a>'
        )

    return _tmpl_download.substitute(
        player=player,
        filename=safe_filename,
        size=size_str,
        content_label=content_label,
        dl_btn=dl_btn,
        audio_btn=audio_btn,
        expires=expires_str,
    )


async def _handle_download_page(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    registry = get_file_registry()
    entry = await registry.get(token)

    if entry is None:
        return web.Response(status=404, content_type="text/html", text=_page_expired)

    if entry.consumed:
        return web.Response(status=410, content_type="text/html", text=_page_consumed)

    audio_entry: Optional[FileEntry] = None
    if entry.audio_token:
        audio_entry = await registry.get(entry.audio_token)

    return web.Response(content_type="text/html", text=_render_page(entry, token, audio_entry))


async def _handle_preview(request: web.Request) -> web.Response:
    """Stream file for in-browser preview. Supports range requests for video scrubbing.
    Does NOT consume the entry — preview is unlimited."""
    token = request.match_info["token"]
    entry = await get_file_registry().get(token)

    if entry is None or entry.consumed:
        return web.Response(status=404, text="Not available.")

    path = Path(entry.file_path)
    if not path.exists():
        return web.Response(status=404, text="File no longer available.")

    # FileResponse handles Range headers automatically — required for video/audio scrubbing
    return web.FileResponse(path=path)


async def _handle_file_download(request: web.Request) -> web.StreamResponse:
    """One-time file download. Streams the file then consumes (deletes) the entry."""
    token = request.match_info["token"]
    registry = get_file_registry()
    entry = await registry.get(token)

    if entry is None:
        return web.Response(status=404, content_type="text/html", text=_page_expired)

    if entry.consumed:
        return web.Response(status=410, content_type="text/html", text=_page_consumed)

    path = Path(entry.file_path)
    if not path.exists():
        return web.Response(status=404, text="File no longer available.")

    content_type = "video/mp4" if entry.content_type == "video" else "audio/mpeg"
    response = web.StreamResponse(headers={
        "Content-Disposition": f'attachment; filename="{entry.filename}"',
        "Content-Type": content_type,
        "Content-Length": str(entry.file_size),
    })
    await response.prepare(request)

    try:
        async with aiofiles.open(path, "rb") as f:
            while True:
                chunk = await f.read(512 * 1024)  # 512 KB chunks
                if not chunk:
                    break
                await response.write(chunk)
        # Only consume after the file is fully sent
        await registry.consume(token)
    except Exception:
        # Client disconnected or write failed — do not consume, allow retry
        pass

    return response


async def _handle_health(request: web.Request) -> web.Response:
    return web.Response(
        content_type="application/json",
        text=json.dumps({"status": "ok"}),
    )


async def start_file_server(port: int) -> web.AppRunner:
    """Start the aiohttp file-hosting server. Returns the runner for graceful shutdown."""
    app = web.Application()
    app.router.add_get("/download/{token}", _handle_download_page)
    app.router.add_get("/preview/{token}", _handle_preview)
    app.router.add_get("/files/{token}", _handle_file_download)
    app.router.add_get("/health", _handle_health)
    app.router.add_static("/static", _STATIC_DIR)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    get_file_registry().start_cleanup_task()
    logger.info(f"File server started on port {port}")
    return runner
