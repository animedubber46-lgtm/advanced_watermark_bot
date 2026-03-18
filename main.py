import asyncio
import os
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, TEMP_DIR, MAX_CONCURRENT_JOBS
from database import db
from states import user_states, pending_videos
from utils import build_presets_keyboard, get_video_media, make_temp_video_path, make_temp_file_path
from watermark.text import apply_text_watermark
from watermark.image import apply_image_watermark

app = Client("advanced_watermark_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)


HELP_TEXT = '''**Advanced Watermark Bot**

Commands:
/start - Start bot
/help - Show help
/addtextwm - Create text watermark preset
/addimagewm - Create image watermark preset
/mypresets - Show your presets
/delpreset - Delete preset by id
/cancel - Cancel current preset creation

How to use:
1. Create watermark preset
2. Send a video
3. Choose preset from buttons
4. Bot processes and sends result
'''


@app.on_message(filters.command("start"))
async def start_handler(_, message):
    await message.reply_text(
        "Send /addtextwm or /addimagewm to create presets, then send a video."
    )


@app.on_message(filters.command("help"))
async def help_handler(_, message):
    await message.reply_text(HELP_TEXT)


@app.on_message(filters.command("cancel"))
async def cancel_handler(_, message):
    user_states.pop(message.from_user.id, None)
    await message.reply_text("Cancelled.")


@app.on_message(filters.command("mypresets"))
async def mypresets_handler(_, message):
    presets = await db.get_presets(message.from_user.id)
    if not presets:
        await message.reply_text("No presets found.")
        return

    text = []
    for p in presets:
        text.append(f"`{str(p['_id'])}` - {p.get('name')} ({p.get('type')})")
    await message.reply_text("\n".join(text))


@app.on_message(filters.command("delpreset"))
async def delpreset_handler(_, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Usage: /delpreset <preset_id>")
        return

    ok = await db.delete_preset(message.from_user.id, parts[1].strip())
    await message.reply_text("Deleted." if ok else "Preset not found.")


@app.on_message(filters.command("addtextwm"))
async def add_textwm_handler(_, message):
    user_states[message.from_user.id] = {"mode": "await_text_name"}
    await message.reply_text("Send preset name for text watermark.")


@app.on_message(filters.command("addimagewm"))
async def add_imagewm_handler(_, message):
    user_states[message.from_user.id] = {"mode": "await_image_name"}
    await message.reply_text("Send preset name for image watermark.")


@app.on_message(filters.photo & filters.private)
async def photo_handler(client, message):
    state = user_states.get(message.from_user.id)
    if not state or state.get("mode") != "await_image_file":
        return

    logo_path = make_temp_file_path(message.from_user.id, "logo", "png")
    await message.download(file_name=logo_path)

    preset = {
        "user_id": message.from_user.id,
        "type": "image",
        "name": state["name"],
        "image_path": logo_path,
        "position": state.get("position", "bottom-right"),
        "opacity": state.get("opacity", 0.8),
        "logo_width": state.get("logo_width", 220),
        "created_at": datetime.utcnow(),
    }
    preset_id = await db.add_preset(preset)
    user_states.pop(message.from_user.id, None)
    await message.reply_text(f"Image preset saved. ID: `{preset_id}`")


@app.on_message(filters.text & filters.private)
async def text_handler(_, message):
    if message.text.startswith("/"):
        return

    state = user_states.get(message.from_user.id)
    if not state:
        return

    mode = state.get("mode")

    if mode == "await_text_name":
        state["name"] = message.text.strip()
        state["mode"] = "await_text_value"
        await message.reply_text("Send watermark text.")
        return

    if mode == "await_text_value":
        state["text"] = message.text
        state["mode"] = "await_text_position"
        await message.reply_text("Send position: top-left, top-right, bottom-left, bottom-right, center")
        return

    if mode == "await_text_position":
        state["position"] = message.text.strip().lower()
        preset = {
            "user_id": message.from_user.id,
            "type": "text",
            "name": state["name"],
            "text": state["text"],
            "position": state["position"],
            "font_size": 36,
            "font_color": "white",
            "opacity": 0.8,
            "bold": True,
            "margin_x": 10,
            "margin_y": 10,
            "created_at": datetime.utcnow(),
        }
        preset_id = await db.add_preset(preset)
        user_states.pop(message.from_user.id, None)
        await message.reply_text(f"Text preset saved. ID: `{preset_id}`")
        return

    if mode == "await_image_name":
        state["name"] = message.text.strip()
        state["mode"] = "await_image_position"
        await message.reply_text("Send position: top-left, top-right, bottom-left, bottom-right, center")
        return

    if mode == "await_image_position":
        state["position"] = message.text.strip().lower()
        state["mode"] = "await_image_file"
        await message.reply_text("Now send the watermark image as a photo.")
        return


@app.on_message((filters.video | filters.document) & filters.private)
async def video_handler(_, message):
    media = get_video_media(message)
    if not media:
        return

    presets = await db.get_presets(message.from_user.id)
    if not presets:
        await message.reply_text("No presets found. Create one with /addtextwm or /addimagewm")
        return

    pending_videos[message.from_user.id] = {
        "chat_id": message.chat.id,
        "message_id": message.id,
        "file_name": getattr(media, "file_name", None) or "video.mp4",
    }

    kb = build_presets_keyboard(presets)
    await message.reply_text("Choose a preset:", reply_markup=kb)


@app.on_callback_query(filters.regex(r"^usepreset:"))
async def usepreset_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    pending = pending_videos.get(user_id)
    if not pending:
        await callback_query.answer("No pending video found.", show_alert=True)
        return

    preset_id = callback_query.data.split(":", 1)[1]
    preset = await db.get_preset(user_id, preset_id)
    if not preset:
        await callback_query.answer("Preset not found.", show_alert=True)
        return

    status = await callback_query.message.edit_text("Downloading video...")
    input_path = make_temp_video_path(user_id, "input")
    output_path = make_temp_video_path(user_id, "output")

    try:
        source_message = await client.get_messages(pending["chat_id"], pending["message_id"])
        await source_message.download(file_name=input_path)

        await status.edit_text("Processing...")

        async with semaphore:
            if preset["type"] == "text":
                await apply_text_watermark(input_path, output_path, preset)
            else:
                await apply_image_watermark(input_path, output_path, preset["image_path"], preset)

        await status.edit_text("Uploading...")
        await client.send_video(
            chat_id=pending["chat_id"],
            video=output_path,
            caption=f"Done with preset: {preset.get('name')}",
            reply_to_message_id=pending["message_id"],
        )
        await status.delete()

    except Exception as e:
        err_text = str(e)
        log_path = "/tmp/ffmpeg_error.log"
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.read().splitlines()
                if lines:
                    err_text = "\n".join(lines[-25:])
            except Exception:
                pass

        if len(err_text) > 3500:
            err_text = err_text[-3500:]

        await status.edit_text(f"❌ An error occurred:\n{err_text}\n\nPlease try again.")
    finally:
        pending_videos.pop(user_id, None)
        for path in (input_path, output_path):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass


async def main():
    await db.ensure_indexes()
    print("Bot started...")
    await app.start()
    await idle()

async def idle():
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    app.run()
