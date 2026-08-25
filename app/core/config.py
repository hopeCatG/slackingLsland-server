import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings:
    app_name = os.getenv("APP_NAME", "Slack-off API")
    app_host = os.getenv("APP_HOST", "127.0.0.1")
    app_port = int(os.getenv("APP_PORT", "8000"))
    cors_allow_origins = tuple(item.strip() for item in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if item.strip())
    mysql_host = os.getenv("MYSQL_HOST", "").strip()
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user = os.getenv("MYSQL_USER", "").strip()
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_database = os.getenv("MYSQL_DATABASE", "").strip()
    token_secret = os.getenv("TOKEN_SECRET", "local-development-token-secret")


@lru_cache
def get_settings() -> Settings:
    return Settings()
