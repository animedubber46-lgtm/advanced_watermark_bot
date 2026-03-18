import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "watermark_bot")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
TEMP_DIR = os.getenv("TEMP_DIR", "temp")
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
DEFAULT_LOGO_WIDTH = int(os.getenv("DEFAULT_LOGO_WIDTH", "220"))
DEFAULT_FONT_REGULAR = os.getenv("DEFAULT_FONT_REGULAR", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
DEFAULT_FONT_BOLD = os.getenv("DEFAULT_FONT_BOLD", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
FALLBACK_FONT = os.getenv("FALLBACK_FONT", "/usr/share/fonts/truetype/freefont/FreeSans.ttf")

os.makedirs(TEMP_DIR, exist_ok=True)
