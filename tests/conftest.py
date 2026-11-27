"""Shared test set-up: a fresh in-memory database and the mock AI for every test."""
from datetime import date

import pytest

from app import db
from app.bookings import CsvBookingProvider
from app.briefing import BriefingService
from app.config import DATA_DIR
from app.extractor.mock import MockExtractor
from app.guests import GuestRepository
from app.handlers import create_handlers
from app.intake import GuestNote, IntakeService
from app.models import Guest
from app.review import ReviewService
from app.safety import SafetyChecker

TODAY = date(2026, 12, 2)  # fixed "today" so tests never go stale
STAY_START, STAY_END = date(2026, 12, 2), date(2026, 12, 5)


@pytest.fixture
def guest():
    return Guest("Murphy", "3", STAY_START, STAY_END, guest_id=1)


@pytest.fixture
def system():
    """All components wired together exactly as the app does it."""
    conn = db.connect(":memory:")
    guests = GuestRepository(conn)
    bookings = CsvBookingProvider(DATA_DIR / "synthetic_bookings.csv")
    review = ReviewService(conn, guests)
    intake = IntakeService(conn, MockExtractor(DATA_DIR / "synthetic_notes.json"),
                           create_handlers(TODAY), SafetyChecker(), guests, bookings, review)
    briefing = BriefingService(bookings, guests, review)

    class System:
        pass

    s = System()
    s.guests, s.bookings, s.review, s.intake, s.briefing = guests, bookings, review, intake, briefing
    return s


def make_note(name, room, text, start=STAY_START, end=STAY_END):
    return GuestNote(name, room, start, end, text)