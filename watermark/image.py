import os
from config import DEFAULT_LOGO_WIDTH
from watermark.ffmpeg_runner import run_ffmpeg

def build_filter(settings: dict) -> str:
    position = settings.get("position", "bottom-right")
    opacity = max(0.0, min(1.0, float(settings.get("opacity", 0.8))))
    logo_width = int(settings.get("logo_width", DEFAULT_LOGO_WIDTH))

    pos_map = {
        "top-left": "10:10",
        "top-right": "W-w-10:10",
        "bottom-left": "10:H-h-10",
        "bottom-right": "W-w-10:H-h-10",
        "center": "(W-w)/2:(H-h)/2",
    }
    xy = pos_map.get(position, "10:10")

    return (
        f"[1:v]scale={logo_width}:-1,"
        f"format=rgba,"
        f"colorchannelmixer=aa={opacity}[logo];"
        f"[0:v][logo]overlay={xy}:shortest=1[vout]"
    )

async def apply_image_watermark(input_path: str, output_path: str, logo_path: str, settings: dict) -> bool:
    fc = build_filter(settings)
    cmd = [
        "ffmpeg",
        "-y",
        "-nostdin",
        "-hide_banner",
        "-fflags", "+genpts+igndts",
        "-err_detect", "ignore_err",
        "-ignore_unknown",
        "-i", input_path,
        "-loop", "1",
        "-i", logo_path,
        "-filter_complex", fc,
        "-map", "[vout]",
        "-map", "0:a:0?",
        "-map_metadata", "-1",
        "-map_chapters", "-1",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "44100",
        "-b:a", "192k",
        "-fps_mode", "vfr",
        "-avoid_negative_ts", "make_zero",
        "-max_muxing_queue_size", "9999",
        "-movflags", "+faststart",
        output_path,
    ]
    ok = await run_ffmpeg(cmd)
    if not os.path.exists(output_path):
        raise Exception("Output file not created")
    return ok
