import os
import time

from uuid import uuid4
from datetime import datetime, timezone
import logging
from logging.handlers import TimedRotatingFileHandler

def new_uuid() -> str:
    return uuid4().hex

def utcnow_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)

def truncate(text: str, limit: int) -> str:
    """Trim text to fit embed limits without raising."""
    return text if len(text) <= limit else text[: limit - 3] + "..."

def load_env(filename=".env"):
    values = {}

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Ignore blank lines and comments
            if not line or line.startswith("#"):
                continue

            # Key/value parsing
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                values[key] = value

    return values

def require_env(env: dict, key: str, filename: str = ".env") -> str:
    """Get a required key from env dict or raise a clear error."""
    try:
        return env[key]
    except KeyError:
        raise RuntimeError(f"{key} not found in {filename}")


class DailyRolloverHandler(TimedRotatingFileHandler):
    def __init__(self, filename, **kwargs):
        super().__init__(
            filename,
            when="midnight",
            interval=1,
            backupCount=5,
            encoding="utf-8",
            **kwargs,
        )
        self._force_rollover_on_start()

    def _force_rollover_on_start(self):
        # Only rotate at startup if the existing file is from a previous day
        if not os.path.exists(self.baseFilename):
            return

        # File modification time
        mtime = os.path.getmtime(self.baseFilename)
        file_date = time.localtime(mtime)[:3]  # (year, month, day)
        today = time.localtime()[:3]

        if file_date != today:
            self.doRollover()
