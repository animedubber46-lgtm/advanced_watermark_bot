import asyncio
import os

LOG_FILE = "/tmp/ffmpeg_error.log"


async def run_ffmpeg(cmd, timeout_seconds=21600):
    """
    Run FFmpeg safely for large videos.
    Only fail if FFmpeg exits with non-zero return code
    or exceeds the timeout.
    """
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        raise Exception("FFmpeg timed out while processing the video.")

    stderr_text = stderr.decode("utf-8", errors="ignore")

    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(stderr_text)
    except Exception:
        pass

    if proc.returncode != 0:
        lines = stderr_text.splitlines()
        short = "\n".join(lines[-80:])
        raise Exception(short if short else "FFmpeg failed")

    return True
