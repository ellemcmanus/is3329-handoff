from datetime import date

from conftest import STAY_END, STAY_START, make_note

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




def test_guest_with_two_bookings_that_day_is_flagged(system):
    note_id = system.intake.submit_note(make_note(
        "Walsh", "2", "Our anniversary is on Friday, could we have a candle on the dessert?"))
    item = system.review.items_for_note(note_id)[0]
    assert any("2 bookings that day" in f.message for f in item.flags)


def test_no_booking_found_is_flagged(system):
    note_id = system.intake.submit_note(make_note(
        "Gallagher", "16", "alergic to prawns and mussles, bday dinner on fri can u do a cake"))
    celebration = [i for i in system.review.items_for_note(note_id) if i.request_type == "celebration"][0]
    assert any("No restaurant booking found" in f.message for f in celebration.flags)


def test_matched_booking_is_attached_to_celebration(system):
    note_id = system.intake.submit_note(make_note(
        "Walsh", "11", "Mr Walsh asked for a glass of champagne at dinner on Friday for his wife's birthday."))
    item = system.review.items_for_note(note_id)[0]
    assert item.details["booking"] == "Fri 04 Dec, dinner 19:45, table 10"