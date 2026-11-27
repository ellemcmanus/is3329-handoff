"""Booking provider: where restaurant bookings come from.

Target: an adapter to the hotel's restaurant reservation system.
Prototype (Mocked): CsvBookingProvider reads synthetic bookings from a file
through the same interface, so the real adapter can replace it later.
"""
import csv
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path

from app.models import Booking, Guest


class BookingProvider(ABC):
    @abstractmethod
    def get_bookings(self, guest: Guest, day: date) -> list[Booking]:
        """All of this guest's restaurant bookings on one day."""

    @abstractmethod
    def get_service(self, day: date, service: str) -> list[Booking]:
        """All bookings for one service (e.g. Friday dinner), ordered by seating time."""


class CsvBookingProvider(BookingProvider):
    def __init__(self, csv_file: Path):
        self._bookings: list[Booking] = []
        with open(csv_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self._bookings.append(Booking(
                    guest_name=row["guest_name"], room=row["room"],
                    day=date.fromisoformat(row["date"]), service=row["service"],
                    time=row["time"], table=row["table"], party_size=int(row["party_size"])))

    def get_bookings(self, guest: Guest, day: date) -> list[Booking]:
        # Match on surname AND room, so two guests called Walsh are not mixed up.
        matches = [b for b in self._bookings
                   if b.day == day
                   and b.guest_name.lower() == guest.name.lower()
                   and b.room == str(guest.room)]
        return sorted(matches, key=lambda b: b.time)

    def get_service(self, day: date, service: str) -> list[Booking]:
        matches = [b for b in self._bookings if b.day == day and b.service == service]
        return sorted(matches, key=lambda b: b.time)