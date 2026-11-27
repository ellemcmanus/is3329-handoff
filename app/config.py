"""Settings and wiring: the ONE place that decides which implementations are used.

Switching from the mock AI to the real LLM is a change to EXTRACTOR in .env.
"""
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from app.extractor import RequestExtractor
from app.extractor.llm import LLMExtractor
from app.extractor.mock import MockExtractor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class Settings:
    extractor: str = "mock"                 # "mock" or "llm"
    database: str = str(PROJECT_ROOT / "handoff.db")
    notes_file: Path = DATA_DIR / "synthetic_notes.json"
    bookings_file: Path = DATA_DIR / "synthetic_bookings.csv"
    demo_today: date | None = None          # fixes "today" so demo dates never go stale
    llm_api_key: str | None = None
    llm_model: str = ""


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    today = os.getenv("DEMO_TODAY")
    return Settings(
        extractor=os.getenv("EXTRACTOR", "mock"),
        database=os.getenv("DATABASE", str(PROJECT_ROOT / "handoff.db")),
        demo_today=date.fromisoformat(today) if today else None,
        llm_api_key=os.getenv("LLM_API_KEY") or None,
        llm_model=os.getenv("LLM_MODEL", ""),
    )


def create_extractor(settings: Settings) -> RequestExtractor:
    if settings.extractor == "mock":
        return MockExtractor(settings.notes_file)
    if settings.extractor == "llm":
        return LLMExtractor(settings.llm_api_key, settings.llm_model)
    raise ValueError(f"Unknown EXTRACTOR setting: {settings.extractor!r} (use 'mock' or 'llm')")
