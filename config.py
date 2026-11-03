"""Central configuration: environment variables and shared constants."""
import os
import re
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # must run before the os.getenv calls below

DB_PATH = BASE_DIR / "database.db"
STATIC_DIR = BASE_DIR / "static"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EDITABLE_FIELDS = {"name", "email", "phone", "city"}
MAX_TOOL_ROUNDS = 5
MAX_HISTORY_MESSAGES = 12


def is_admin(email: str) -> bool:
    return email.strip().lower() == ADMIN_EMAIL