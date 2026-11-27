from datetime import date

from conftest import STAY_END, STAY_START

from app.bookings import CsvBookingProvider
from app.config import DATA_DIR
from app.models import Guest

provider = CsvBookingProvider(DATA_DIR / "synthetic_bookings.csv")
FRIDAY = date(2026, 12, 4)


def test_finds_the_right_booking():
    murphy = Guest("Murphy", "3", STAY_START, STAY_END)
    bookings = provider.get_bookings(murphy, FRIDAY)
    assert len(bookings) == 1 and bookings[0].time == "19:00" and bookings[0].table == "6"


def test_two_guests_with_same_surname_are_kept_apart():
    walsh_11 = Guest("Walsh", "11", STAY_START, STAY_END)
    assert [b.table for b in provider.get_bookings(walsh_11, FRIDAY)] == ["10"]


def test_service_is_ordered_by_seating_time():
    times = [b.time for b in provider.get_service(FRIDAY, "dinner")]
    assert times == sorted(times) and len(times) > 5