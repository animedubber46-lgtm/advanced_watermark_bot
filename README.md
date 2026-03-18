# Advanced Telegram Watermark Bot

Stable Telegram watermark bot for VPS deployment.

## Features
- Text watermark and image watermark
- Save multiple presets per user
- Inline buttons to select watermark presets
- Queue / concurrency limit
- MongoDB storage
- FFmpeg logging to `/tmp/ffmpeg_error.log`
- Safer FFmpeg mapping for weird Telegram/anime encodes
- Works well on strong VPS setups

## Commands
- `/start`
- `/help`
- `/addtextwm` — create a text watermark preset
- `/addimagewm` — upload an image preset
- `/mypresets` — list saved presets
- `/delpreset` — delete a preset by id
- `/cancel`

## VPS setup
```bash
apt update
apt install -y ffmpeg fonts-dejavu-core
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python3 main.py
```

## Bot flow
1. Create watermark presets with `/addtextwm` or `/addimagewm`
2. Send a video or document containing video
3. Bot shows your saved presets
4. Choose one preset
5. Bot processes and sends watermarked output

## Notes
- Keep enough free disk space for input + output + temp files
- FFmpeg errors are saved to `/tmp/ffmpeg_error.log`
- This project is intentionally simple and stable rather than overloaded with risky FFmpeg tricks
