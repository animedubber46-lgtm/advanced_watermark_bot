import asyncio
import os

FFMPEG_ERROR_LOG = "/tmp/ffmpeg_error.log"

async def run_ffmpeg(cmd: list[str]) -> bool:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )

    _, stderr = await proc.communicate()
    stderr_text = stderr.decode("utf-8", errors="ignore")

    try:
        with open(FFMPEG_ERROR_LOG, "w", encoding="utf-8") as f:
            f.write(stderr_text)
    except Exception:
        pass

    if proc.returncode == 0:
        return True

    lines = stderr_text.splitlines()
    short = "\n".join(lines[-80:])
    raise Exception(short if short else "FFmpeg failed")
