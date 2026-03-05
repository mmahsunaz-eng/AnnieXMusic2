# Authored By Certified Coders © 2025

import asyncio
import contextlib
import glob
import os
import re
from typing import Dict, Optional

import aiofiles
import aiohttp
from aiohttp import TCPConnector
from yt_dlp import YoutubeDL

from AnnieXMedia.utils.cookie_handler import COOKIE_PATH as _COOKIES_FILE
from AnnieXMedia.utils.tuning import CHUNK_SIZE, SEM
from config import API_KEY, API_URL, VIDEO_API_URL
from AnnieXMedia.logging import LOGGER

LOGGER = LOGGER(__name__)

# ==============================
# HEROKU SAFE DIRECTORIES
# ==============================

DOWNLOAD_DIR = "/tmp"
CACHE_DIR = "/tmp"

USE_AUDIO_API = bool(API_URL and API_KEY)
USE_VIDEO_API = bool(VIDEO_API_URL and API_KEY)

_inflight: Dict[str, asyncio.Future] = {}
_inflight_lock = asyncio.Lock()

_session: Optional[aiohttp.ClientSession] = None
_session_lock = asyncio.Lock()

YOUTUBE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")


# ==============================
# UTILS
# ==============================

def log_download_source(title: str, source: str) -> None:
    LOGGER.info(f"Track '{title}' - Downloaded by {source}")


def extract_video_id(link: str) -> str:
    if not link:
        return ""
    s = link.strip()
    if YOUTUBE_ID_RE.match(s):
        return s
    if "v=" in s:
        return s.split("v=")[-1].split("&")[0]
    last = s.split("/")[-1].split("?")[0]
    if YOUTUBE_ID_RE.match(last):
        return last
    return ""


def get_cookie_file() -> Optional[str]:
    try:
        if _COOKIES_FILE and os.path.exists(_COOKIES_FILE) and os.path.getsize(_COOKIES_FILE) > 0:
            return _COOKIES_FILE
    except Exception:
        pass
    return None


def find_cached_file(video_id: str) -> Optional[str]:
    if not video_id:
        return None
    for ext in ("m4a", "mp4", "webm", "mkv"):
        path = f"/tmp/{video_id}.{ext}"
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
    return None


# ==============================
# YTDLP OPTIONS
# ==============================

def get_ytdlp_base_opts() -> Dict[str, object]:
    opts = {
        "outtmpl": "/tmp/%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "verbose": True, 
        "overwrites": False,
        "continuedl": True,
        "noprogress": True,
        "concurrent_fragment_downloads": 8,
        "socket_timeout": 30,
        "retries": 2,
        "fragment_retries": 2,
        "cachedir": "/tmp",
        "ignoreerrors": False,
        "merge_output_format": "mp4",
        "ffmpeg_location": "/app/.apt/usr/bin",
        "extractor_args": {
            "youtube": {
               "player_client": 
        ["android", "web"]
    }
},
    }

    if cookiefile := get_cookie_file():
        opts["cookiefile"] = cookiefile

    return opts


def get_final_path_from_info(info: Dict) -> Optional[str]:
    vid = info.get("id")
    if not vid:
        return None

    matches = sorted(
        glob.glob(f"/tmp/{vid}.*"),
        key=os.path.getmtime,
        reverse=True,
    )

    for path in matches:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path

    return None


def download_with_ytdlp_sync(link: str, fmt: str, audio_only: bool = False) -> Optional[str]:
    try:
        opts = get_ytdlp_base_opts()
        opts["format"] = fmt

        # hanya untuk /play
        if audio_only:
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=True)

        path = get_final_path_from_info(info)

        if path and os.path.exists(path) and os.path.getsize(path) > 0:
            return path

        return None

    except Exception as e:
        LOGGER.error(f"yt-dlp failed: {e}")
        return None


# ==============================
# HTTP SESSION
# ==============================

async def get_http_session() -> aiohttp.ClientSession:
    global _session
    if _session and not _session.closed:
        return _session

    async with _session_lock:
        if _session and not _session.closed:
            return _session

        timeout = aiohttp.ClientTimeout(total=600)
        connector = TCPConnector(limit=0, ttl_dns_cache=300)
        _session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return _session


async def download_file(url: str, out_path: str) -> Optional[str]:
    try:
        session = await get_http_session()
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            async with aiofiles.open(out_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    if chunk:
                        await f.write(chunk)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return out_path

        return None

    except Exception:
        return None


# ==============================
# MAIN DOWNLOAD FUNCTION
# ==============================

async def run_with_semaphore(coro):
    async with SEM:
        return await coro


async def deduplicate_download(key: str, runner):
    async with _inflight_lock:
        if fut := _inflight.get(key):
            return await fut
        fut = asyncio.get_running_loop().create_future()
        _inflight[key] = fut

    try:
        result = await runner()
        fut.set_result(result)
        return result
    finally:
        async with _inflight_lock:
            _inflight.pop(key, None)


async def yt_dlp_download(link: str, type: str, title: str = "") -> Optional[str]:
    loop = asyncio.get_running_loop()
    vid = extract_video_id(link)

    if cached := find_cached_file(vid):
        if title:
            LOGGER.info(f"Track '{title}' - Served from cache")
        return cached

    if type == "audio":

        async def run():
            result = await run_with_semaphore(
                loop.run_in_executor(
                    None,
                    download_with_ytdlp_sync,
                    link,
                    "bestaudio*/bestaudio/best",
                    True,  # audio mode
                )
            )
            if result and title:
                log_download_source(title, "yt-dlp")
            return result

        return await deduplicate_download(f"audio:{link}", run)

    elif type == "video":

        async def run():
            result = await run_with_semaphore(
                loop.run_in_executor(
                    None,
                    download_with_ytdlp_sync,
                    link,
                    "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
                    False,  # video mode
                )
            )
            if result and title:
                log_download_source(title, "yt-dlp")
            return result

        return await deduplicate_download(f"video:{link}", run)

    return None
