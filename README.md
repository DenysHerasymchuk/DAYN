
<p align="center">
  <img src="src/icon.png" width="300" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Telegram-Bot-2CA5E0?logo=telegram&logoColor=white" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/YouTube-Downloader-FF0000?logo=youtube&logoColor=white" alt="YouTube">
  <img src="https://img.shields.io/badge/TikTok-Downloader-000000?logo=tiktok&logoColor=white" alt="TikTok">
  <img src="https://img.shields.io/badge/Aiogram-3.x-blue?logo=telegram" alt="Aiogram">
  <img src="https://img.shields.io/badge/yt--dlp-2025+-orange" alt="yt-dlp">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/MIT-License-green" alt="MIT License">
  <img src="https://img.shields.io/badge/Prometheus-Metrics-E6522C?logo=prometheus&logoColor=white" alt="Prometheus">
  <img src="https://img.shields.io/badge/Grafana-Dashboards-F46800?logo=grafana&logoColor=white" alt="Grafana">
  <img src="https://img.shields.io/badge/FFmpeg-Included-007808?logo=ffmpeg&logoColor=white" alt="FFmpeg">
</p>

<p align="center">
  <h1 align="center">DAYN - Download All Your Needs</h1>
</p>

DAYN is a smart Telegram bot that makes downloading content from YouTube and TikTok as simple as sending a link. It handles both videos and audio, supports quality selection, and works entirely within Telegram - no external apps or websites needed. Whether you want to save a tutorial, download music, or keep a favorite clip, DAYN delivers files directly to your chat with real-time progress updates and automatic cleanup.

## 🚀 What it Does
DAYN supports two major platforms with distinct features. For YouTube, you can choose from multiple video qualities or extract just the audio as an MP3 file. TikTok downloads include videos, photo slideshows, and audio extraction from clips. The bot shows a visual progress bar while downloading, so you always know what's happening. After sending your file, temporary files are automatically cleaned up to save space.

Important note on file sizes: Telegram Bot API currently limits file uploads to 50MB for all bot accounts. This is a platform restriction, not a DAYN limitation. [You can read more in Telegram's official FAQ.](https://core.telegram.org/bots/faq#how-do-i-upload-a-large-file) 


## 📦 Quick Start for Users
### 1. Get the Bot Ready
First, clone the repository and set up a Python virtual environment. Using a virtual environment is recommended to avoid conflicts with system packages and ensure clean dependency management.

```bash
git clone https://github.com/DenysHerasymchuk/DAYN.git
cd DAYN
```

```bash
#Create and activate virtual environment (Linux/macOS)
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

```
env
BOT_TOKEN=your_actual_bot_token_here
PREMIUM=false
MAX_FILE_SIZE=52428800
TEMP_DIR=temp
LOG_LEVEL=INFO
```

### 4. Start Downloading
Run the bot and send it a YouTube or TikTok link. For YouTube videos, you'll see quality options; for TikTok content, it downloads instantly with an audio extraction option.

```
bash
python run.py
```

Keep your terminal running while using the bot. To stop it, press Ctrl+C in the terminal.

## 🐳 Docker Deployment (Full Stack, preferable)

For production use or monitoring, DAYN includes a complete Docker Compose setup with observability tools:

```bash
docker-compose up -d
```

This starts four services:
- Bot Service: The Telegram bot itself, exposing metrics on port `8000`
- Prometheus: Time-series database collecting metrics on port `9090`
- Grafana: Beautiful dashboards on port `3000` (login: `admin/admin`)
- Node Exporter: System-level metrics on port `9100`

The monitoring stack gives you real-time insights into download statistics, success rates, error patterns, and system performance—perfect for understanding how your bot is being used.

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
- YouTube Downloader (app/downloader/youtube/): Uses yt-dlp to fetch video info, estimate sizes, and download content
- TikTok Downloader (app/downloader/tiktok/): Combines yt-dlp for videos and musicaldown.com API for photo posts

Each downloader implements progress callbacks that update the user with visual progress bars. File size checking enforces the 50MB Telegram limit

### 3. Core Services
File Manager (`app/core/file_manager.py`): Handles all file operations including audio extraction (via FFmpeg), cleanup, and temporary storage management

Metrics (`app/bot/utils/metrics.py`): Prometheus integration tracking downloads, errors, processing times, and file sizes

User Logger: Structured logging with user context for debugging and analytics

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

Telegram's 50MB file upload limit for bots is the primary constraint. DAYN handles this by:
- Filtering out YouTube qualities that would exceed the limit
- Providing estimated file sizes before download

Other known issues:
- Some TikTok photo posts may fail audio extraction due to platform inconsistencies
- YouTube metadata fetching can time out on slow connections (30-second timeout)
- Concurrent downloads are limited by Telegram's rate limiting

These issues are actively tracked and improvements are welcome via GitHub issues.

## 💰 Supporting the Project
DAYN is open source and free to use. If it saves you time or you find it valuable, consider supporting its development:

- 👀 Follow me on GitHub
- ⭐ Star the project on GitHub

Contributions, bug reports, and feature requests are all welcome on the GitHub repository.

## 📄 License & Attribution
DAYN is released under the **MIT License © 2026 Denys Herasymchuk**. This means you're free to use, modify, and distribute the software, as long as you include the original copyright notice. See the LICENSE file for complete terms.

The project builds upon several excellent open-source libraries including Aiogram for Telegram integration, yt-dlp for media downloading, and Prometheus for metrics collection.