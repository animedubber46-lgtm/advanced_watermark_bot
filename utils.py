import os
import re
import time
from typing import Optional
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TEMP_DIR

def safe_name(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip())
    return text[:50] or "preset"

def build_presets_keyboard(presets):
    rows = []
    for p in presets:
        rows.append([
            InlineKeyboardButton(
                f"{p.get('name','preset')} ({p.get('type','?')})",
                callback_data=f"usepreset:{str(p['_id'])}"
            )
        ])
    return InlineKeyboardMarkup(rows) if rows else None

def progress_bar(percent: int) -> str:
    done = max(0, min(10, percent // 10))
    return "█" * done + "░" * (10 - done)

def make_temp_video_path(user_id: int, suffix: str) -> str:
    return os.path.join(TEMP_DIR, f"{user_id}_{int(time.time())}_{suffix}.mp4")

def make_temp_file_path(user_id: int, suffix: str, ext: str) -> str:
    return os.path.join(TEMP_DIR, f"{user_id}_{int(time.time())}_{suffix}.{ext}")

def get_video_media(message):
    if message.video:
        return message.video
    if message.document and getattr(message.document, "mime_type", "").startswith("video/"):
        return message.document
    return None
