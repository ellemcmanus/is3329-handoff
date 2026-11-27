"""Request handler interface: one implementation per request type.

Adding a new request type (for example "room service") means adding one
new module with a RequestHandler subclass and registering it in
app/handlers/__init__.py. Nothing else changes.
"""
from abc import ABC, abstractmethod
from datetime import date

from app.models import WARNING, ExtractedRequest, Flag, Guest, HandoffItem


class RequestHandler(ABC):
    def __init__(self, today: date | None = None):
        # "today" can be fixed for demos and tests, so dates don't go stale.
        self.today = today or date.today()

    @abstractmethod
    def validate(self, request: ExtractedRequest, guest: Guest) -> HandoffItem:
        """Check one extracted request and return it with any flags attached."""

    # Helpers shared by the handlers -------------------------------------

    @staticmethod
    def parse_date(value) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None

    def check_date(self, value, guest: Guest, what: str) -> list[Flag]:
        """Flag a date that is missing, unreadable, in the past, or outside the stay."""
        day = self.parse_date(value)
        if value and day is None:
            return [Flag(WARNING, f"{what}: date '{value}' could not be read. Check with the guest.")]
        if day is None:
            return [Flag(WARNING, f"{what}: no date given. Ask the guest which day.")]
        flags = []
        if day < self.today:
            flags.append(Flag(WARNING, f"{what}: {day:%a %d %b} is in the past."))
        if not guest.is_staying_on(day):
            flags.append(Flag(WARNING, f"{what}: {day:%a %d %b} is outside the guest's stay "
                                       f"({guest.stay_start:%d %b} to {guest.stay_end:%d %b})."))
        return flags