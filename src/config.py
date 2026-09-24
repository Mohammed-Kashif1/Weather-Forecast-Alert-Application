"""Application configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "outputs"
IMAGE_DIR = OUTPUT_DIR / "images"
for directory in (DATA_DIR, OUTPUT_DIR, IMAGE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(OUTPUT_DIR / "weather.db")))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = ROOT_DIR / DATABASE_PATH

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
API_BASE_URL = "https://api.openweathermap.org/data/2.5"
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))

DEFAULT_TEMP_THRESHOLD = float(os.getenv("DEFAULT_TEMP_THRESHOLD", "35"))
DEFAULT_HUMIDITY_THRESHOLD = float(os.getenv("DEFAULT_HUMIDITY_THRESHOLD", "85"))
DEFAULT_RAIN_THRESHOLD = float(os.getenv("DEFAULT_RAIN_THRESHOLD", "70"))

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
EMAIL_FROM = os.getenv("EMAIL_FROM", "").strip()
EMAIL_TO = os.getenv("EMAIL_TO", "").strip()
