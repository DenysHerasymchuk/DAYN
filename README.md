
<p align="center">
  <img src="./src/icon.png" width="300" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Telegram-Bot-2CA5E0?logo=telegram&logoColor=white" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/Aiogram-3.x-blue?logo=telegram" alt="Aiogram">
  <img src="https://img.shields.io/badge/yt--dlp-2025+-orange" alt="yt-dlp">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/MIT-License-green" alt="MIT License">
  <img src="https://img.shields.io/badge/Prometheus-Metrics-E6522C?logo=prometheus&logoColor=white" alt="Prometheus">
  <img src="https://img.shields.io/badge/Grafana-Dashboards-F46800?logo=grafana&logoColor=white" alt="Grafana">
</p>


<h1 align="center">DAYN - Download All Your Needs</h1>


DAYN is a smart Telegram bot that makes downloading content from YouTube and TikTok as simple as sending a link. It handles both videos and audio, supports quality selection, and automatically handles files of any size. Whether you want to save a tutorial, download music, or keep a favorite clip, DAYN delivers files directly to your chat with real-time progress updates and automatic cleanup.

## 🚀 What it Does
DAYN supports two major platforms with distinct features. For YouTube, you can choose from any available video quality or extract just the audio as an MP3 file. TikTok downloads include videos, photo slideshows, and audio extraction from clips. The bot shows a visual progress bar while downloading, so you always know what's happening. After sending your file, temporary files are automatically cleaned up to save space.

**File size handling:** Telegram Bot API limits bot uploads to 50 MB — a known platform restriction [documented in Telegram's official FAQ](https://core.telegram.org/bots/faq#how-do-i-upload-a-large-file). DAYN solves this by automatically hosting oversized files on its built-in web server and sending you a private download link instead. The link is valid for a configurable period (default 30 minutes) and the file is deleted afterward. Large YouTube qualities are marked with 🔗 in the quality picker to indicate they will be delivered via link.


## 📦 Quick Start for Users
### 1. Get the Bot Ready
First, clone the repository and set up a Python virtual environment. Using a virtual environment is recommended to avoid conflicts with system packages and ensure clean dependency management.

```bash
git clone https://github.com/DenysHerasymchuk/DAYN.git
cd DAYN
```

```bash
# Create and activate virtual environment (Linux/macOS)
python -m venv venv
source venv/bin/activate
```

```bash
# Create and activate virtual environment (Windows)
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
With your virtual environment active, install all required Python packages. These include Aiogram for Telegram integration, yt-dlp for media downloading, and other supporting libraries.

```bash
pip install -r requirements.txt
```
### 3. Configure Your Bot Token
Create your bot through @BotFather on Telegram, then copy the token you receive. Create a .env file in the project root directory with your configuration. The .env.example file shows all available options.

```env
BOT_TOKEN=your_telegram_bot_token_here
MAX_FILE_SIZE=52428800
TEMP_DIR=temp
LOG_LEVEL=INFO
LOGS_DIR=logs

# Monitoring
METRICS_PORT=8000
ENVIRONMENT=development

# Web file server (large file fallback)
WEB_PORT=8080
WEB_BASE_URL=http://your-domain.com:8080
FILE_EXPIRY_SECONDS=1800

# Download performance (parallel DASH fragment downloads, 1-16)
CONCURRENT_FRAGMENT_DOWNLOADS=4
```

`WEB_BASE_URL` must be set to a publicly reachable address so that the download links sent to users actually work. For local testing, use your machine's LAN IP (e.g. `http://192.168.0.x:8080`).

### 4. Start Downloading
Run the bot and send it a YouTube or TikTok link. For YouTube videos, you'll see quality options; for TikTok content, it downloads instantly with an audio extraction option.

```bash
python run.py
```

## 🐳 Docker Deployment (Preferable)

For production use or monitoring, DAYN includes a complete Docker Compose setup with observability tools:

```bash
docker-compose up -d
```

This starts four services:
- **Bot Service**: The Telegram bot itself, exposing metrics on port `8000` and the web file server on port `8080`
- **Prometheus**: Time-series database collecting metrics on port `9090`
- **Grafana**: Dashboards on port `3000` (login: `admin/admin`)
- **Node Exporter**: System-level metrics on port `9100`

The monitoring stack gives you real-time insights into download statistics, success rates, error patterns, and system performance—perfect for understanding how your bot is being used.

> Make sure port `8080` is accessible from the internet (or your LAN) and that `WEB_BASE_URL` in your `.env` points to it, so download links sent to Telegram users are reachable.

## 🏗️ How DAYN Works (For Developers)

DAYN is built with a modular architecture that separates concerns clearly. The entry point is `app/bot/main.py` which sets up the Aiogram dispatcher, logging, and metrics server. Here's how the flow works:

### 1. Handler Architecture
The bot uses a router-based handler system:
- Common Handlers (`app/bot/handlers/common/`): Handle /start, /help, and cancel operations
- YouTube Handlers (`app/bot/handlers/youtube/`): Process YouTube URLs, fetch available qualities, manage download callbacks
- TikTok Handlers (`app/bot/handlers/tiktok/`): Process TikTok URLs, handle photos/videos, manage audio extraction

When a user sends a URL, validators in `app/bot/utils/validators.py` check if it's a YouTube or TikTok link. The appropriate handler takes over, using state management to track user sessions through the download process.

### 2. Downloader System
The download logic is abstracted into platform-specific downloaders:
- **YouTube Downloader** (`app/downloader/youtube/`): Uses yt-dlp to fetch video info, list all available qualities, and download content. All qualities are shown — large ones are flagged with 🔗 to indicate web delivery.
- **TikTok Downloader** (`app/downloader/tiktok/`): Combines yt-dlp for videos and musicaldown.com API for photo posts.

Each downloader implements progress callbacks that update the user with visual progress bars. After download, the actual file size is checked. Files within Telegram's 50 MB limit are sent directly; larger files are handed off to the web server.

### 3. Web File Server
`app/web/` is a self-contained aiohttp web server that handles large file delivery:

- **`file_registry.py`**: Token-based registry tracking hosted files. Each entry carries a UUID token, file path, size, content type, expiry time, and a `consumed` flag. Files are deleted automatically after download or when the link expires.
- **`server.py`**: Four routes — `/download/{token}` (HTML page), `/preview/{token}` (range-request streaming for in-browser playback), `/files/{token}` (one-time download that deletes the file after transfer), `/health`.
- **`templates/`**: HTML pages (`download.html`, `consumed.html`, `expired.html`) loaded once at startup using Python's `string.Template`.
- **`static/`**: `style.css` served by aiohttp's static handler and cached by browsers.

### 4. Core Services
**File Manager** (`app/core/file_manager.py`): Handles all file operations including audio extraction (via FFmpeg), cleanup, and temporary storage management.

**Metrics** (`app/bot/utils/metrics.py`): Prometheus integration tracking downloads, errors, processing times, and file sizes.

**User Logger**: Structured logging with user context for debugging and analytics.

### 4. State Management
The bot uses Aiogram's FSM (Finite State Machine) to track user sessions. For YouTube, it remembers quality selections; for TikTok, it maintains context for audio extraction. States automatically expire after 24 hours to prevent stale data.

## 📊 Monitoring & Observability

DAYN includes comprehensive metrics out of the box. The Prometheus client exposes:

- Download counts segmented by platform and success status
- Processing time histograms for different handlers
- File size distributions
- Error rates by type and platform
- Active user gauges

The included Grafana dashboard (`monitoring/grafana/provisioning/dashboards/dayn-bot.json`) provides visualizations for all these metrics. You can access it at http://localhost:3000 after starting the Docker stack.

## ⚠️ Current Limitations & Known Issues

Telegram's 50 MB upload limit for bots is handled automatically — files above the limit are hosted on DAYN's built-in web server and a private download link is sent instead. The link expires after `FILE_EXPIRY_SECONDS` (default 30 minutes) and the file is deleted.

Other known issues:
- Download links require `WEB_BASE_URL` to point to a publicly reachable address; links will not work if it is set to `localhost`
- Some TikTok photo posts may fail audio extraction due to platform inconsistencies
- YouTube metadata fetching can time out on slow connections (30-second timeout)
- Concurrent requests per user are throttled to **1 per second** by `ThrottlingMiddleware` (`app/bot/middlewares/throttling.py`). This prevents abuse but means rapid button presses (e.g. quickly re-selecting quality) will be silently dropped with a "Please wait..." notice

These issues are actively tracked and improvements are welcome via GitHub issues.

## 💰 Supporting the Project
DAYN is open source and free to use. If it saves you time or you find it valuable, consider supporting its development:

- 👀 Follow me on GitHub
- ⭐ Star the project on GitHub

Contributions, bug reports, and feature requests are all welcome on the GitHub repository.

## 📄 License & Attribution
DAYN is released under the **MIT License © 2026 Denys Herasymchuk**. This means you're free to use, modify, and distribute the software, as long as you include the original copyright notice. See the LICENSE file for complete terms.

The project builds upon several excellent open-source libraries including Aiogram for Telegram integration, yt-dlp for media downloading, and Prometheus for metrics collection.