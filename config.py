import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "aureum-dev-secret-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("RENDER", "").lower() == "true"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads" / "receipts"

    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        SQLALCHEMY_DATABASE_URI = normalize_database_url(database_url)
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'instance' / 'expense.db'}"
