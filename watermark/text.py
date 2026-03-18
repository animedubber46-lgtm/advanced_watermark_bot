import os
from config import DEFAULT_FONT_REGULAR, DEFAULT_FONT_BOLD, FALLBACK_FONT
from watermark.ffmpeg_runner import run_ffmpeg

def _escape_text(text: str) -> str:
    text = str(text)
    return (
        text.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace(":", "\\:")
        .replace("%", "\\%")
        .replace(",", "\\,")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )

def _get_font(bold: bool = False) -> str:
    if bold and os.path.exists(DEFAULT_FONT_BOLD):
        return DEFAULT_FONT_BOLD
    if os.path.exists(DEFAULT_FONT_REGULAR):
        return DEFAULT_FONT_REGULAR
    return FALLBACK_FONT

def _position_to_expr(position: str, mx: int, my: int):
    pos = {
        "top-left": ("10", "10"),
        "top-right": ("w-text_w-10", "10"),
        "bottom-left": ("10", "h-text_h-10"),
        "bottom-right": ("w-text_w-10", "h-text_h-10"),
        "center": ("(w-text_w)/2", "(h-text_h)/2"),
    }
    x, y = pos.get(position, ("10", "10"))
    x = x.replace("10", str(mx), 1) if x == "10" else x.replace("w-text_w-10", f"w-text_w-{mx}")
    y = y.replace("10", str(my), 1) if y == "10" else y.replace("h-text_h-10", f"h-text_h-{my}")
    return x, y

def build_text_filter(settings: dict) -> str:
    text = _escape_text(settings.get("text", "Watermark"))
    font = _get_font(settings.get("bold", True))
    size = int(settings.get("font_size", 36))
    color = settings.get("font_color", "white")
    opacity = max(0.0, min(1.0, float(settings.get("opacity", 0.8))))
    x, y = _position_to_expr(
        settings.get("position", "bottom-right"),
        int(settings.get("margin_x", 10)),
        int(settings.get("margin_y", 10)),
    )
    return (
        f"drawtext=fontfile={font}:text='{text}':"
        f"fontsize={size}:fontcolor={color}@{opacity}:x={x}:y={y}"
    )

async def apply_text_watermark(input_path: str, output_path: str, settings: dict) -> bool:
    vf = build_text_filter(settings)
    cmd = [
        "ffmpeg",
        "-y",
        "-nostdin",
        "-hide_banner",
        "-fflags", "+genpts+igndts",
        "-err_detect", "ignore_err",
        "-ignore_unknown",
        "-i", input_path,
        "-vf", vf,
        "-map", "0:v:0",
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
