"""Application configuration."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import os

APP_NAME = "RussianFlashcards"
APP_VERSION = "0.1.0"

# Database
DB_PATH = Path(__file__).parent.parent / "data" / "russian_flashcards.db"

# CEFR Levels
CEFR_LEVELS = ["A1", "A2", "B1", "B2"]

# Daily defaults
DEFAULT_DAILY_GOAL = 20
DEFAULT_NOTIFICATION_HOUR = 9
DEFAULT_NOTIFICATION_MINUTE = 0

# SM-2 defaults
INITIAL_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
EASY_BONUS = 1.3

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR = DATA_DIR / "cache"
AUDIO_CACHE_DIR = CACHE_DIR / "audio"
TTS_MODEL_DIR = CACHE_DIR / "tts_models"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
TTS_MODEL_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    daily_goal: int = DEFAULT_DAILY_GOAL
    notification_enabled: bool = True
    notification_hour: int = DEFAULT_NOTIFICATION_HOUR
    notification_minute: int = DEFAULT_NOTIFICATION_MINUTE
    theme: str = "light"  # "light" or "dark"
    active_plan: Optional[str] = None  # CEFR level

    def save(self, path: Path = None) -> None:
        if path is None:
            path = DATA_DIR / "config.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "daily_goal": self.daily_goal,
                    "notification_enabled": self.notification_enabled,
                    "notification_hour": self.notification_hour,
                    "notification_minute": self.notification_minute,
                    "theme": self.theme,
                    "active_plan": self.active_plan,
                },
                f,
                indent=2,
            )

    @classmethod
    def load(cls, path: Path = None) -> "AppConfig":
        if path is None:
            path = DATA_DIR / "config.json"
        if not path.exists():
            return cls()
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return cls(
                daily_goal=data.get("daily_goal", DEFAULT_DAILY_GOAL),
                notification_enabled=data.get("notification_enabled", True),
                notification_hour=data.get("notification_hour", DEFAULT_NOTIFICATION_HOUR),
                notification_minute=data.get("notification_minute", DEFAULT_NOTIFICATION_MINUTE),
                theme=data.get("theme", "light"),
                active_plan=data.get("active_plan"),
            )
        except (json.JSONDecodeError, KeyError):
            return cls()


# Global config instance
config = AppConfig.load()
